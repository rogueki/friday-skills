"""Bounded, single-page extraction from a caller supplied response transport.

The transport is deliberately injected: this module does not grant network access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
import ipaddress
import re
import time
from typing import Callable, Mapping
from urllib.parse import urlsplit


MAX_BYTES = 1_000_000
MAX_CHARS = 50_000
MAX_SECONDS = 15.0
MAX_NODES = 2_000
MAX_DEPTH = 64
_CHALLENGE = re.compile(r"just a moment|verify you are human|captcha|cloudflare challenge", re.I)
_LOGIN = re.compile(r"(?:^|/)(?:login|signin|auth|checkpoint)(?:/|$)", re.I)
_SIMPLE_SELECTOR = re.compile(r"^(?P<tag>[a-z][a-z0-9-]*)?(?:(?P<kind>[.#])(?P<name>[a-zA-Z_][\w-]*))?$", re.I)


class ExtractionError(ValueError):
    """The requested page cannot be used as evidence."""


@dataclass(frozen=True)
class PageResponse:
    status: int
    final_url: str
    body: bytes
    headers: Mapping[str, str] = field(default_factory=dict)
    method: str = "injected-transport"


@dataclass(frozen=True)
class ExtractionResult:
    source_url: str
    final_url: str
    retrieved_at_utc: str
    mode: str
    selector: str | None
    values: tuple[str, ...]
    table: tuple[tuple[str, ...], ...]
    markdown: str | None
    provenance: str = "injected-transport"
    trust: str = "untrusted-page-data"


@dataclass
class _Node:
    tag: str
    attrs: dict[str, str]
    parent: _Node | None = None
    children: list[_Node | str] = field(default_factory=list)


class _Tree(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("root", {})
        self.stack = [self.root]
        self.node_count = 0

    def _new_node(self, tag: str, attrs: list[tuple[str, str | None]]) -> _Node:
        self.node_count += 1
        if self.node_count > MAX_NODES or len(self.stack) >= MAX_DEPTH:
            raise ExtractionError("HTML node or depth limit exceeded")
        return _Node(tag, {key: value or "" for key, value in attrs}, self.stack[-1])

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = self._new_node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in {"br", "hr", "img", "input", "meta", "link", "source", "wbr"}:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.stack[-1].children.append(self._new_node(tag, attrs))

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        self.stack[-1].children.append(data)


def _text(node: _Node) -> str:
    if node.tag in {"script", "style", "noscript", "template", "svg"}:
        return ""
    return " ".join(part for child in node.children if (part := child if isinstance(child, str) else _text(child)).strip())


def _all_nodes(node: _Node):
    for child in node.children:
        if isinstance(child, _Node):
            yield child
            yield from _all_nodes(child)


def _matches(node: _Node, token: str) -> bool:
    match = _SIMPLE_SELECTOR.fullmatch(token)
    if not match or not (match["tag"] or match["kind"]):
        raise ExtractionError("unsupported selector; use tag, .class, #id, or descendants")
    if match["tag"] and node.tag != match["tag"].lower():
        return False
    if match["kind"] == ".":
        return match["name"] in node.attrs.get("class", "").split()
    if match["kind"] == "#":
        return match["name"] == node.attrs.get("id")
    return True


def _select(root: _Node, selector: str) -> list[_Node]:
    tokens = selector.strip().removesuffix("::text").split()
    if not tokens or len(tokens) > 4 or len(selector) > 120:
        raise ExtractionError("selector length or depth exceeded")
    selected = [root]
    for token in tokens:
        selected = [candidate for node in selected for candidate in _all_nodes(node) if _matches(candidate, token)]
        if len(selected) > 500:
            raise ExtractionError("too many selector matches")
    return selected


def _normal(value: str) -> str:
    return " ".join(value.split())


def _url(url: str, allowed_hosts: set[str]) -> str:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower().rstrip(".")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        is_ip = False
    else:
        is_ip = True
    try:
        port = parts.port
    except ValueError as exc:
        raise ExtractionError("invalid URL port") from exc
    if (
        parts.scheme != "https"
        or not host
        or is_ip
        or host == "localhost"
        or host.endswith(".localhost")
        or host.endswith(".local")
        or host not in allowed_hosts
        or parts.username is not None
        or parts.password is not None
        or port not in (None, 443)
        or "\\" in url
        or any(ord(char) < 32 for char in url)
    ):
        raise ExtractionError("URL is not an allowed HTTPS host")
    return host


def scrapling_static_transport(
    *,
    allowed_hosts: set[str],
    authorize_egress: Callable[[str, float, int], bool],
    fetcher: object | None = None,
) -> Callable[[str, float, int], PageResponse]:
    """Opt-in static Fetcher transport; host must pin public DNS/IP and cap ingress.

    The authorizer must approve the exact URL and limits before the sole request.
    Scrapling's in-memory response limit is checked after receipt, so a trusted
    host egress layer is required to cap downloaded bytes during transfer.
    """
    allowed = {host.lower().rstrip(".") for host in allowed_hosts}

    def fetch(url: str, timeout_s: float, max_bytes: int) -> PageResponse:
        _url(url, allowed)
        if not (0 < timeout_s <= MAX_SECONDS and 1 <= max_bytes <= MAX_BYTES):
            raise ExtractionError("transport limit exceeded")
        if authorize_egress(url, timeout_s, max_bytes) is not True:
            raise ExtractionError("host egress authorization denied")
        selected_fetcher = fetcher
        if selected_fetcher is None:
            try:
                from scrapling.fetchers import Fetcher
            except ImportError as exc:
                raise ExtractionError("optional Scrapling package unavailable") from exc
            selected_fetcher = Fetcher
        page = selected_fetcher.get(
            url, timeout=timeout_s, retries=0, follow_redirects=False, max_redirects=0,
        )
        body = page.body
        if not isinstance(body, bytes) or len(body) > max_bytes:
            raise ExtractionError("Scrapling response byte limit exceeded")
        return PageResponse(status=page.status, final_url=page.url, body=body, headers=page.headers,
                            method="scrapling-static")

    return fetch


def scrapling_stealth_transport(
    *,
    allowed_hosts: set[str],
    authorize_browser_egress: Callable[[str, float, int], bool],
    fetcher: object | None = None,
) -> Callable[[str, float, int], PageResponse]:
    """Opt-in browser fetch behind a trusted host's enforced network boundary.

    The authorizer approves the exact URL, time and ingress-byte budget and must
    enforce public DNS/IP pinning, redirects, every subrequest, and byte limits.
    Playwright routing is defense in depth; it cannot enforce those properties.
    """
    allowed = {host.lower().rstrip(".") for host in allowed_hosts}

    def fetch(url: str, timeout_s: float, max_bytes: int) -> PageResponse:
        source_host = _url(url, allowed)
        if not (0 < timeout_s <= MAX_SECONDS and 1 <= max_bytes <= MAX_BYTES):
            raise ExtractionError("transport limit exceeded")
        if authorize_browser_egress(url, timeout_s, max_bytes) is not True:
            raise ExtractionError("host browser egress authorization denied")
        selected_fetcher = fetcher
        if selected_fetcher is None:
            try:
                from scrapling.fetchers import StealthyFetcher
            except ImportError as exc:
                raise ExtractionError("optional Scrapling package unavailable") from exc
            selected_fetcher = StealthyFetcher

        route_installed = False

        def route_request(route: object) -> None:
            try:
                if route.request.method in {"GET", "HEAD"} and _url(route.request.url, {source_host}) == source_host:
                    route.fallback()
                else:
                    route.abort()
            except (ExtractionError, AttributeError, ValueError):
                route.abort()

        def page_setup(page: object) -> None:
            nonlocal route_installed
            page.route("**/*", route_request)
            route_installed = True

        page = selected_fetcher.fetch(
            url,
            timeout=int(timeout_s * 1000),
            retries=1,
            retry_delay=0,
            wait=0,
            network_idle=False,
            google_search=False,
            disable_resources=True,
            solve_cloudflare=False,
            block_webrtc=True,
            page_setup=page_setup,
            additional_args={
                "service_workers": "block",
                "ignore_https_errors": False,
                "permissions": [],
            },
        )
        if not route_installed:
            raise ExtractionError("browser request route was not installed")
        body = page.body
        if not isinstance(body, bytes) or len(body) > max_bytes:
            raise ExtractionError("Scrapling response byte limit exceeded")
        return PageResponse(
            status=page.status,
            final_url=page.url,
            body=body,
            headers=page.headers,
            method="scrapling-stealth",
        )

    return fetch


def extract_one(
    source_url: str,
    *,
    mode: str,
    transport: Callable[[str, float, int], PageResponse],
    allowed_hosts: set[str],
    selector: str | None = None,
    max_bytes: int = MAX_BYTES,
    max_chars: int = MAX_CHARS,
    timeout_s: float = MAX_SECONDS,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> ExtractionResult:
    """Extract one response; caller's transport must enforce DNS and egress policy."""
    if mode not in {"css", "table", "markdown"}:
        raise ExtractionError("explicit css, table, or markdown mode required")
    if (mode in {"css", "table"}) != bool(selector):
        raise ExtractionError("selector required only for css/table mode")
    if not (1 <= max_bytes <= MAX_BYTES and 1 <= max_chars <= MAX_CHARS and 0 < timeout_s <= MAX_SECONDS):
        raise ExtractionError("extraction limit exceeded")
    allowed = {host.lower().rstrip(".") for host in allowed_hosts}
    source_host = _url(source_url, allowed)
    started = time.monotonic()
    response = transport(source_url, timeout_s, max_bytes)
    if time.monotonic() - started > timeout_s:
        raise ExtractionError("transport timeout exceeded")
    final_host = _url(response.final_url, allowed)
    if final_host != source_host:
        raise ExtractionError("cross-host redirect denied")
    if _LOGIN.search(urlsplit(response.final_url).path):
        raise ExtractionError("login redirect denied")
    if response.status in {401, 403, 429}:
        raise ExtractionError(f"access denied or rate limited: HTTP {response.status}")
    if response.status != 200:
        raise ExtractionError(f"unexpected HTTP {response.status}")
    content_type = next((value for key, value in response.headers.items() if key.lower() == "content-type"), "text/html")
    if "text/html" not in content_type.lower():
        raise ExtractionError("HTML content type required")
    if not isinstance(response.body, bytes) or len(response.body) > max_bytes:
        raise ExtractionError("response byte limit exceeded")
    if response.method not in {"injected-transport", "scrapling-static", "scrapling-stealth"}:
        raise ExtractionError("unknown extraction method")
    try:
        html = response.body.decode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise ExtractionError("UTF-8 HTML required") from exc
    if len(html) > max_chars:
        raise ExtractionError("response character limit exceeded")
    tree = _Tree()
    tree.feed(html)
    visible = _normal(_text(tree.root))
    if not visible or _CHALLENGE.search(visible[:2000]):
        raise ExtractionError("empty or challenge page")
    values: tuple[str, ...] = ()
    table: tuple[tuple[str, ...], ...] = ()
    markdown: str | None = None
    if mode == "css":
        values = tuple(value for node in _select(tree.root, selector or "") if (value := _normal(_text(node))))
        if not values:
            raise ExtractionError("selector has no visible match")
    elif mode == "table":
        tables = _select(tree.root, selector or "")
        if len(tables) != 1 or tables[0].tag != "table":
            raise ExtractionError("selector must identify exactly one table")
        table = tuple(
            tuple(_normal(_text(cell)) for cell in _all_nodes(row) if cell.tag in {"th", "td"})
            for row in _all_nodes(tables[0]) if row.tag == "tr"
        )
        table = tuple(row for row in table if row)
        if not table:
            raise ExtractionError("table contains no cells")
    else:
        blocks = []
        for node in _all_nodes(tree.root):
            if node.tag in {"h1", "h2", "h3", "p", "li"}:
                content = _normal(_text(node))
                if content:
                    prefix = {"h1": "# ", "h2": "## ", "h3": "### ", "li": "- "}.get(node.tag, "")
                    blocks.append(prefix + content)
        markdown = "\n\n".join(blocks)
        if not markdown:
            raise ExtractionError("no article blocks found")
    timestamp = now()
    if timestamp.tzinfo is None:
        raise ExtractionError("retrieval time must be timezone aware")
    return ExtractionResult(
        source_url, response.final_url, timestamp.astimezone(timezone.utc).isoformat(), mode,
        selector, values, table, markdown, response.method,
    )
