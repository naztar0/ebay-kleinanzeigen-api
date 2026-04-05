# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-04-05

### Added
- IP-ban detection: scraper checks response body for Kleinanzeigen's block page before calling `raise_for_status()`, handling both HTTP 200 and HTTP 403 variants of the block response
- `KleinanzeigenBannedError` custom exception in `src/app/exceptions.py`
- `error_category: "ip_banned"` set on `PageMetric` when a ban is detected
- HTTP **503** response with `error_category: "ip_banned"` when all fetched pages return a block — never silently returns empty results when the IP is blocked
- `network_error` category on `PageMetric` for non-status HTTP errors (connection, timeout)
- Separate `except httpx.HTTPStatusError` / `except httpx.HTTPError` handlers in `_fetch_listings_page` for finer error categorisation

### Fixed
- API previously returned `success: true` with 0 results when the host IP was blocked — a silent failure that was impossible to distinguish from a legitimate empty search

## [2.0.0] - 2026-04-05

### Added

- Shared `httpx.AsyncClient` via FastAPI `lifespan` — single connection pool reused across all requests (eliminates per-request TLS handshake overhead)
- Parallel multi-page fetching with `asyncio.gather` + configurable `APP_PAGE_FETCH_CONCURRENCY` semaphore (default 3) — `pages=3` now takes the same wall-clock time as `pages=1`
- `GET /health` endpoint (excluded from OpenAPI schema) for Docker/reverse-proxy health checks
- `X-Request-ID` middleware — attaches a UUID to every request, binds it to all log lines, echoes it in the response header
- `slowapi` rate limiter wired up and configurable via `APP_RATE_LIMIT_ENABLED` / `APP_RATE_LIMIT_REQUESTS` / `APP_RATE_LIMIT_WINDOW_SECONDS`
- `CORSMiddleware` with `allow_methods=["GET"]` and configurable `APP_CORS_ALLOW_ORIGINS`
- In-memory response caching via `fastapi-cache2` (60 s for listings, 300 s for single detail)
- Typed `DetailedListingItem(summary, detail)` model — `/v1/listings-detailed` now has a proper OpenAPI schema instead of `list`
- `PerformanceMetrics` exposed in `ListingsResponse.metrics` (was computed but discarded)
- `sort_by` validated as `Literal[...]` — invalid values rejected at input rather than silently no-opping
- `start_page` upper bound `le=200`
- `listing_id` regex validation `^\d{5,15}(-[a-z0-9-]+)?$` before any network call
- uvloop auto-installed on non-Windows platforms
- Connection pool tuning: `APP_HTTP_MAX_CONNECTIONS`, `APP_HTTP_MAX_KEEPALIVE_CONNECTIONS`
- `APP_CACHE_TTL_SECONDS` and `APP_CACHE_TTL_DETAIL_SECONDS` settings

### Changed

- **BREAKING**: Error responses now use `ApiErrorResponse` shape `{"success": false, "error": "..."}` instead of FastAPI's default `{"detail": "..."}`
- `KleinanzeigenScraperService` accepts injected `client: httpx.AsyncClient` — no longer creates its own client; `close()` method removed
- Routes no longer construct or close the scraper; use `ScraperDep` Annotated dependency instead
- 302 redirect detection uses `response.is_redirect` (reliable boolean) instead of string-matching the error message
- `_slugify` now translates German umlauts before ASCII-folding (`möbel` → `moebel`, previously → `mbel`)
- Log rotation changed from time-based `"12:00"` to size-based `"100 MB"`
- All `Optional[T]` / `List[T]` / `Dict[K,V]` → `T | None` / `list[T]` / `dict[K,V]`
- `Location.zip` and `Location.city` default to `""` (scraper may produce empty strings for these)
- `ListingDetail.title` no longer requires `min_length=1`
- `pytest` moved to dev dependency group
- Benchmark script resolves listing ID dynamically from a live search instead of using a hardcoded ID

### Removed

- Dead `_matches_price_filters` method (price filtering is handled by Kleinanzeigen URL params)
- Unused `LISTINGS_SEARCH_PATH` constant
- `HttpClientFactory` class replaced by `create_shared_client()` function
- `import time` inside `_fetch_listings_page` (moved to module top)

### Fixed

- `GET /v1/listings/{listing_id}` now returns 404 for expired or removed listings instead of 500
- Concurrent listing-page fetching no longer shares mutable state between coroutines

### Performance

- `pages=3` benchmark: **0.335 s** (was ~1.985 s) — ~6× faster due to parallel page fetching
- `pages=5` benchmark: **0.629 s** (was ~3.712 s) — ~6× faster
- Single detail: **0.342 s** (was ~0.894 s) — ~2.6× faster due to connection reuse
- Cache hits for identical queries return sub-millisecond responses

## [1.0.0] - 2025-10-02

### Added

- Sort by price parameter (`sort_by`): sort listings by lowest or highest price
- Start page parameter (`start_page`): begin pagination from any page number
- Pagination metadata in API responses including total available results
- Automatic deduplication of listings across pages using ad_id tracking
- Total results extraction from breadcrumb HTML
- Early termination optimization for queries with limited results
- Duplicate tracking counter in pagination metadata
- Comprehensive API usage documentation
- Performance benchmark suite with new feature testing

### Changed

- **BREAKING**: `fetch_listings()` method now returns 3-tuple instead of 2-tuple (listings, metrics, pagination)
- Pagination URL format now uses correct `/seite:X/` path instead of query parameters
- API response structure now includes `pagination` metadata object
- Improved URL building to correctly handle all parameter combinations
- Enhanced logging with early termination indicators

### Fixed

- Critical pagination bug where pages weren't actually changing
- Duplicate listings appearing in results
- Incorrect URL format causing failed page requests
- Performance issue with unnecessary 302 redirect requests
- German number formatting in total results parsing

### Performance

- Up to 80% faster response times for queries with limited results
- Early termination prevents unnecessary HTTP requests when last page is reached
- Zero duplicate listings in responses
- Smart pagination detection reduces overhead

## [0.2.0] - 2025-09-30

### Added

- Initial pagination support
- Price filtering (min_price, max_price)
- Location-based search with radius
- Multi-page fetching capability
- Performance metrics in responses

### Changed

- Migrated to src-based project structure
- Updated to FastAPI with async/await patterns
- Improved error handling and logging

## [0.1.0] - 2025-09-15

### Added

- Initial release
- Basic listing search functionality
- Single listing detail retrieval
- Docker support
- Basic API documentation
