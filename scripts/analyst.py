#!/usr/bin/env python3
"""
Analyst Engine — Competitor Analysis / Keyword Analysis / Market Analysis
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.cache import TTL_PRESETS, get, set
from utils.compressor import compress
from utils.formatter import fmt_competitor_brief
from utils.mcp_client import call_tool_json


def analyze_competitor(platform: str, site: str, asin: str):
    """Competitor analysis: detail + reviews + traffic keywords + competitor keywords"""
    amz_site = site if platform == "amazon" else "US"

    def fetch(tool: str, params: dict):
        cached = get(tool, params)
        if cached:
            return cached
        data = call_tool_json(tool, params)
        set(tool, params, data, TTL_PRESETS.get(tool, 21600))
        return data

    detail = fetch("product_detail", {"amz_site": amz_site, "asin": asin})
    reviews = fetch("product_reviews", {"amz_site": amz_site, "asin": asin})
    traffic = fetch("product_traffic_terms", {"amz_site": amz_site, "asin": asin})
    keywords = fetch("competitor_product_keywords", {"amz_site": amz_site, "asin": asin})

    print(fmt_competitor_brief(asin, detail, reviews, traffic))
    print()
    print("## Keyword Rankings")
    print(compress("competitor_product_keywords", keywords))


def analyze_keyword(platform: str, site: str, keyword: str):
    """Keyword analysis: detail + extensions + search results"""
    amz_site = site if platform == "amazon" else "US"

    def fetch(tool: str, params: dict, optional: bool = False):
        cached = get(tool, params)
        if cached:
            return cached
        try:
            data = call_tool_json(tool, params)
            set(tool, params, data, TTL_PRESETS.get(tool, 43200))
            return data
        except Exception as e:
            if optional:
                fetch.errors[tool] = str(e).split("\n")[0][:120]
                return None
            raise

    fetch.errors = {}

    detail = fetch("keyword_detail", {"keyword_support_site": amz_site, "keyword": keyword})
    extends = fetch("keyword_extends", {"keyword_support_site": amz_site, "keyword": keyword}, optional=True)
    results = fetch("keyword_search_results", {"keyword_support_site": amz_site, "keyword": keyword}, optional=True)

    print(f"# Keyword Analysis Report: {keyword} ({platform.upper()} {amz_site})")
    print()
    print("## Keyword Detail")
    print(compress("keyword_detail", detail))
    print()
    if extends:
        print("## Extensions / Long-Tail Keywords")
        print(compress("keyword_extends", extends))
        print()
    else:
        print(f"> Extension data unavailable: {fetch.errors.get('keyword_extends', 'Unknown reason')}. Retry later.")
        print()
    if results:
        print("## Search Results — Top Products")
        print(compress("keyword_search_results", results))
    else:
        print(f"> Search results unavailable: {fetch.errors.get('keyword_search_results', 'Unknown reason')}. Retry later.")


def analyze_market(platform: str, site: str, node_id: str):
    """Market analysis: category report"""
    amz_site = site if platform == "amazon" else "US"

    params = {"amz_site": amz_site, "node_id": node_id}
    cached = get("category_report", params)
    if cached:
        data = cached
    else:
        data = call_tool_json("category_report", params)
        set("category_report", params, data, TTL_PRESETS["category_report"])

    print(f"# Market Analysis Report: Category {node_id} ({platform.upper()} {amz_site})")
    print()
    print("## Category Top 100")
    print(compress("category_report", data))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", required=True, choices=["competitor", "keyword", "market"])
    parser.add_argument("--platform", default="amazon")
    parser.add_argument("--site", default="US")
    parser.add_argument("--asin", default="")
    parser.add_argument("--keyword", default="")
    parser.add_argument("--node-id", default="")
    args = parser.parse_args()

    if args.mode == "competitor":
        if not args.asin:
            print("Error: --asin is required for competitor mode", file=sys.stderr)
            sys.exit(1)
        analyze_competitor(args.platform, args.site, args.asin)
    elif args.mode == "keyword":
        if not args.keyword:
            print("Error: --keyword is required for keyword mode", file=sys.stderr)
            sys.exit(1)
        analyze_keyword(args.platform, args.site, args.keyword)
    elif args.mode == "market":
        if not args.node_id:
            print("Error: --node-id is required for market mode", file=sys.stderr)
            sys.exit(1)
        analyze_market(args.platform, args.site, args.node_id)


if __name__ == "__main__":
    main()