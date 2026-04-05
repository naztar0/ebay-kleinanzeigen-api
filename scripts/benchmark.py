# to use it please install matplotlib (uv run --group dev python scripts/benchmark.py)
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_QUERY = "pc"


@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    elapsed_times: List[float]

    @property
    def average(self) -> float:
        return statistics.mean(self.elapsed_times)

    @property
    def minimum(self) -> float:
        return min(self.elapsed_times)

    @property
    def maximum(self) -> float:
        return max(self.elapsed_times)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "average": round(self.average, 3),
            "min": round(self.minimum, 3),
            "max": round(self.maximum, 3),
        }


def run_request(
    client: httpx.Client, method: str, url: str, *, params: dict | None = None
) -> float:
    start = time.perf_counter()
    response = client.request(method, url, params=params, timeout=30.0)
    response.raise_for_status()
    # Touch payload to make sure we actually parse it
    _ = response.json()
    return time.perf_counter() - start


def benchmark_listings(
    client: httpx.Client,
    *,
    base_url: str,
    query: str,
    page_count: int,
    iterations: int,
    sort_by: str | None = None,
    start_page: int = 1,
) -> BenchmarkResult:
    url = f"{base_url}/v1/listings"
    params = {
        "query": query,
        "page_count": page_count,
        "min_price": 10,
        "max_price": 300,
    }
    if sort_by:
        params["sort_by"] = sort_by
    if start_page > 1:
        params["start_page"] = start_page

    times = [run_request(client, "GET", url, params=params) for _ in range(iterations)]

    name_parts = [f"query='{query}'", f"pages={page_count}"]
    if sort_by:
        name_parts.append(f"sort='{sort_by}'")
    if start_page > 1:
        name_parts.append(f"start={start_page}")

    return BenchmarkResult(
        name=f"/v1/listings ({', '.join(name_parts)})",
        iterations=iterations,
        elapsed_times=times,
    )


def benchmark_listing_detail(
    client: httpx.Client,
    *,
    base_url: str,
    listing_id: str,
    iterations: int,
) -> BenchmarkResult:
    url = f"{base_url}/v1/listings/{listing_id}"
    times = [run_request(client, "GET", url) for _ in range(iterations)]
    return BenchmarkResult(
        name=f"/v1/listings/{{listing_id}} (id={listing_id})",
        iterations=iterations,
        elapsed_times=times,
    )


def benchmark_listings_detailed(
    client: httpx.Client,
    *,
    base_url: str,
    query: str,
    page_count: int,
    max_concurrent_details: int,
    iterations: int,
) -> BenchmarkResult:
    url = f"{base_url}/v1/listings-detailed"
    times = [
        run_request(
            client,
            "GET",
            url,
            params={
                "query": query,
                "page_count": page_count,
                "min_price": 10,
                "max_price": 300,
                "max_concurrent_details": max_concurrent_details,
            },
        )
        for _ in range(iterations)
    ]
    return BenchmarkResult(
        name=(
            f"/v1/listings-detailed (query='{query}', pages={page_count}, "
            f"concurrency={max_concurrent_details})"
        ),
        iterations=iterations,
        elapsed_times=times,
    )


def parse_page_counts(value: str) -> List[int]:
    try:
        return [int(part) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "page_counts must be integers separated by commas"
        ) from exc


def parse_concurrency_values(value: str) -> List[int]:
    try:
        return [int(part) for part in value.split(",") if part.strip()]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "max_concurrency must be integers separated by commas"
        ) from exc


def resolve_listing_id(client: httpx.Client, base_url: str, query: str) -> str:
    """Fetch one page of listings and return the first ad_id for detail benchmarks."""
    resp = client.get(
        f"{base_url}/v1/listings",
        params={"query": query, "page_count": 1},
        timeout=30.0,
    )
    resp.raise_for_status()
    results = resp.json().get("data", {}).get("results", [])
    if not results:
        raise RuntimeError(
            f"No listings returned for query '{query}'; cannot run detail benchmark."
        )
    return results[0]["adid"]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark Kleinanzeigen API endpoints"
    )
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="API base URL")
    parser.add_argument(
        "--query", default=DEFAULT_QUERY, help="Search term for listing benchmarks"
    )
    parser.add_argument(
        "--page-counts",
        default="1,3,5",
        type=parse_page_counts,
        help="Comma-separated list of page counts",
    )
    parser.add_argument(
        "--iterations", type=int, default=3, help="Iterations per benchmark"
    )
    parser.add_argument(
        "--max-concurrency",
        default="5,10",
        type=parse_concurrency_values,
        help="Comma-separated list of max_concurrent_details values for /v1/listings-detailed",
    )
    parser.add_argument("--output", choices=["table", "json"], default="table")
    parser.add_argument(
        "--chart-output", help="Path to save a PNG chart of the results"
    )
    args = parser.parse_args(argv)

    results: List[BenchmarkResult] = []
    listings_series: List[Tuple[int, float]] = []
    detailed_series: Dict[int, List[Tuple[int, float]]] = {
        value: [] for value in args.max_concurrency
    }

    with httpx.Client() as client:
        # Resolve a live listing ID for the detail benchmark
        print(f"Resolving live listing ID for query='{args.query}'...")
        detail_listing_id = resolve_listing_id(client, args.base_url, args.query)
        print(f"Using listing ID: {detail_listing_id}")

        # Basic listings benchmark
        for page_count in args.page_counts:
            listing_result = benchmark_listings(
                client,
                base_url=args.base_url,
                query=args.query,
                page_count=page_count,
                iterations=args.iterations,
            )
            results.append(listing_result)
            listings_series.append((page_count, listing_result.average))

        # Test with sort by price (if using page_count=3)
        if 3 in args.page_counts:
            results.append(
                benchmark_listings(
                    client,
                    base_url=args.base_url,
                    query=args.query,
                    page_count=3,
                    iterations=args.iterations,
                    sort_by="price",
                )
            )

        # Test with start_page parameter (if using page_count=2)
        if 2 in args.page_counts or 3 in args.page_counts:
            page_cnt = 2 if 2 in args.page_counts else 3
            results.append(
                benchmark_listings(
                    client,
                    base_url=args.base_url,
                    query=args.query,
                    page_count=page_cnt,
                    iterations=args.iterations,
                    start_page=3,
                )
            )

        # Test early termination optimization with limited results query
        results.append(
            benchmark_listings(
                client,
                base_url=args.base_url,
                query="acemagic",  # Limited results query
                page_count=10,
                iterations=args.iterations,
            )
        )

        results.append(
            benchmark_listing_detail(
                client,
                base_url=args.base_url,
                listing_id=detail_listing_id,
                iterations=args.iterations,
            )
        )

        for max_concurrent_details in args.max_concurrency:
            for page_count in args.page_counts:
                detailed_result = benchmark_listings_detailed(
                    client,
                    base_url=args.base_url,
                    query=args.query,
                    page_count=page_count,
                    max_concurrent_details=max_concurrent_details,
                    iterations=args.iterations,
                )
                results.append(detailed_result)
                detailed_series[max_concurrent_details].append(
                    (page_count, detailed_result.average)
                )

    if args.chart_output:
        try:
            import matplotlib.pyplot as plt
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "matplotlib is required for chart generation. Install it or remove --chart-output."
            ) from exc

        if listings_series:
            listings_series.sort(key=lambda item: item[0])
        for values in detailed_series.values():
            values.sort(key=lambda item: item[0])

        figure, axis = plt.subplots(figsize=(8, 4.5))

        if listings_series:
            axis.plot(
                [item[0] for item in listings_series],
                [item[1] for item in listings_series],
                marker="o",
                label="/v1/listings",
            )

        for concurrency, values in detailed_series.items():
            if not values:
                continue
            axis.plot(
                [item[0] for item in values],
                [item[1] for item in values],
                marker="o",
                label=f"/v1/listings-detailed (concurrency={concurrency})",
            )

        axis.set_title("Benchmark: Average Response Time vs Page Count")
        axis.set_xlabel("Page Count")
        axis.set_ylabel("Average Response Time (s)")
        axis.set_xticks(args.page_counts)
        axis.grid(True, linestyle="--", linewidth=0.5, alpha=0.7)
        axis.legend()
        figure.tight_layout()
        figure.savefig(args.chart_output, dpi=150)
        plt.close(figure)

    if args.output == "json":
        print(json.dumps([result.to_dict() for result in results], indent=2))
        return 0

    # Table output
    header = (
        f"{'Benchmark':<65} {'Iter':>4} {'Avg (s)':>8} {'Min (s)':>8} {'Max (s)':>8}"
    )
    print(header)
    print("-" * len(header))
    for result in results:
        print(
            f"{result.name:<65} {result.iterations:>4} "
            f"{result.average:>8.3f} {result.minimum:>8.3f} {result.maximum:>8.3f}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
