# Ebay Kleinanzeigen API

<div align="center">
  <h3 align="center">Ebay Kleinanzeigen API</h3>

  <p align="center">
    A powerful API interface for Ebay-Kleinanzeigen.de that enables you to fetch listings and specific data.
  </p>

  <p align="center">
    <b>Looking for a ready-to-use solution?</b>
    <br />
    Try it at <a href="https://kleinanzeigen-agent.de/features/developer-api"><strong>kleinanzeigen-agent.de »</strong></a>
    <br />
    Automated Search Agents
    <br />
    Search & Detail API
    <br />
    <a href="https://github.com/DanielWTE/ebay-kleinanzeigen-api/issues">Report Bug</a>
    ·
    <a href="https://github.com/DanielWTE/ebay-kleinanzeigen-api/issues">Request Feature</a>
  </p>
</div>

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Project Structure

This project now follows a modern `src/` based layout:

- `src/app/core/`: Configuration and logging setup
- `src/app/api/routes/`: FastAPI routers
- `src/app/models/`: Pydantic request/response models
- `src/app/services/`: Scraper and HTTP utilities
- `tests/`: Test suite (to be updated)

## Getting Started

### Want to skip the setup?

Visit [kleinanzeigen-agent.de](https://kleinanzeigen-agent.de/features/developer-api) for our hosted solution with additional features and zero configuration required.

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)

### Installation with uv (recommended)

```sh
uv sync
uv run uvicorn src.app.main:app --reload
```

### Installation with pip

### Installation

1. Clone the repository

```sh
git clone https://github.com/DanielWTE/ebay-kleinanzeigen-api.git
cd ebay-kleinanzeigen-api
```

2. Install dependencies

```sh
pip install -r requirements.txt
```

3. Start the API

```sh
uvicorn src.app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Installation using UV

#### Prerequisites

- uv package manager

#### Installation of dependencies

```sh
uv sync
```

#### Start the API

```sh
# Windows
uv run uvicorn src.app.main:app

# macOS/Linux (optional auto-reload for development)
uv run uvicorn src.app.main:app --reload
```

### Installation using Docker

1. Build the Docker image

```sh
docker build -t ebay-kleinanzeigen-api .
```

2. Run the Docker container

```sh
docker run -p 8000:8000 ebay-kleinanzeigen-api
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### 1. Fetch Listings

**Endpoint:** `GET /v1/listings`

**Description:** Retrieves listings as summary records.

#### 2. Fetch Listing Details

**Endpoint:** `GET /v1/listings/{listing_id}`

**Description:** Retrieves a single listing with full detail.

#### 3. Fetch Listings with Details

**Endpoint:** `GET /v1/listings-detailed`

**Description:** Retrieves listings and their detailed information in a single request.

##### Query Parameters

Same as `/v1/listings` plus `max_concurrent_details` (default 10, max 20).

##### Example Request

```http
GET /inserate-detailed?query=laptop&page_count=2&max_concurrent_details=10
```

### Production Deployment

#### Running with Multiple Workers

For production environments, it is recommended to run the API with multiple worker processes to fully utilize CPU cores and handle more concurrent requests.

You can specify the number of workers using the `--workers` flag with `uvicorn`. A good starting point is `(2 * number_of_cpu_cores) + 1`.

```sh
# Example: Start with 4 workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Note:** When running with multiple workers, each worker will have its own `OptimizedPlaywrightManager` instance. Ensure your server has enough RAM to accommodate multiple browser instances.

### Documentation

#### API Response Format

All API endpoints return responses in the following JSON format:

##### API Response Format

```json
{
  "success": true,
  "time_taken": 1.23,
  "unique_results": 100,
  "data": [...],
  "performance_metrics": {
    "pages_requested": 5,
    "pages_successful": 5,
    "success_rate": 100.0,
    "average_page_time": 2.45
  }
}
```

##### Combined Endpoint Response Format

```json
{
  "success": true,
  "time_taken": 3.45,
  "unique_results": 25,
  "data": [
    {
      "adid": "123456",
      "title": "Example Item",
      "price": "100",
      "details": {
        "id": "123456",
        "description": "Full description...",
        "seller": {...},
        "location": {...}
      }
    }
  ],
  "performance_metrics": {
    "listings_found": 25,
    "details_fetched": 25,
    "success_rate": 100.0
  }
}
```

## Performance Features

## Performance Benchmarks

You can run repeatable benchmarks locally using the helper script in `scripts/benchmark.py`. Make sure the API server is already running, then execute:

```bash
uv run python scripts/benchmark.py \
  --iterations 3 \
  --page-counts 1,3,5 \
  --max-concurrency 5,10,15 \
  --query pc \
  --chart-output assets/benchmarks.png
```

This script hits

- `GET /v1/listings` for each requested `page_count`
- `GET /v1/listings/{listing_id}` using listing `3198895972`
- `GET /v1/listings-detailed` for each `page_count` combined with the `max_concurrency` values

The output is a table summarising the average, min and max response times across the chosen iterations and saves a chart overlaying the results to `assets/benchmarks.png`. Use `--output json` if you prefer JSON payloads for automation.

### Sample Benchmark Results

| Endpoint | Parameters | Avg (s) | Min (s) | Max (s) | Notes |
|----------|------------|--------:|--------:|--------:|-------|
| `/v1/listings` | `query=pc`, `pages=1` | 0.899 | 0.736 | 1.030 | Basic search |
| `/v1/listings` | `query=pc`, `pages=3` | 1.985 | 1.661 | 2.239 | Multi-page |
| `/v1/listings` | `query=pc`, `pages=5` | 3.712 | 2.814 | 5.223 | Multi-page |
| `/v1/listings` | `query=pc`, `pages=3`, `sort=price` | 1.543 | 1.275 | 1.698 | With sorting |
| `/v1/listings` | `query=pc`, `pages=3`, `start=3` | 1.595 | 1.521 | 1.644 | Start from page 3 |
| `/v1/listings` | `query=acemagic`, `pages=10` | 1.125 | 0.792 | 1.305 | Early termination (2 pages exist) |
| `/v1/listings/{id}` | `id=3198895972` | 0.894 | 0.817 | 0.959 | Single listing |
| `/v1/listings-detailed` | `pages=1`, `concurrency=5` | 6.571 | 6.106 | 7.212 | With details |
| `/v1/listings-detailed` | `pages=3`, `concurrency=5` | 14.833 | 13.521 | 16.801 | With details |
| `/v1/listings-detailed` | `pages=5`, `concurrency=5` | 20.502 | 19.836 | 21.284 | With details |
| `/v1/listings-detailed` | `pages=1`, `concurrency=10` | 3.833 | 3.453 | 4.034 | Higher concurrency |
| `/v1/listings-detailed` | `pages=3`, `concurrency=10` | 11.189 | 11.038 | 11.460 | Higher concurrency |
| `/v1/listings-detailed` | `pages=5`, `concurrency=10` | 16.519 | 15.946 | 16.987 | Higher concurrency |

![Benchmark chart](assets/benchmarks.png)

### Technical Features

- **uvloop Integration**: High-performance asyncio event loop
- **Context Pooling**: Efficient browser resource reuse
- **Memory Optimization**: Automatic garbage collection and efficient processing
- **Intelligent Concurrency**: Optimal concurrent processing with resource control

API documentation is available at `http://localhost:8000/docs` when running locally.

## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>
