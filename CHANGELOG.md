# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

