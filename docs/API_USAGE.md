# API Usage Guide

## Base URL

```
http://localhost:8000/v1
```

## Endpoints

### GET /listings

Retrieve listing summaries with advanced filtering and pagination.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | None | Search term (e.g., "mini pc") |
| `location` | string | None | Location filter (e.g., "Berlin") |
| `radius` | integer | None | Search radius in km (1-100) |
| `min_price` | integer | None | Minimum price in EUR |
| `max_price` | integer | None | Maximum price in EUR |
| `sort_by` | string | None | Sort order: "price"/"lowest" (ascending), "highest" (descending), or None (newest) |
| `page_count` | integer | 1 | Number of pages to fetch (1-10) |
| `start_page` | integer | 1 | Starting page number |

**Example Requests:**

```bash
# Basic search
curl "http://localhost:8000/v1/listings?query=mini%20pc"

# With price filter and sorting
curl "http://localhost:8000/v1/listings?query=pc&min_price=10&max_price=350&sort_by=price"

# Paginated from specific page
curl "http://localhost:8000/v1/listings?query=pc&start_page=6&page_count=5"
```

### GET /listings-detailed

Same as `/listings` but includes full details for each listing.

**Additional Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_concurrent_details` | integer | 10 | Max concurrent detail fetches (1-20) |

**Example:**

```bash
curl "http://localhost:8000/v1/listings-detailed?query=laptop&page_count=2&max_concurrent_details=10"
```

### GET /listings/{listing_id}

Retrieve detailed information for a single listing.

**Example:**

```bash
curl "http://localhost:8000/v1/listings/2921485881"
```

## Response Format

### Successful Response

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "ad_id": "2921485881",
        "url": "https://www.kleinanzeigen.de/...",
        "title": "Product Title",
        "price": 70.0,
        "currency": "€",
        "negotiable": true,
        "description_snippet": "Product description..."
      }
    ],
    "total_results": 54,
    "pagination": {
      "pages_requested": 2,
      "pages_fetched": 2,
      "start_page": 1,
      "end_page": 2,
      "total_available_results": 117378,
      "results_per_page": 25,
      "duplicates_removed": 0
    },
    "time_taken": 2.143
  },
  "time_taken": 2.143
}
```

### Pagination Metadata

| Field | Description |
|-------|-------------|
| `pages_requested` | Number of pages requested |
| `pages_fetched` | Number of pages successfully fetched |
| `start_page` | Starting page number |
| `end_page` | Ending page number |
| `total_available_results` | Total results available (if detected) |
| `results_per_page` | Results per page (typically 25) |
| `duplicates_removed` | Number of duplicate listings removed |

### Error Response

```json
{
  "success": false,
  "error": "Failed to fetch listings",
  "time_taken": 0.123
}
```

## Use Cases

### Find Cheapest Items

```bash
curl "http://localhost:8000/v1/listings?query=iphone&min_price=50&max_price=300&sort_by=price&page_count=3"
```

### Paginated Fetching

Fetch results in batches without duplicates:

```bash
# First batch: pages 1-5
curl "http://localhost:8000/v1/listings?query=laptop&page_count=5"

# Second batch: pages 6-10
curl "http://localhost:8000/v1/listings?query=laptop&start_page=6&page_count=5"
```

### Location-Based Search

```bash
curl "http://localhost:8000/v1/listings?query=fahrrad&location=Berlin&radius=20"
```

## Python Examples

### Basic Usage

```python
import requests

response = requests.get(
    "http://localhost:8000/v1/listings",
    params={
        "query": "mini pc",
        "min_price": 10,
        "max_price": 350,
        "sort_by": "price",
        "page_count": 3,
    }
)

data = response.json()
print(f"Found {data['data']['total_results']} unique listings")
print(f"Total available: {data['data']['pagination']['total_available_results']}")

for listing in data['data']['results']:
    print(f"{listing['title']}: {listing['price']} EUR")
```

### Batch Fetching

```python
def fetch_all_pages(query, batch_size=5):
    all_listings = []
    page = 1
    
    while True:
        response = requests.get(
            "http://localhost:8000/v1/listings",
            params={
                "query": query,
                "start_page": page,
                "page_count": batch_size,
            }
        )
        
        data = response.json()
        listings = data['data']['results']
        
        if not listings:
            break
            
        all_listings.extend(listings)
        page += batch_size
    
    return all_listings
```

## Interactive Documentation

**Swagger UI:** `http://localhost:8000/docs`

**ReDoc:** `http://localhost:8000/redoc`

## Tips

- Start with fewer pages and increase if needed for better performance
- Check `pagination.duplicates_removed` to see deduplication effectiveness
- Use `pagination.total_available_results` to calculate total pages
- Use `start_page` to avoid re-fetching already seen results
- The API automatically stops fetching when no more pages are available

## Support

For issues or questions, check the application logs at `logs/kleinanzeigen-api_*.log`

