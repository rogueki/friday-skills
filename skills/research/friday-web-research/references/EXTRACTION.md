# Single-page extraction

The executable path in this repository is `adapters.web_extraction.extract_one`. It consumes one HTML response from an injected host transport. Optional `scrapling_static_transport` performs one static Scrapling `Fetcher.get` request. Optional `scrapling_stealth_transport` invokes `StealthyFetcher.fetch` for one authorized public page that needs browser rendering. Both require a trusted host capability to approve the exact URL, time, and byte budget before fetching. The host must enforce DNS/public-IP pinning, exact host policy on initial requests and redirects, every browser subrequest, and an aggregate byte cap during download. The adapter independently checks the requested HTTPS host against an exact allowlist, the final URL, status, content type, returned body size, challenge/login patterns, and a small selector grammar. These checks cannot serve as a complete SSRF boundary for an arbitrary transport.

`css` accepts a tag, `.class`, `#id`, `tag.class`, `tag#id`, or up to four descendant tokens, optionally suffixed with `::text`. `table` requires a selector identifying exactly one table. `markdown` extracts headings, paragraphs, and list items. The HTML parser caps node count and depth. There is no pagination, login, CSS combinators, PDF, OCR, or recursive crawl. The browser transport may render JavaScript, but the extractor reads only the resulting HTML. The result records source URL, final URL, UTC retrieval, mode, selector, and method provenance (`injected-transport`, `scrapling-static`, or `scrapling-stealth`); page text remains `untrusted-page-data`. Check extracted fields against the visible source before citing them.

```python
from adapters.web_extraction import PageResponse, extract_one

def host_transport(url: str, timeout_s: float, max_bytes: int) -> PageResponse:
    # Host implementation must enforce DNS/public-IP pinning and egress policy.
    raise NotImplementedError

result = extract_one(
    "https://docs.example.org/report", mode="table", selector="table#data",
    allowed_hosts={"docs.example.org"}, transport=host_transport,
)
```

For an authorized static Scrapling request, construct `scrapling_static_transport(allowed_hosts={"docs.example.org"}, authorize_egress=trusted_host_capability)` and pass it to `extract_one`. The capability receives `(url, timeout_s, max_bytes)` and must return `True` only when the host enforces its DNS/IP and ingress rules. The transport calls `Fetcher.get(url, timeout=..., retries=0, follow_redirects=False, max_redirects=0)` once. It checks returned bytes after receipt; Scrapling's `Fetcher.get` does **not** give this adapter a streaming download cap. Thus a host network layer is mandatory for the pre-receipt cap. Do not expose this constructor as an agent tool without that host boundary.

For a separately selected browser request, construct `scrapling_stealth_transport(allowed_hosts={"docs.example.org"}, authorize_browser_egress=trusted_browser_capability)` and pass it to `extract_one`. The browser capability has the same `(url, timeout_s, max_bytes)` signature but must be specifically authorized for browser egress. Scrapling 0.4.15 calls `page_setup` before navigation; the adapter installs an exact-host Playwright route there and permits only GET/HEAD requests. It sets `service_workers="block"`, rejects invalid TLS certificates, disables geolocation/notification permissions, Google referrer, Cloudflare solving, and browser retries beyond one attempt. Scrapling can swallow errors raised by `page_setup`; the adapter checks that route installation was observed. A Playwright route does **not** re-intercept every redirect or constrain DNS, WebSockets, all browser processes, or bytes while downloading. The trusted host's network controls are mandatory, even if the route is installed. No such host boundary or live target test is supplied by this repository.

## Optional packages and next integration boundary

Locally inspected on 2026-10-15: Scrapling 0.4.15, Crawl4AI 0.9.3, Playwright 1.62.0. These are **not mandatory runtime dependencies of this package**. Current Scrapling uses `Fetcher.get(url)` for static pages, `page.status`, `page.body` (bytes), and `StealthyFetcher.fetch(url)` for browser rendering. The older `StealthyFetcher.get` example in the operator's local skill is stale. Crawl4AI uses `AsyncWebCrawler(config=BrowserConfig(...))` and `await crawler.arun(url=..., config=CrawlerRunConfig(...))`; results expose `success` and markdown. Crawl4AI remains unwired because its browser requires the same full egress boundary. Do not pass credentials or private page content to an optional cloud provider.

Sources: [Scrapling fetcher API](https://scrapling.readthedocs.io/en/latest/api-reference/fetchers.html), [Scrapling fetcher basics](https://scrapling.readthedocs.io/en/latest/fetching/choosing.html), [Playwright routes](https://playwright.dev/python/docs/api/class-route), [Playwright network redirects and service workers](https://playwright.dev/python/docs/network), [Crawl4AI v0.9.x quick start](https://docs.crawl4ai.com/core/quickstart/), [Crawl4AI result reference](https://docs.crawl4ai.com/core/crawler-result/). The upstream [Scrapling agent skill](https://github.com/D4Vinci/Scrapling/blob/main/agent-skill/Scrapling-Skill/SKILL.md) and the operator's local `playwright-and-crawl4ai-scraper` informed the tool selection; this text and implementation are original.

## Access decisions

An HTTP 401/403/429, CAPTCHA, login redirect, challenge page, or empty response is a stop condition. No automatic StealthyFetcher or Firecrawl fallback is installed. The browser transport is available only by explicit construction with a trusted browser egress capability; it does not solve Cloudflare challenges or guarantee anti-bot access. Firecrawl requires separate explicit cost and data-sharing authorization; no `.env` lookup, key handling, paid call, or auto-escalation is present.
