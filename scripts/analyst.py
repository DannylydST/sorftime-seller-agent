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


def _organic_share_brief(traffic) -> str:
    """Compute organic vs ad share from product_traffic_terms `exposure_position`
    (values "Organic"/"Ad"/"Ad,Organic"). Low organic share = buy-traffic bestseller
    whose demand depends on ads — a red flag for new entrants (v3.6.1)."""
    if isinstance(traffic, dict) and "data" in traffic:
        traffic = traffic.get("data", [])
    if not isinstance(traffic, list) or not traffic:
        return ""
    organic = 0
    ad = 0
    for item in traffic:
        pos = str(item.get("exposure_position", item.get("曝光位置", ""))).lower()
        if "organic" in pos:
            organic += 1
        if "ad" in pos:
            ad += 1
    total = len(traffic)
    org_ratio = organic / total if total else 0
    ad_ratio = ad / total if total else 0
    if org_ratio >= 0.7:
        return ""  # healthy organic share, no flag
    if org_ratio < 0.5:
        return (f"- **Organic Traffic Share 🔴**: only {organic}/{total} traffic keywords are organic "
                f"({org_ratio*100:.0f}%), {ad_ratio*100:.0f}% ad-involved — **buy-traffic bestseller**, "
                f"demand depends on ads; new entrants should not compete head-on\n")
    return (f"- **Organic Traffic Share 🟡**: {organic}/{total} organic ({org_ratio*100:.0f}%), "
            f"{ad_ratio*100:.0f}% ad-involved — moderate ad dependence\n")


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
    org_brief = _organic_share_brief(traffic)
    if org_brief:
        print(org_brief)
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