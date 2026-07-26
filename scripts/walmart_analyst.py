#!/usr/bin/env python3
"""
Walmart Analyst Engine — One-click Walmart deep analysis

Three modes:
  competitor — Competitor breakdown (detail + traffic keywords + trends)
  keyword   — Keyword analysis (detail + long-tail keywords + top products)
  market    — Market analysis (category report + top product profiles)
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.cache import TTL_PRESETS, get, set
from utils.compressor import compress
from utils.mcp_client import call_tool_json


def _parse_flat_trend(data: list) -> list[tuple]:
    """Parse Walmart flat trend array [date, value, date, value, ...] → [(date, value), ...]"""
    if not isinstance(data, list) or len(data) < 2:
        return []
    result = []
    for i in range(0, len(data) - 1, 2):
        date_str = str(data[i])
        try:
            val = int(data[i + 1])
        except (ValueError, TypeError):
            val = 0
        result.append((date_str, val))
    return result


def _raw_call(tool_name: str, arguments: dict):
    """Call Walmart tools without registered Schema"""
    return call_tool_json("sorftime_raw_call", {
        "tool_name": tool_name,
        "arguments": arguments,
    })


def _fetch(tool_name: str, params: dict, use_raw: bool = False, optional: bool = False):
    """Cached tool call"""
    cached = get(tool_name, params)
    if cached:
        return cached
    try:
        if use_raw:
            data = _raw_call(tool_name, params)
        else:
            data = call_tool_json(tool_name, params)
        ttl = TTL_PRESETS.get(tool_name, 21600)
        set(tool_name, params, data, ttl)
        return data
    except Exception as e:
        if optional:
            return None
        raise


def analyze_competitor(product_id: str):
    """Competitor analysis: product detail + traffic keywords + sales/rating trends"""
    detail = _fetch("walmart_product_detail_by_product_id",
                    {"product_id": product_id, "site": "US"}, use_raw=True)
    traffic = _fetch("walmart_product_traffic_terms",
                     {"product_id": product_id, "site": "US"}, use_raw=True, optional=True)
    trend_sales = _fetch("walmart_product_trend_by_product_id",
                         {"product_id": product_id, "site": "US", "trend_type": "SalesVolume"},
                         use_raw=True, optional=True)
    trend_star = _fetch("walmart_product_trend_by_product_id",
                        {"product_id": product_id, "site": "US", "trend_type": "Star"},
                        use_raw=True, optional=True)

    print(f"# Walmart Competitor Analysis Report: {product_id}")
    print()

    print("## Product Snapshot")
    print(compress("walmart_product_detail_by_product_id", detail))
    print()

    if traffic and isinstance(traffic, list) and traffic:
        print("## Traffic Keywords TOP 10")
        print(compress("walmart_product_traffic_terms", traffic[:10]))
        print()
    else:
        print("> Traffic keyword data unavailable.")
        print()

    print("## Trend Summary")
    sales_trend = _parse_flat_trend(trend_sales) if isinstance(trend_sales, list) else []
    if sales_trend:
        recent = sales_trend[-7:]  # 最近7天
        trend_str = " → ".join(f"{d[5:]}:{v}" for d, v in recent)
        print(f"- **Sales Volume Trend (Last 7 Days)**: {trend_str}")
        if len(sales_trend) >= 14:
            last7 = sum(v for _, v in sales_trend[-7:])
            prev7 = sum(v for _, v in sales_trend[-14:-7])
            if prev7 > 0:
                change = (last7 - prev7) / prev7 * 100
                arrow = "📈" if change > 0 else "📉"
                print(f"- **Week-over-Week**: {arrow} {change:+.1f}% (last 7d: {last7} vs prev 7d: {prev7})")
    else:
        print("- Sales trend data unavailable.")

    star_trend = _parse_flat_trend(trend_star) if isinstance(trend_star, list) else []
    if star_trend:
        recent = star_trend[-7:]
        trend_str = " → ".join(f"{d[5:]}:{v}" for d, v in recent)
        print(f"- **Rating Trend (Last 7 Days)**: {trend_str}")
    else:
        print("- Rating trend data unavailable.")
    print()


def analyze_keyword(keyword: str):
    """Keyword analysis: detail + extensions + search results"""
    detail = _fetch("walmart_keyword_detail",
                    {"keyword": keyword, "site": "US"}, use_raw=True, optional=True)
    extends = _fetch("walmart_keyword_extends",
                     {"keyword": keyword, "site": "US"}, use_raw=True, optional=True)
    results = _fetch("walmart_keyword_search_results",
                     {"keyword": keyword, "site": "US"}, optional=True)

    print(f"# Walmart Keyword Analysis Report: {keyword}")
    print()

    if detail and isinstance(detail, dict):
        print("## Keyword Detail")
        print(compress("walmart_keyword_detail", detail))
        print()
    else:
        print("> Keyword detail unavailable.")
        print()

    if extends and isinstance(extends, list) and extends:
        print("## Extensions / Long-Tail Keywords")
        print(compress("walmart_keyword_extends", extends))
        print()
    else:
        print("> Extension data unavailable.")
        print()

    if results and isinstance(results, list) and results:
        print("## Search Results — Top Products")
        print(compress("walmart_keyword_search_results", results))
    else:
        print("> Keyword search results unavailable.")


def analyze_market(node_id: str):
    """Market analysis: category report + top product profiles"""
    report = _fetch("walmart_category_report_by_node_id",
                    {"node_id": node_id, "site": "US"}, use_raw=True)

    print(f"# Walmart Market Analysis Report: Category {node_id}")
    print()

    products = report if isinstance(report, list) else []
    if not products:
        print("> No data for this category. Please verify the nodeId.")
        return

    print("## Category Top Products")
    print(compress("walmart_category_report_by_node_id", products))
    print()

    # Batch fetch top 10 product details and traffic keywords
    top10 = products[:10]
    if top10:
        print("## Top Product Profiles (Top 10)")
        print()
        for idx, p in enumerate(top10, 1):
            pid = p.get("ProductId", "")
            title = p.get("Title", "")[:40]
            if not pid:
                continue
            print(f"### {idx}. {title}")
            try:
                detail = _fetch("walmart_product_detail_by_product_id",
                                {"product_id": pid, "site": "US"}, use_raw=True, optional=True)
                if detail and isinstance(detail, dict):
                    brand = detail.get("Brand", "-")
                    seller = detail.get("Seller", "-")
                    ship = detail.get("Shipedby", "-")
                    reviews = detail.get("ReviewsCount", 0)
                    rating = detail.get("Ratings", 0)
                    print(f"- **ProductId**: {pid} | **Brand**: {brand} | **Seller**: {seller}")
                    print(f"- **Fulfillment**: {ship} | **Reviews**: {reviews} | **Rating**: {rating}")
                else:
                    print(f"- **ProductId**: {pid} | Detail unavailable")
            except Exception:
                print(f"- **ProductId**: {pid} | Detail fetch failed")
            print()

        print("## Category Overview")
        sellers = {}
        brands = {}
        wfs_count = 0
        total_sales = 0
        for p in products[:20]:
            sellers[p.get("Seller", "Unknown")] = sellers.get(p.get("Seller", "Unknown"), 0) + 1
            brands[p.get("Brand", "Unknown")] = brands.get(p.get("Brand", "Unknown"), 0) + 1
            if p.get("Shipedby") == "WFS":
                wfs_count += 1
            total_sales += p.get("ListingSalesVolumeOfMonth", 0)

        print(f"- **TOP20 Total Monthly Sales**: {total_sales:,}")
        print(f"- **WFS Share**: {wfs_count}/20 ({wfs_count*5}%)")
        print(f"- **Brand Count**: {len(brands)} (TOP3: {', '.join(sorted(brands, key=brands.get, reverse=True)[:3])})")
        print(f"- **Seller Count**: {len(sellers)} (TOP3: {', '.join(sorted(sellers, key=sellers.get, reverse=True)[:3])})")


def main():
    parser = argparse.ArgumentParser(description="Walmart Analyst Engine")
    parser.add_argument("--mode", required=True, choices=["competitor", "keyword", "market"])
    parser.add_argument("--product-id", default="", help="Walmart ProductId (competitor mode)")
    parser.add_argument("--keyword", default="", help="Keyword (keyword mode)")
    parser.add_argument("--node-id", default="", help="Category nodeId (market mode)")
    args = parser.parse_args()

    if args.mode == "competitor":
        if not args.product_id:
            print("Error: --product-id is required for competitor mode", file=sys.stderr)
            sys.exit(1)
        analyze_competitor(args.product_id)
    elif args.mode == "keyword":
        if not args.keyword:
            print("Error: --keyword is required for keyword mode", file=sys.stderr)
            sys.exit(1)
        analyze_keyword(args.keyword)
    elif args.mode == "market":
        if not args.node_id:
            print("Error: --node-id is required for market mode", file=sys.stderr)
            sys.exit(1)
        analyze_market(args.node_id)


if __name__ == "__main__":
    main()
