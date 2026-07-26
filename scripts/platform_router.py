#!/usr/bin/env python3
"""
多平台专项分析 — 统一处理 Amazon / TikTok / Shopee / TEMU / Walmart 的参数映射与工具调用
为不同平台卖家提供一致入口，自动适配参数名差异
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.cache import TTL_PRESETS, get, set
from utils.compressor import compress
from utils.mcp_client import call_tool_json


def run_amazon(site: str, mode: str, asin: str, node_id: str, keyword: str):
    """Amazon 平台分析"""
    if mode == "product":
        if not asin:
            print("Error: Amazon product mode requires --asin", file=sys.stderr)
            sys.exit(1)
        params = {"amz_site": site, "asin": asin}
        cached = get("product_detail", params)
        data = cached if cached else call_tool_json("product_detail", params)
        if not cached:
            set("product_detail", params, data, TTL_PRESETS["product_detail"])
        print(f"# Amazon {site} 产品详情: {asin}")
        print()
        print(compress("product_detail", data))

    elif mode == "category":
        if not node_id:
            print("Error: Amazon category mode requires --node-id", file=sys.stderr)
            sys.exit(1)
        params = {"amz_site": site, "node_id": node_id}
        cached = get("category_report", params)
        data = cached if cached else call_tool_json("category_report", params)
        if not cached:
            set("category_report", params, data, TTL_PRESETS["category_report"])
        print(f"# Amazon {site} 类目报告: {node_id}")
        print()
        print(compress("category_report", data))

    elif mode == "search":
        kw = keyword or "best seller"
        params = {"amz_site": site, "search_name": kw}
        cached = get("product_search", params)
        data = cached if cached else call_tool_json("product_search", params)
        if not cached:
            set("product_search", params, data, TTL_PRESETS["product_search"])
        print(f"# Amazon {site} 产品搜索: {kw}")
        print()
        print(compress("product_search", data))

    else:
        print(f"Error: unsupported Amazon mode '{mode}'", file=sys.stderr)
        sys.exit(1)


def run_tiktok(site: str, mode: str, product_id: str, category_id: str, keyword: str = ""):
    """TikTok Shop 平台分析"""
    if mode == "product":
        if not product_id:
            print("Error: TikTok product mode requires --product-id", file=sys.stderr)
            sys.exit(1)
        params = {"site": site, "product_id": product_id}
        cached = get("tiktok_product_detail", params)
        data = cached if cached else call_tool_json("tiktok_product_detail", params)
        if not cached:
            set("tiktok_product_detail", params, data, TTL_PRESETS.get("tiktok_product_detail", 21600))
        print(f"# TikTok {site} 产品详情: {product_id}")
        print()
        print(compress("tiktok_product_detail", data))

    elif mode == "category":
        if not category_id:
            print("Error: TikTok category mode requires --category-id", file=sys.stderr)
            sys.exit(1)
        params = {"site": site, "category_id": category_id}
        cached = get("tiktok_category_report", params)
        data = cached if cached else call_tool_json("tiktok_category_report", params)
        if not cached:
            set("tiktok_category_report", params, data, TTL_PRESETS.get("tiktok_category_report", 21600))
        print(f"# TikTok {site} 类目报告: {category_id}")
        print()
        print(compress("tiktok_category_report", data))

    elif mode == "search":
        print(f"Error: TikTok Shop 当前未在 Sorftime MCP 中开放 `product_search` 工具。", file=sys.stderr)
        print("    替代方案：", file=sys.stderr)
        print("    1. 有 product_id 时，使用 --mode product --product-id <id>", file=sys.stderr)
        print("    2. 有 category_id 时，使用 --mode category --category-id <id>", file=sys.stderr)
        print("    3. 需要探索相似产品时，可通过 sorftime_raw_call 调用 tiktok_similar_product", file=sys.stderr)
        sys.exit(1)

    else:
        print(f"Error: unsupported TikTok mode '{mode}'", file=sys.stderr)
        sys.exit(1)


def run_walmart(site: str, mode: str, product_id: str, node_id: str, keyword: str):
    """Walmart 平台分析"""
    if mode == "product":
        if not product_id:
            print("Error: Walmart product mode requires --product-id", file=sys.stderr)
            sys.exit(1)
        params = {"site": site, "product_id": product_id}
        cached = get("walmart_product_detail_by_product_id", params)
        data = cached if cached else call_tool_json("sorftime_raw_call", {
            "tool_name": "walmart_product_detail_by_product_id",
            "arguments": params,
        })
        if not cached:
            set("walmart_product_detail_by_product_id", params, data,
                TTL_PRESETS.get("walmart_product_detail_by_product_id", 21600))
        print(f"# Walmart {site} 产品详情: {product_id}")
        print()
        print(compress("walmart_product_detail_by_product_id", data))

    elif mode == "category":
        if not node_id:
            print("Error: Walmart category mode requires --node-id", file=sys.stderr)
            sys.exit(1)
        params = {"site": site, "node_id": node_id}
        cached = get("walmart_category_report_by_node_id", params)
        data = cached if cached else call_tool_json("sorftime_raw_call", {
            "tool_name": "walmart_category_report_by_node_id",
            "arguments": params,
        })
        if not cached:
            set("walmart_category_report_by_node_id", params, data,
                TTL_PRESETS.get("walmart_category_report_by_node_id", 86400))
        print(f"# Walmart {site} 类目报告: {node_id}")
        print()
        print(compress("walmart_category_report_by_node_id", data))

    elif mode == "search":
        kw = keyword or "best seller"
        params = {"site": site, "keyword": kw}
        cached = get("walmart_keyword_search_results", params)
        data = cached if cached else call_tool_json("walmart_keyword_search_results", params)
        if not cached:
            set("walmart_keyword_search_results", params, data,
                TTL_PRESETS.get("walmart_keyword_search_results", 21600))
        print(f"# Walmart {site} 关键词搜索: {kw}")
        print()
        print(compress("walmart_keyword_search_results", data))

    else:
        print(f"Error: unsupported Walmart mode '{mode}'", file=sys.stderr)
        sys.exit(1)


def run_raw_fallback(platform: str, site: str, tool_name: str, arguments: dict):
    """其他平台 fallback：通过 sorftime_raw_call 调用未注册 schema 的工具"""
    params = {"tool_name": tool_name, "arguments": arguments}
    print(f"# {platform.upper()} {site} 原始调用: {tool_name}")
    print()
    print("> 当前 Sorftime MCP 对该平台的注册工具有限，正通过 `sorftime_raw_call` 透传调用。")
    print()
    data = call_tool_json("sorftime_raw_call", params)
    print("```json")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
    print("```")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True, choices=["amazon", "tiktok", "shopee", "temu", "walmart"])
    parser.add_argument("--site", default="US")
    parser.add_argument("--mode", default="product", choices=["product", "category", "search"])
    parser.add_argument("--asin", default="")
    parser.add_argument("--product-id", default="")
    parser.add_argument("--category-id", default="")
    parser.add_argument("--node-id", default="")
    parser.add_argument("--keyword", default="")
    args = parser.parse_args()

    if args.platform == "amazon":
        run_amazon(args.site, args.mode, args.asin, args.node_id, args.keyword)
    elif args.platform == "tiktok":
        run_tiktok(args.site, args.mode, args.product_id, args.category_id, args.keyword)
    elif args.platform == "walmart":
        run_walmart(args.site, args.mode, args.product_id, args.node_id, args.keyword)
    else:
        # Shopee / TEMU 的原始调用映射（示例）
        raw_tool_map = {
            "shopee": "shopee_product_search" if args.mode == "search" else "shopee_product_detail",
            "temu": "temu_product_search" if args.mode == "search" else "temu_product_detail",
        }
        tool = raw_tool_map.get(args.platform, f"{args.platform}_product_detail")
        # 构造通用参数
        raw_args = {"site": args.site}
        if args.asin:
            raw_args["asin"] = args.asin
        if args.product_id:
            raw_args["product_id"] = args.product_id
        if args.keyword:
            raw_args["keyword"] = args.keyword
        run_raw_fallback(args.platform, args.site, tool, raw_args)


if __name__ == "__main__":
    main()