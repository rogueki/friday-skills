# Single-page extraction

The executable path in this repository is `adapters.web_extraction.extract_one`. It consumes one HTML response from an injected host transport. The optional `scrapling_static_transport` performs one static Scrapling `Fetcher.get` request only after a trusted host capability authorizes the exact URL and limits. The host must enforce DNS resolution/public-IP pinning, egress restrictions and a byte cap during download. The adapter independently checks the requested HTTPS host against an exact allowlist, the final URL, status, content type, body size, challenge/login patterns, and a small supported selector grammar. A caller cannot treat these checks as a complete SSRF boundary for an arbitrary transport.

`css` accepts a tag, `.class`, `#id`, `tag.class`, `tag#id`, or up to four descendant tokens, optionally suffixed with `::text`. `table` requires a selector identifying exactly one table. `markdown` extracts headings, paragraphs, and list items. The HTML parser caps node count and depth. The implementation is deliberately small: no JavaScript, pagination, login, CSS combinators, PDF, OCR, or recursive crawl. The result records source URL, final URL, UTC retrieval, mode, selector, and method provenance (`injected-transport` or `scrapling-static`); page text remains `untrusted-page-data`. Check extracted fields against the visible source before citing them.

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

## Optional packages and next integration boundary

Locally inspected on 2026-10-15: Scrapling 0.4.15, Crawl4AI 0.9.3, Playwright 1.62.0. These are **not mandatory runtime dependencies of this package**. Current Scrapling uses `Fetcher.get(url)` for static pages, `page.status`, `page.body` (bytes), and `StealthyFetcher.fetch(url)` for browser rendering. The older `StealthyFetcher.get` example in the operator's local skill is stale. Crawl4AI uses `AsyncWebCrawler(config=BrowserConfig(...))` and `await crawler.arun(url=..., config=CrawlerRunConfig(...))`; results expose `success` and markdown. Its browser may issue secondary requests, so a URL argument alone cannot constrain browser egress. Do not enable a browser live path until the host constrains every request and redirect. Do not pass credentials or private page content to an optional cloud provider.

Sources: [Scrapling fetcher API](https://scrapling.readthedocs.io/en/latest/api-reference/fetchers.html), [Scrapling fetcher basics](https://scrapling.readthedocs.io/en/latest/fetching/choosing.html), [Crawl4AI v0.9.x quick start](https://docs.crawl4ai.com/core/quickstart/), [Crawl4AI result reference](https://docs.crawl4ai.com/core/crawler-result/). The upstream [Scrapling agent skill](https://github.com/D4Vinci/Scrapling/blob/main/agent-skill/Scrapling-Skill/SKILL.md) and the operator's local `playwright-and-crawl4ai-scraper` informed the tool selection; this text and implementation are original.

## Access decisions

An HTTP 401/403/429, CAPTCHA, login redirect, challenge page, or empty response is a stop condition. No automatic StealthyFetcher or Firecrawl fallback is installed. An operator may separately select a browser method for an authorized public page, but this repository does not currently offer its live transport. Firecrawl requires separate explicit cost and data-sharing authorization; no `.env` lookup, key handling, paid call, or auto-escalation is present.
