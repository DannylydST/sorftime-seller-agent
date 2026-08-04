#!/usr/bin/env python3
"""
Sorftime MCP Bridge
将 Sorftime 的 HTTP MCP 端点桥接为本地 stdio MCP Server

--one-shot mode: pure httpx HTTP call, does NOT import mcp (avoids Windows C-extension segfault).
Server mode: imports mcp and runs stdio server.
"""

import os
import sys
from pathlib import Path

_ONE_SHOT = "--one-shot" in sys.argv

if _ONE_SHOT:
    # ── One-shot path: no mcp import needed ──────────────────────
    import asyncio
    import json
    import httpx
    from typing import Any, Dict, List, Optional
    from utils.env_config import load_env
    from utils.platform_utils import get_venv_python

    # Stub mcp types — only referenced in function signatures, never called in --one-shot
    class _MCPStub:
        def __init__(self, *args, **kwargs): pass
    Tool = _MCPStub
    TextContent = _MCPStub
    Server = _MCPStub
    async def stdio_server(*args, **kwargs):
        if False: yield  # pragma: no cover

else:
    # ── Server path: needs mcp, redirect to venv if missing ──────
    try:
        import mcp  # noqa: F401
    except ImportError:
        venv_python = None
        try:
            from utils.platform_utils import get_venv_python
            venv_python = get_venv_python()
        except Exception:
            pass
        if venv_python and venv_python.exists():
            if sys.platform == "win32":
                os.execve(str(venv_python), [str(venv_python), __file__] + sys.argv[1:], os.environ.copy())
            else:
                os.execv(str(venv_python), [str(venv_python), __file__] + sys.argv[1:])
        else:
            print("ERROR: mcp module not found. Run install.py first to create the virtual environment.", file=sys.stderr)
            sys.exit(1)

    import asyncio
    import json
    import httpx
    from typing import Any, Dict, List, Optional
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
    from utils.env_config import load_env

    # ── MCP version guard: block 2.x on startup ──────────────────
    try:
        from importlib.metadata import version as _get_version
        _mcp_version = _get_version("mcp")
        _mcp_major = int(_mcp_version.split(".")[0])
    except Exception:
        _mcp_version = "unknown"
        _mcp_major = 1  # assume safe
    if _mcp_major >= 2:
        print(
            f"ERROR: MCP {_mcp_version} is not yet supported (breaking changes from 1.x).",
            "Please run:  python3 scripts/install.py --upgrade",
            "This will install mcp>=1.0.0,<2.0.0 into the virtual environment.",
            sep="\n", file=sys.stderr,
        )
        sys.exit(1)

load_env()
SORFTIME_MCP_URL = os.getenv("SORFTIME_MCP_URL", "https://mcp.sorftime.com")
SORFTIME_MCP_KEY = os.getenv("SORFTIME_MCP_KEY", "")

# ── 动态 Schema 加载（方案 B：全自动同步） ──
# 优先从 schema_store 加载（由 sync_manager.py 同步生成），
# 若不存在则回退到硬编码（首次安装或同步失败时兜底）

def _load_core_tools() -> list[dict]:
    """加载工具 Schema：优先动态存储，其次硬编码"""
    tools = []
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from utils.schema_store import load_latest

        dynamic_tools = load_latest()
        if dynamic_tools:
            # 转换为 bridge 需要的格式（服务端 Schema 已是标准格式，直接透传）
            tools = [
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "inputSchema": t.get("inputSchema", {"type": "object", "properties": {}, "required": []}),
                }
                for t in dynamic_tools
            ]
    except Exception:
        pass  # 回退到硬编码

    if not tools:
        # 回退：硬编码的核心工具（首次安装或 schema_store 不可用时兜底）
        tools = list(_FALLBACK_CORE_TOOLS)

    # 始终追加本地代理工具（不在服务端 Schema 中，由 bridge 本地处理）
    raw_names = {t["name"] for t in tools}
    if "sorftime_raw_call" not in raw_names:
        tools.append({
            "name": "sorftime_raw_call",
            "description": "透传调用任意 Sorftime MCP 工具（用于访问未在 bridge 中单独注册 Schema 的工具）",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "要调用的 Sorftime 工具名称"},
                    "arguments": {"type": "object", "description": "工具参数（JSON 对象）"},
                },
                "required": ["tool_name", "arguments"],
            },
        })

    return tools


# 硬编码后备（首次安装或自动同步未运行时兜底）
_FALLBACK_CORE_TOOLS = [
    {
        "name": "ali1688_product_request",
        "description": """Query the product details on the 1688 platform. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "The product ID to be queried.",
                    "type": "string"
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "ali1688_product_search",
        "description": """Search product information on the 1688 platform across multiple dimensions. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "description": "Query based on a category (not limited to leaf categories); if specified, search within that category.",
                    "type": "string",
                    "default": ""
                },
                "product_id": {
                    "description": "Query similar products based on a ProductId (note: it does not query only this ProductId; to fetch that exact product, call the product_request tool).",
                    "type": "string",
                    "default": ""
                },
                "supplier_name": {
                    "description": "Fuzzy-match products by supplier name.",
                    "type": "string",
                    "default": ""
                },
                "supplier_type": {
                    "description": "Filter by supplier type, single choice. 1: Powerful merchant, 2: Super factory.",
                    "type": "integer",
                    "default": 0
                },
                "supplier_member_type": {
                    "description": "Filter by supplier member type, single choice. 1: Deep certified, 2: Non-deep certified.",
                    "type": "integer",
                    "default": 0
                },
                "rights": {
                    "description": "Filter by rights/benefits. Multiple choice, comma-separated, e.g. \"1,2,3\". 1: 7-day free return, 2: free shipping insurance, 3: ship within 48 hours.",
                    "type": "string",
                    "default": ""
                },
                "dropshipping_price_range_min": {
                    "description": "Filter products with selling price greater than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "dropshipping_price_range_max": {
                    "description": "Filter products with selling price less than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "cumulative_sale_count_min": {
                    "description": "Filter products with cumulative sales volume greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "cumulative_sale_count_max": {
                    "description": "Filter products with cumulative sales volume less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "recent_30_day_sale_min": {
                    "description": "Filter products with sales quantity in the last 30 days greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "recent_30_day_sale_max": {
                    "description": "Filter products with sales quantity in the last 30 days less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "repurchase_rate_min": {
                    "description": "Filter products with repurchase rate greater than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "repurchase_rate_max": {
                    "description": "Filter products with repurchase rate less than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "service_score_min": {
                    "description": "Filter products with overall service score greater than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "service_score_max": {
                    "description": "Filter products with overall service score less than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "sku_count_min": {
                    "description": "Filter products with SKU count greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "sku_count_max": {
                    "description": "Filter products with SKU count less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "stock_count_min": {
                    "description": "Filter products with stock count greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "stock_count_max": {
                    "description": "Filter products with stock count less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "online_date_range_min": {
                    "description": "Filter products by listing start date, date format yyyy-MM-dd.",
                    "type": "string",
                    "default": ""
                },
                "online_date_range_max": {
                    "description": "Filter products by listing end date, date format yyyy-MM-dd.",
                    "type": "string",
                    "default": ""
                },
                "page": {
                    "description": "Which page of data to query, defaults to page 1.",
                    "type": "integer",
                    "default": 1
                }
            }
        },
    },
    {
        "name": "ali1688_product_search_from_image",
        "description": """Search products on the 1688 platform by image. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "image_url": {
                    "description": "Image URL, required. Must pass a web image URL, and the image size must not exceed 1MB.",
                    "type": "string"
                },
                "page": {
                    "description": "Which page of data to query, defaults to page 1.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "image_url"
            ]
        },
    },
    {
        "name": "ali1688_product_variations",
        "description": """Find the variation (SKU) data of a product on the 1688 platform by product ID. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "The product ID to be queried.",
                    "type": "string"
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "ali1688_similar_product",
        "description": """Find sourcing/wholesale suppliers for a product on the 1688 platform. Can be used to analyze the procurement cost price of a product.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "search_name": {
                    "description": "The product name to search for.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "search_name"
            ]
        },
    },
    {
        "name": "category_keywords",
        "description": """Query the core keywords of an Amazon sub-category market. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "description": "Query the specified sub-category market by nodeid; data type: string.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "node_id"
            ]
        },
    },
    {
        "name": "category_name_search",
        "description": """Query Amazon sub-category markets by name, returning the NodeID and Name of matching sub-categories.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category_name": {
                    "description": "The name of the category market to query.",
                    "type": "string"
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "category_name"
            ]
        },
    },
    {
        "name": "category_report",
        "description": """Query the real-time top-100-by-sales product data report for a specified sub-category on Amazon.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "description": "Sub-category node_id, query this specific sub-category data; data type: string.",
                    "type": "string"
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "node_id"
            ]
        },
    },
    {
        "name": "category_report_from_history",
        "description": """Query the historical-period top-100-by-sales product data report for a specified sub-category on Amazon. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "description": "View historical data; specify the start date in yyyy-MM-dd format.",
                    "type": "string"
                },
                "end_date": {
                    "description": "View historical data; after specifying start_date, this specifies the end date. Supports a max combination of 40 days.",
                    "type": "string"
                },
                "node_id": {
                    "description": "Sub-category node_id, query this specific sub-category data; data type: string.",
                    "type": "string"
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "start_date",
                "end_date",
                "node_id"
            ]
        },
    },
    {
        "name": "category_search_from_product_name",
        "description": """Search Amazon sub-category markets related to a given product category name (e.g. air fryer, phone power bank); returns data sorted by sales volume in descending order. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_name": {
                    "description": "The product category name to search (e.g. air fryer, phone power bank).",
                    "type": "string"
                },
                "month_sales_volume_min": {
                    "description": "Optional: filter sub-category markets whose monthly sales volume is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "month_sales_volume_max": {
                    "description": "Optional: filter sub-category markets whose monthly sales volume is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "ratings_min": {
                    "description": "Optional: filter sub-category markets whose star rating is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "ratings_max": {
                    "description": "Optional: filter sub-category markets whose star rating is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "ratings_count_min": {
                    "description": "Optional: filter sub-category markets whose review count is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "ratings_count_max": {
                    "description": "Optional: filter sub-category markets whose review count is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "price_min": {
                    "description": "Optional: filter sub-category markets whose average selling price (local currency) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "price_max": {
                    "description": "Optional: filter sub-category markets whose average selling price (local currency) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "seasonal_popular_product": {
                    "description": "Optional: filter sub-categories whose peak season is the given month. Defaults to Both.",
                    "type": "string",
                    "enum": [
                        "Both",
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December"
                    ],
                    "default": "Both"
                },
                "top3_product_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-3 products sales-volume share of top-100 (sales-monopoly index) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "top3_product_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-3 products sales-volume share of top-100 (sales-monopoly index) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "amazon_owned_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose Amazon-owned products sales-volume share within top-100 (seller-monopoly index) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "amazon_owned_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose Amazon-owned products sales-volume share within top-100 (seller-monopoly index) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "top100_top400_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-100 products sales-volume share within top-400 (lower share = longer-tail) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "top100_top400_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-100 products sales-volume share within top-400 (lower share = longer-tail) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "newproduct_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose new-product sales-volume share (products listed within 3 months) within top-100 is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "newproduct_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose new-product sales-volume share (products listed within 3 months) within top-100 is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "product_name"
            ]
        },
    },
    {
        "name": "category_search_from_top_node",
        "description": """Search Amazon sub-category markets under a given top-level category (e.g. automotive, home & kitchen); returns data sorted by sales volume in descending order.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "top_node": {
                    "description": "The top-level category to search under (e.g. automotive, home & kitchen); obtain the top-level node id/name via category_tree first.",
                    "type": "string"
                },
                "month_sales_volume_min": {
                    "description": "Optional: filter sub-category markets whose monthly sales volume is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "month_sales_volume_max": {
                    "description": "Optional: filter sub-category markets whose monthly sales volume is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "ratings_min": {
                    "description": "Optional: filter sub-category markets whose star rating is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "ratings_max": {
                    "description": "Optional: filter sub-category markets whose star rating is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "ratings_count_min": {
                    "description": "Optional: filter sub-category markets whose review count is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "ratings_count_max": {
                    "description": "Optional: filter sub-category markets whose review count is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "price_min": {
                    "description": "Optional: filter sub-category markets whose average selling price (local currency) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "price_max": {
                    "description": "Optional: filter sub-category markets whose average selling price (local currency) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "seasonal_popular_product": {
                    "description": "Optional: filter sub-categories whose peak season is the given month. Defaults to Both.",
                    "type": "string",
                    "enum": [
                        "Both",
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December"
                    ],
                    "default": "Both"
                },
                "top3_product_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-3 products sales-volume share of top-100 (sales-monopoly index) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "top3_product_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-3 products sales-volume share of top-100 (sales-monopoly index) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "amazon_owned_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose Amazon-owned products sales-volume share within top-100 (seller-monopoly index) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "amazon_owned_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose Amazon-owned products sales-volume share within top-100 (seller-monopoly index) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "top100_top400_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-100 products sales-volume share within top-400 (lower share = longer-tail) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "top100_top400_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-100 products sales-volume share within top-400 (lower share = longer-tail) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "newproduct_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose new-product sales-volume share (products listed within 3 months) within top-100 is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "newproduct_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose new-product sales-volume share (products listed within 3 months) within top-100 is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "top_node"
            ]
        },
    },
    {
        "name": "category_tree",
        "description": """Query the product category structure on the Amazon platform. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                },
                "node_id": {
                    "description": "Optional: if specified, returns the child categories of this node_id; if not specified, returns the top-level and second-level categories. Data type: string.",
                    "type": "string",
                    "default": ""
                }
            }
        },
    },
    {
        "name": "category_trend",
        "description": """Query Amazon sub-category market trend data, based on the sub-category's top-100 products statistics.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "description": "The sub-category node_id to query; data type: string.",
                    "type": "string"
                },
                "trend_index": {
                    "description": "The trend type. Defaults to SalesCount.",
                    "type": "string",
                    "enum": [
                        "SalesCount",
                        "BrandProductCount",
                        "SellerProductCount",
                        "AvgPrice",
                        "AvgRatingCount",
                        "AvgScore",
                        "NewProductSalesAmountShare",
                        "AmazonSalesAmountShare",
                        "Top3ProductSalesAmountShare",
                        "Top3BrandSalesAmountShare",
                        "Top3SellerSalesAmountShare"
                    ],
                    "default": "SalesCount"
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "node_id"
            ]
        },
    },
    {
        "name": "change_favorite_keyword",
        "description": """Move a favorited keyword in my Amazon platform keyword library to a specified folder; if the folder does not exist, it will be created. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to be moved.",
                    "type": "string"
                },
                "to_dict": {
                    "description": "The name of the destination folder; it will be auto-created if it does not exist.",
                    "type": "string"
                },
                "from_dict": {
                    "description": "Source folder name. Optional; if specified, moves the keyword from the given source folder.",
                    "type": "string",
                    "default": ""
                },
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "keyword",
                "to_dict"
            ]
        },
    },
    {
        "name": "competitor_product_keywords",
        "description": """Get the exposure positions of a product's competitors under core keywords on the Amazon platform; this calculation only uses organic exposure (excluding ad exposure), to analyze the product's traffic-acquisition ability (e.g. if it ranks near the top in high-volume core keywords, it has strong traffic-acquisition ability; otherwise it needs improvement).""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asin": {
                    "description": "Product ASIN.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "asin"
            ]
        },
    },
    {
        "name": "del_favorite_keyword",
        "description": """Delete a specified favorited keyword from my Amazon platform keyword library. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to be deleted.",
                    "type": "string"
                },
                "dict": {
                    "description": "Favorite folder name. Optional; if specified, deletes the keyword under the given folder; otherwise deletes from the default folder.",
                    "type": "string",
                    "default": ""
                },
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "favorite_keyword",
        "description": """Add a keyword favorite into my Amazon platform keyword library. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to be added to favorites.",
                    "type": "string"
                },
                "dict": {
                    "description": "Favorite folder name. Optional; if specified, the keyword is added to the given folder; otherwise it is added to the default folder.",
                    "type": "string",
                    "default": ""
                },
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "get_favorite_keyword",
        "description": """Query the keywords in my Amazon platform keyword library. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dict": {
                    "description": "Favorite folder name. Optional; if specified, queries keywords under the given folder; pass `all` to query all keywords.",
                    "type": "string",
                    "default": ""
                },
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 50 records.",
                    "type": "integer",
                    "default": 1
                }
            }
        },
    },
    {
        "name": "get_favorite_keyword_dict",
        "description": """Query the favorite folder list of my Amazon platform keyword library. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 100 records.",
                    "type": "integer",
                    "default": 1
                }
            }
        },
    },
    {
        "name": "get_time",
        "description": """Get the current server time.""",
        "inputSchema": {
            "type": "object",
            "properties": {}
        },
    },
    {
        "name": "keyword_detail",
        "description": """Query the detail of a trending keyword on the Amazon platform.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to query.",
                    "type": "string"
                },
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "keyword_extends",
        "description": """Query the extended keywords of a trending keyword on the Amazon platform; useful for sellers to find related keywords, discover long-tail terms, or mine personalized demand.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to query.",
                    "type": "string"
                },
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "keyword_list",
        "description": """Query the real-time trending keyword list on the Amazon platform, sorted by weekly search volume. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "rank_min": {
                    "description": "Optional: filter keywords whose weekly search-volume rank is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "rank_max": {
                    "description": "Optional: filter keywords whose weekly search-volume rank is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "search_volume_min": {
                    "description": "Optional: filter keywords whose monthly search volume is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "search_volume_max": {
                    "description": "Optional: filter keywords whose monthly search volume is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                }
            }
        },
    },
    {
        "name": "keyword_list_from_history",
        "description": """Query the historical-date trending keyword list on the Amazon platform, sorted by weekly search volume. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "date": {
                    "description": "The queried date, in yyyy-MM-dd format; the earliest supported date is 2025-03-04.",
                    "type": "string"
                },
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "rank_min": {
                    "description": "Optional: filter keywords whose weekly search-volume rank is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "rank_max": {
                    "description": "Optional: filter keywords whose weekly search-volume rank is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "search_volume_min": {
                    "description": "Optional: filter keywords whose monthly search volume is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "search_volume_max": {
                    "description": "Optional: filter keywords whose monthly search volume is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                }
            },
            "required": [
                "date"
            ]
        },
    },
    {
        "name": "keyword_search_results",
        "description": """Query the organic-position product list of a trending keyword's search results on the Amazon platform.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to query.",
                    "type": "string"
                },
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "position_type": {
                    "description": "Exposure position type. 0: all, 1: organic only (default), 2: ads only.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "keyword_trend",
        "description": """Query the historical trend of a trending keyword on the Amazon platform, supporting search volume, search rank, and CPC price trends.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to query.",
                    "type": "string"
                },
                "keyword_support_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "potential_product",
        "description": """(隐赚指数选品) Search for potential products on the Amazon platform. """,
        "inputSchema": {
            "type": "object",
            "properties": {
                "search_name": {
                    "description": "Optional: search related products by this name.",
                    "type": "string",
                    "default": ""
                },
                "price_min": {
                    "description": "Optional: filter products with selling price greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "price_max": {
                    "description": "Optional: filter products with selling price less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "month_sales_volume_min": {
                    "description": "Optional: filter products with monthly sales volume greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "month_sales_volume_max": {
                    "description": "Optional: filter products with monthly sales volume less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "delivery_type": {
                    "description": "Optional: filter products by fulfillment method. Allowed values: `Both` (default, no filter), `FBM` (seller-fulfilled), `FBA` (any product using Amazon FBA, including seller-shipped and third-party like 1688), `AmzFBA` (third-party seller using Amazon FBA, e.g. 1688).",
                    "type": "string",
                    "enum": [
                        "Both",
                        "FBM",
                        "FBA",
                        "AmzFBA"
                    ],
                    "default": "Both"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "amz_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE"
                    ],
                    "default": "Unknow"
                }
            }
        },
    },
    {
        "name": "product_customers_say",
        "description": """Query the Amazon "Customers Say" content summarized from the product's user reviews. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asin": {
                    "description": "The product ASIN to query.",
                    "type": "string"
                },
                "site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "asin"
            ]
        },
    },
    {
        "name": "product_detail",
        "description": """Query the detailed data of a product on the Amazon platform.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asin": {
                    "description": "Product ASIN, single-ASIN query only.",
                    "type": "string"
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "asin"
            ]
        },
    },
    {
        "name": "product_ranking_trend_by_keyword",
        "description": """Exposure ranking trend of a product under a given keyword on the Amazon platform, sorted by exposure time in descending order. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asin": {
                    "description": "Product ASIN.",
                    "type": "string"
                },
                "keyword": {
                    "description": "The keyword.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "asin",
                "keyword"
            ]
        },
    },
    {
        "name": "product_report",
        "description": """Analysis report for a single product on the Amazon platform. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asin": {
                    "description": "Product ASIN.",
                    "type": "string"
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "asin"
            ]
        },
    },
    {
        "name": "product_reviews",
        "description": """Query user reviews of a product on the Amazon platform in the last year; returns at most 100 reviews.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asin": {
                    "description": "Product ASIN.",
                    "type": "string"
                },
                "review_type": {
                    "description": "Review sentiment to query. Defaults to Both.",
                    "type": "string",
                    "enum": [
                        "Both",
                        "Positive",
                        "Negative"
                    ],
                    "default": "Both"
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "asin"
            ]
        },
    },
    {
        "name": "product_search",
        "description": """Search the real-time product data on the Amazon platform, sorted by monthly sales volume in descending order by default.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "seasonal_popular_product": {
                    "description": "Optional: filter products that are in peak season in the specified month. Defaults to Both.",
                    "type": "string",
                    "enum": [
                        "Both",
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December"
                    ],
                    "default": "Both"
                },
                "brand": {
                    "description": "Optional: filter products of the specified brand.",
                    "type": "string",
                    "default": ""
                },
                "seller_name": {
                    "description": "Optional: filter products of the specified seller.",
                    "type": "string",
                    "default": ""
                },
                "search_name": {
                    "description": "Optional: search related products by this name.",
                    "type": "string",
                    "default": ""
                },
                "property_name": {
                    "description": "Optional: filter products whose title or attributes contain the specified property.",
                    "type": "string",
                    "default": ""
                },
                "price_min": {
                    "description": "Optional: filter products with selling price greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "price_max": {
                    "description": "Optional: filter products with selling price less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "month_sales_volume_min": {
                    "description": "Optional: filter products with monthly sales volume greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "month_sales_volume_max": {
                    "description": "Optional: filter products with monthly sales volume less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "ratings_min": {
                    "description": "Optional: filter products with star rating greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "ratings_max": {
                    "description": "Optional: filter products with star rating less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "ratings_count_min": {
                    "description": "Optional: filter products with review count greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "ratings_count_max": {
                    "description": "Optional: filter products with review count less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "subcategory_sales_volume_rank_min": {
                    "description": "Optional: filter products whose sales volume rank in the subcategory is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "subcategory_sales_volume_rank_max": {
                    "description": "Optional: filter products whose sales volume rank in the subcategory is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "delivery_type": {
                    "description": "Optional: filter products by fulfillment method. Allowed values: `Both` (default, no filter), `FBM` (seller-fulfilled), `FBA` (any product using Amazon FBA, including seller-shipped and third-party like 1688), `AmzFBA` (third-party seller using Amazon FBA, e.g. 1688).",
                    "type": "string",
                    "enum": [
                        "Both",
                        "FBM",
                        "FBA",
                        "AmzFBA"
                    ],
                    "default": "Both"
                },
                "variation_count_min": {
                    "description": "Optional: filter products whose variation (child ASIN) count is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "variation_count_max": {
                    "description": "Optional: filter products whose variation (child ASIN) count is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "sortby_potential_index": {
                    "description": "Optional: if true, sort by the product's potential index from high to low.",
                    "type": "boolean",
                    "default": False
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            }
        },
    },
    {
        "name": "product_search_from_history",
        "description": """Search historical product data on the Amazon platform to view top-selling products in a past period. Sorted by monthly sales volume in descending order by default. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "search_time": {
                    "description": "The period to search, in yyyy-MM format (year-month).",
                    "type": "string"
                },
                "search_name": {
                    "description": "Optional: search related products by this name.",
                    "type": "string",
                    "default": ""
                },
                "price_min": {
                    "description": "Optional: filter products with selling price greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "price_max": {
                    "description": "Optional: filter products with selling price less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "month_sales_volume_min": {
                    "description": "Optional: filter products with monthly sales volume greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "month_sales_volume_max": {
                    "description": "Optional: filter products with monthly sales volume less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "ratings_min": {
                    "description": "Optional: filter products with star rating greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "ratings_max": {
                    "description": "Optional: filter products with star rating less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "ratings_count_min": {
                    "description": "Optional: filter products with review count greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "ratings_count_max": {
                    "description": "Optional: filter products with review count less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "delivery_type": {
                    "description": "Optional: filter products by fulfillment method. Allowed values: `Both` (default, no filter), `FBM` (seller-fulfilled), `FBA` (any product using Amazon FBA, including seller-shipped and third-party like 1688), `AmzFBA` (third-party seller using Amazon FBA, e.g. 1688).",
                    "type": "string",
                    "enum": [
                        "Both",
                        "FBM",
                        "FBA",
                        "AmzFBA"
                    ],
                    "default": "Both"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "amz_site": {
                    "description": "Amazon marketplace site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "search_time"
            ]
        },
    },
    {
        "name": "product_traffic_terms",
        "description": """Reverse-lookup keywords for a product on the Amazon platform; returns the keywords where the product has appeared in the first 3 pages recently, sorted by latest exposure time in descending order.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asin": {
                    "description": "Product ASIN.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "asin"
            ]
        },
    },
    {
        "name": "product_trend",
        "description": """Query the historical trend of a product on the Amazon platform, supporting monthly sales volume/amount, price, and top-category rank trends.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asin": {
                    "description": "Product ASIN.",
                    "type": "string"
                },
                "product_trend_type": {
                    "description": "Product trend type to query. Defaults to SalesVolume.",
                    "type": "string",
                    "enum": [
                        "SalesVolume",
                        "SalesAmount",
                        "Price",
                        "Rank"
                    ],
                    "default": "SalesVolume"
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "asin"
            ]
        },
    },
    {
        "name": "product_variations",
        "description": """Query the variation (child ASIN) details of a product on the Amazon platform.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asin": {
                    "description": "Product ASIN, single-ASIN query only.",
                    "type": "string"
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "asin"
            ]
        },
    },
    {
        "name": "search_categories_broadly",
        "description": """Broadly search sub-category markets that match multi-dimensional constraints, for multi-dimensional product selection. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "month_sales_volume_min": {
                    "description": "Optional: filter sub-category markets whose monthly sales volume is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "month_sales_volume_max": {
                    "description": "Optional: filter sub-category markets whose monthly sales volume is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "ratings_min": {
                    "description": "Optional: filter sub-category markets whose star rating is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "ratings_max": {
                    "description": "Optional: filter sub-category markets whose star rating is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "ratings_count_min": {
                    "description": "Optional: filter sub-category markets whose review count is greater than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "ratings_count_max": {
                    "description": "Optional: filter sub-category markets whose review count is less than or equal to this value.",
                    "type": "integer",
                    "default": -9999
                },
                "price_min": {
                    "description": "Optional: filter sub-category markets whose average selling price (local currency) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "price_max": {
                    "description": "Optional: filter sub-category markets whose average selling price (local currency) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "seasonal_popular_product": {
                    "description": "Optional: filter sub-categories whose peak season is the given month. Defaults to Both.",
                    "type": "string",
                    "enum": [
                        "Both",
                        "January",
                        "February",
                        "March",
                        "April",
                        "May",
                        "June",
                        "July",
                        "August",
                        "September",
                        "October",
                        "November",
                        "December"
                    ],
                    "default": "Both"
                },
                "top3_product_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-3 products sales-volume share of top-100 (sales-monopoly index) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "top3_product_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-3 products sales-volume share of top-100 (sales-monopoly index) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "amazon_owned_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose Amazon-owned products sales-volume share within top-100 (seller-monopoly index) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "amazon_owned_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose Amazon-owned products sales-volume share within top-100 (seller-monopoly index) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "top100_top400_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-100 products sales-volume share within top-400 (lower share = longer-tail) is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "top100_top400_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose top-100 products sales-volume share within top-400 (lower share = longer-tail) is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "newproduct_sales_share_min": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose new-product sales-volume share (products listed within 3 months) within top-100 is greater than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "newproduct_sales_share_max": {
                    "description": "Optional: use 0-1 to indicate percentage (e.g. 10% = 0.1). Filter sub-category markets whose new-product sales-volume share (products listed within 3 months) within top-100 is less than or equal to this value.",
                    "type": "number",
                    "default": -9999
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            }
        },
    },
    {
        "name": "shopee_category_request",
        "description": """Query Best Seller products under a Shopee category. Optional queryDate for historical review (only sub-categories supported). (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "description": "The category ID to look up.",
                    "type": "string"
                },
                "query_date": {
                    "description": "Optional, format yyyy-MM-dd. If specified, used to query historical data for the natural week containing the date (only sub-categories support historical review; for non-sub-categories this parameter is invalid).",
                    "type": "string",
                    "default": None
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "node_id"
            ]
        },
    },
    {
        "name": "shopee_category_search_from_name",
        "description": """Search related category markets on Shopee by name. Used to obtain category node IDs and category names. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "description": "The category name to search for.",
                    "type": "string"
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "name"
            ]
        },
    },
    {
        "name": "shopee_category_trend",
        "description": """Used to query the historical trend of a Shopee category market. Each call returns one trend dimension; select the trendIndex enum accordingly. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "description": "The category node ID to query.",
                    "type": "string",
                    "default": None
                },
                "trend_index": {
                    "description": "The historical trend type to query.",
                    "type": "string",
                    "enum": [
                        "MonthlySalesVolume",
                        "MonthlySalesAmount",
                        "AveragePrice",
                        "AverageReviewCount",
                        "AverageStarRating",
                        "SellerCount",
                        "AverageVariantCount",
                        "BrandCount",
                        "FlagshipStoreCount",
                        "FlagshipStoreRatio",
                        "FlagshipStoreMonthlySales",
                        "FlagshipStoreMonthlySalesRatio",
                        "PreferredStoreCount",
                        "PreferredStoreRatio",
                        "PreferredStoreMonthlySales",
                        "PreferredStoreMonthlySalesRatio",
                        "OrdinaryStoreCount",
                        "OrdinaryStoreRatio",
                        "OrdinaryStoreMonthlySales",
                        "OrdinaryStoreMonthlySalesRatio",
                        "Listed1MonthProductCount",
                        "Listed1MonthProductCountRatio",
                        "Listed1MonthSalesVolume",
                        "Listed1MonthSalesVolumeRatio",
                        "Listed1MonthSalesAmount",
                        "Listed1MonthSalesAmountRatio",
                        "Listed1MonthAvgStarRating",
                        "Listed1MonthAvgReviewCount",
                        "Listed1MonthAvgPrice",
                        "Listed3MonthProductCount",
                        "Listed3MonthProductCountRatio",
                        "Listed3MonthSalesVolume",
                        "Listed3MonthSalesVolumeRatio",
                        "Listed3MonthSalesAmount",
                        "Listed3MonthSalesAmountRatio",
                        "Listed3MonthAvgStarRating",
                        "Listed3MonthAvgReviewCount",
                        "Listed3MonthAvgPrice",
                        "Listed6MonthProductCount",
                        "Listed6MonthProductCountRatio",
                        "Listed6MonthSalesVolume",
                        "Listed6MonthSalesVolumeRatio",
                        "Listed6MonthSalesAmount",
                        "Listed6MonthSalesAmountRatio",
                        "Listed6MonthAvgStarRating",
                        "Listed6MonthAvgReviewCount",
                        "Listed6MonthAvgPrice",
                        "Listed12MonthProductCount",
                        "Listed12MonthProductCountRatio",
                        "Listed12MonthSalesVolume",
                        "Listed12MonthSalesVolumeRatio",
                        "Listed12MonthSalesAmount",
                        "Listed12MonthSalesAmountRatio",
                        "Listed12MonthAvgStarRating",
                        "Listed12MonthAvgReviewCount",
                        "Listed12MonthAvgPrice",
                        "Listed24MonthProductCount",
                        "Listed24MonthProductCountRatio",
                        "Listed24MonthSalesVolume",
                        "Listed24MonthSalesVolumeRatio",
                        "Listed24MonthSalesAmount",
                        "Listed24MonthSalesAmountRatio",
                        "Listed24MonthAvgStarRating",
                        "Listed24MonthAvgReviewCount",
                        "Listed24MonthAvgPrice",
                        "Top3ProductSalesVolumeRatio",
                        "Top3ProductSalesAmountRatio",
                        "Top3SellerSalesVolumeRatio",
                        "Top3SellerSalesAmountRatio",
                        "Top5ProductSalesVolumeRatio",
                        "Top5ProductSalesAmountRatio",
                        "Top5SellerSalesVolumeRatio",
                        "Top5SellerSalesAmountRatio",
                        "Top10ProductSalesVolumeRatio",
                        "Top10ProductSalesAmountRatio",
                        "Top10SellerSalesVolumeRatio",
                        "Top10SellerSalesAmountRatio"
                    ],
                    "default": "MonthlySalesVolume"
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            }
        },
    },
    {
        "name": "shopee_change_favorite_keyword",
        "description": """Move a favorited keyword on the Shopee platform to a specified dict (auto-created if it does not exist). (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to move.",
                    "type": "string"
                },
                "to_dict": {
                    "description": "The destination dict name.",
                    "type": "string"
                },
                "from_dict": {
                    "description": "Optional. If specified, only move the keyword from this source dict.",
                    "type": "string",
                    "default": ""
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "keyword",
                "to_dict"
            ]
        },
    },
    {
        "name": "shopee_del_favorite_keyword",
        "description": """Delete a specified keyword from my Shopee keyword favorites. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to delete.",
                    "type": "string"
                },
                "dict": {
                    "description": "Optional. If specified, delete the keyword from this dict only.",
                    "type": "string",
                    "default": ""
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "shopee_favorite_keyword",
        "description": """Add a keyword to my Shopee keyword favorites. If the specified dict does not exist, it is created automatically. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to favorite.",
                    "type": "string"
                },
                "dict": {
                    "description": "Optional. If specified, add the keyword to this favorites dict (auto-created if not exists).",
                    "type": "string",
                    "default": ""
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "shopee_get_favorite_keyword",
        "description": """Query the favorited keywords in my Shopee keyword favorites. Specify `dict=all` to query every keyword across all dicts. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dict": {
                    "description": "Optional. If specified, queries keywords under the given folder; pass `all` to query all keywords.",
                    "type": "string",
                    "default": ""
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 100 records.",
                    "type": "integer",
                    "default": 1
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            }
        },
    },
    {
        "name": "shopee_get_favorite_keyword_dict",
        "description": """Query the list of dicts (folders) in my Shopee keyword favorites. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 100 records.",
                    "type": "integer",
                    "default": 1
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            }
        },
    },
    {
        "name": "shopee_keyword_relation_results",
        "description": """Search Shopee related products by keyword, returning up to 20 products per page. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to query (e.g. summer dress).",
                    "type": "string",
                    "default": None
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            }
        },
    },
    {
        "name": "shopee_keyword_search",
        "description": """The list of trending keywords on Shopee, sorted by monthly search volume by default. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "Optional. The keyword to query (e.g. summer dress). When provided, the search is keyword-specific; otherwise it returns the trending list.",
                    "type": "string",
                    "default": None
                },
                "rank_min": {
                    "description": "Optional. Filter by minimum monthly rank.",
                    "type": "integer",
                    "default": 0
                },
                "rank_max": {
                    "description": "Optional. Filter by maximum monthly rank.",
                    "type": "integer",
                    "default": 0
                },
                "search_volume_min": {
                    "description": "Optional. Filter by minimum monthly search volume.",
                    "type": "integer",
                    "default": 0
                },
                "search_volume_max": {
                    "description": "Optional. Filter by maximum monthly search volume.",
                    "type": "integer",
                    "default": 0
                },
                "page": {
                    "description": "Optional. Page index, defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            }
        },
    },
    {
        "name": "shopee_product_request",
        "description": """Query detailed information of a Shopee product. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "The product ID to query.",
                    "type": "string"
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "shopee_product_search",
        "description": """Search product data on the Shopee platform with multi-dimensional filters, sorted by monthly sales volume descending. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "Optional. If specified: query similar products based on productId (note: it does not query only this productId; to fetch that exact product, call the ProductRequest tool).",
                    "type": "string",
                    "default": None
                },
                "node_id": {
                    "description": "Optional. If specified: query within a category (not limited to sub-categories).",
                    "type": "string",
                    "default": None
                },
                "price_range_min": {
                    "description": "Optional. If specified: limit minimum selling price (val >= setting value).",
                    "type": "number",
                    "default": 0
                },
                "price_range_max": {
                    "description": "Optional. If specified: limit maximum selling price (val <= setting value).",
                    "type": "number",
                    "default": 0
                },
                "month_sale_volume_range_min": {
                    "description": "Optional. If specified: limit minimum monthly sales volume (val >= setting value).",
                    "type": "integer",
                    "default": 0
                },
                "month_sale_volume_range_max": {
                    "description": "Optional. If specified: limit maximum monthly sales volume (val <= setting value).",
                    "type": "integer",
                    "default": 0
                },
                "online_date_range_min": {
                    "description": "Optional. If specified: limit listing start date (yyyy-MM-dd).",
                    "type": "string",
                    "default": None
                },
                "online_date_range_max": {
                    "description": "Optional. If specified: limit listing end date (yyyy-MM-dd).",
                    "type": "string",
                    "default": None
                },
                "star_range_min": {
                    "description": "Optional. If specified: limit minimum star rating.",
                    "type": "number",
                    "default": 0
                },
                "star_range_max": {
                    "description": "Optional. If specified: limit maximum star rating.",
                    "type": "number",
                    "default": 0
                },
                "comment_count_range_min": {
                    "description": "Optional. If specified: limit minimum comment count.",
                    "type": "integer",
                    "default": 0
                },
                "comment_count_range_max": {
                    "description": "Optional. If specified: limit maximum comment count.",
                    "type": "integer",
                    "default": 0
                },
                "variation_count_range_min": {
                    "description": "Optional. If specified: limit minimum variation count.",
                    "type": "integer",
                    "default": 0
                },
                "variation_count_range_max": {
                    "description": "Optional. If specified: limit maximum variation count.",
                    "type": "integer",
                    "default": 0
                },
                "shop_location": {
                    "description": "Optional. Shop location type: 1 = local store, 2 = cross-border store.",
                    "type": "integer",
                    "default": 0
                },
                "shop_type": {
                    "description": "Optional. Shop type: 1 = ordinary store, 2 = preferred store, 3 = flagship store.",
                    "type": "integer",
                    "default": 0
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                },
                "page": {
                    "description": "Page query, max 20 products per page. Defaults to 1 (pages start from 1, not 0).",
                    "type": "integer",
                    "default": 1
                }
            }
        },
    },
    {
        "name": "shopee_product_search_from_name",
        "description": """Search related products on Shopee by name, returning up to 20 products each call. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "description": "The product name keyword to search for.",
                    "type": "string"
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                },
                "page": {
                    "description": "Page index, defaults to page 1.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "name"
            ]
        },
    },
    {
        "name": "shopee_product_trend",
        "description": """Supports historical trends across five dimensions: star rating, comment count, price, cumulative sales, and last-30-day sales. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "The product ID to query.",
                    "type": "string"
                },
                "query_start": {
                    "description": "Optional. Query start time (yyyy-MM-dd). Default last 1 year. When span > 1 year, each call consumes 10 credits.",
                    "type": "string",
                    "default": None
                },
                "query_end": {
                    "description": "Optional. Query end time (yyyy-MM-dd). Defaults to the current time.",
                    "type": "string",
                    "default": None
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "shopee_shop_request",
        "description": """Query Shopee seller (shop) details. Returns basic information and a Top500 snapshot of the shop's products. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "shop_id": {
                    "description": "The shop ID to query.",
                    "type": "string"
                },
                "site": {
                    "description": "Shopee site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "VN",
                        "ID",
                        "SG",
                        "TH",
                        "MY",
                        "TW",
                        "PH",
                        "BR"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "shop_id"
            ]
        },
    },
    {
        "name": "similar_product_feature",
        "description": """Query the product features of an Amazon sub-category.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_name": {
                    "description": "The sub-category name to query (e.g. power bank, air fryer).",
                    "type": "string"
                },
                "amz_site": {
                    "description": "Amazon marketplace site. ",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "GB",
                        "DE",
                        "FR",
                        "IN",
                        "CA",
                        "JP",
                        "ES",
                        "IT",
                        "MX",
                        "AE",
                        "AU",
                        "BR",
                        "SA"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "product_name"
            ]
        },
    },
    {
        "name": "temu_category_request",
        "description": """Query Best Seller products under a Temu category market, which can be used for category data analysis. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "description": "The category ID to query.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "site": {
                    "description": "Temu site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "US",
                        "EU"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "node_id"
            ]
        },
    },
    {
        "name": "temu_category_search",
        "description": """Search category data on the Temu e-commerce platform with multi-dimensional filtering. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "description": "Optional. If specified: limit the search scope to the specified category and its sub-categories (the specified category nodeId is not limited to leaf categories).",
                    "type": "string",
                    "default": None
                },
                "sale_count_min": {
                    "description": "Optional. If specified: filter to category markets whose Top-100 products have monthly sales count greater than or equal to this value; larger value indicates higher product sales monopoly.",
                    "type": "integer",
                    "default": 0
                },
                "sale_count_max": {
                    "description": "Optional. If specified: filter to category markets whose Top-100 products have monthly sales count less than or equal to this value; larger value indicates higher product sales monopoly.",
                    "type": "integer",
                    "default": 0
                },
                "sale_count_share_ratio_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 share of Top-600 monthly sales is greater than or equal to this value (in %). Higher means more concentrated in Top-100; lower means a long-tail category.",
                    "type": "number",
                    "default": 0
                },
                "sale_count_share_ratio_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 share of Top-600 monthly sales is less than or equal to this value (in %). Higher means more concentrated in Top-100; lower means a long-tail category.",
                    "type": "number",
                    "default": 0
                },
                "sale_count_mom_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 month-over-month sales growth is greater than or equal to this value (in %). Larger means faster growth.",
                    "type": "number",
                    "default": 0
                },
                "sale_count_mom_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 month-over-month sales growth is less than or equal to this value (in %). Larger means faster growth.",
                    "type": "number",
                    "default": 0
                },
                "sale_amount_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 monthly sales amount is greater than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "sale_amount_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 monthly sales amount is less than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "price_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 product selling price is greater than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "price_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 product selling price is less than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "avg_review_count_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 average review count is greater than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "avg_review_count_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 average review count is less than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "avg_star_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 average star rating is greater than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "avg_star_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 average star rating is less than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "seller_count_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 unique seller count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "seller_count_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 unique seller count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "brand_count_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 unique brand count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "brand_count_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 unique brand count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "top10_product_sale_count_share_ratio_min": {
                    "description": "Optional. If specified: filter to categories whose Top-10 share of Top-100 sales count is greater than or equal to this value (in %). Higher means stronger product monopoly.",
                    "type": "number",
                    "default": 0
                },
                "top10_product_sale_count_share_ratio_max": {
                    "description": "Optional. If specified: filter to categories whose Top-10 share of Top-100 sales count is less than or equal to this value (in %). Higher means stronger product monopoly.",
                    "type": "number",
                    "default": 0
                },
                "top10_seller_sale_count_share_ratio_min": {
                    "description": "Optional. If specified: in the Top-100 products, filter to categories whose Top-10 sellers' sales count share is greater than or equal to this value (in %). Higher means stronger seller monopoly.",
                    "type": "number",
                    "default": 0
                },
                "top10_seller_sale_count_share_ratio_max": {
                    "description": "Optional. If specified: in the Top-100 products, filter to categories whose Top-10 sellers' sales count share is less than or equal to this value (in %). Higher means stronger seller monopoly.",
                    "type": "number",
                    "default": 0
                },
                "semi_managed_shop_count_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 semi-managed shop count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "semi_managed_shop_count_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 semi-managed shop count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "semi_managed_shop_sale_count_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 semi-managed shop monthly sales count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "semi_managed_shop_sale_count_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 semi-managed shop monthly sales count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "semi_managed_shop_cumulative_sale_count_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 semi-managed shop cumulative sales count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "semi_managed_shop_cumulative_sale_count_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 semi-managed shop cumulative sales count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "star_seller_count_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 star seller count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "star_seller_count_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 star seller count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "star_seller_monthly_sale_count_min": {
                    "description": "Optional. If specified: filter to categories whose Top-100 star seller monthly sales count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "star_seller_monthly_sale_count_max": {
                    "description": "Optional. If specified: filter to categories whose Top-100 star seller monthly sales count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "new_product_count_min": {
                    "description": "Optional. If specified: filter to categories whose Top-600 new-product (listed within 30 days) count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "new_product_count_max": {
                    "description": "Optional. If specified: filter to categories whose Top-600 new-product (listed within 30 days) count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "new_product_sale_count_min": {
                    "description": "Optional. If specified: filter to categories whose Top-600 new-product (within 30 days) monthly sales count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "new_product_sale_count_max": {
                    "description": "Optional. If specified: filter to categories whose Top-600 new-product (within 30 days) monthly sales count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "new_product_sale_count_share_ratio_min": {
                    "description": "Optional. If specified: filter to categories whose Top-600 new-product (within 30 days) monthly sales count share is greater than or equal to this value (in %).",
                    "type": "number",
                    "default": 0
                },
                "new_product_sale_count_share_ratio_max": {
                    "description": "Optional. If specified: filter to categories whose Top-600 new-product (within 30 days) monthly sales count share is less than or equal to this value (in %).",
                    "type": "number",
                    "default": 0
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "site": {
                    "description": "Temu site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "US",
                        "EU"
                    ],
                    "default": "UnKonw"
                }
            }
        },
    },
    {
        "name": "temu_category_search_from_name",
        "description": """Search Temu platform category markets by name. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "description": "The category name to search for.",
                    "type": "string"
                },
                "site": {
                    "description": "Temu site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "US",
                        "EU"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "name"
            ]
        },
    },
    {
        "name": "temu_product_request",
        "description": """Query Temu product details. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "The product ID.",
                    "type": "string"
                },
                "site": {
                    "description": "Temu site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "US",
                        "EU"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "temu_product_search",
        "description": """Search product data on the Temu e-commerce platform with multi-dimensional filtering, sorted by monthly sales count descending. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "Optional. If specified: query similar products based on the given ProductId.",
                    "type": "string",
                    "default": None
                },
                "node_id": {
                    "description": "Optional. If specified: limit the search scope to the specified category and its sub-categories (the specified category nodeId is not limited to leaf categories).",
                    "type": "string",
                    "default": None
                },
                "brand": {
                    "description": "Optional. If specified: query hot-selling products of the specified brand.",
                    "type": "string",
                    "default": None
                },
                "seller_name": {
                    "description": "Optional. If specified: query hot-selling products of the specified seller.",
                    "type": "string",
                    "default": None
                },
                "cumulative_sale_count_min": {
                    "description": "Optional. If specified: filter products whose cumulative sales count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "cumulative_sale_count_max": {
                    "description": "Optional. If specified: filter products whose cumulative sales count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "sale_count_min": {
                    "description": "Optional. If specified: filter products whose monthly sales count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "sale_count_max": {
                    "description": "Optional. If specified: filter products whose monthly sales count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "sale_amount_min": {
                    "description": "Optional. If specified: filter products whose monthly sales amount is greater than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "sale_amount_max": {
                    "description": "Optional. If specified: filter products whose monthly sales amount is less than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "sale_count_mom_min": {
                    "description": "Optional. If specified: filter products whose month-over-month growth is greater than or equal to this value (in %).",
                    "type": "number",
                    "default": 0
                },
                "sale_count_mom_max": {
                    "description": "Optional. If specified: filter products whose month-over-month growth is less than or equal to this value (in %).",
                    "type": "number",
                    "default": 0
                },
                "price_min": {
                    "description": "Optional. If specified: filter products whose selling price is greater than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "price_max": {
                    "description": "Optional. If specified: filter products whose selling price is less than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "manage_type": {
                    "description": "Optional. If specified: filter products by management type.",
                    "type": "integer",
                    "default": 0
                },
                "comment_count_min": {
                    "description": "Optional. If specified: filter products whose comment count is greater than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "comment_count_max": {
                    "description": "Optional. If specified: filter products whose comment count is less than or equal to this value.",
                    "type": "integer",
                    "default": 0
                },
                "star_min": {
                    "description": "Optional. If specified: filter products whose star rating is greater than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "star_max": {
                    "description": "Optional. If specified: filter products whose star rating is less than or equal to this value.",
                    "type": "number",
                    "default": 0
                },
                "sale_time_min": {
                    "description": "Optional. If specified: filter products by listing start date (yyyy-MM-dd).",
                    "type": "string",
                    "default": None
                },
                "sale_time_max": {
                    "description": "Optional. If specified: filter products by listing end date (yyyy-MM-dd).",
                    "type": "string",
                    "default": None
                },
                "site": {
                    "description": "Temu site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "US",
                        "EU"
                    ],
                    "default": "UnKonw"
                },
                "page": {
                    "description": "Pagination, at most 20 products per page. Defaults to 1 (page index starts from 1, not 0).",
                    "type": "integer",
                    "default": 1
                }
            }
        },
    },
    {
        "name": "temu_product_search_from_name",
        "description": """Search Temu products by name, returning 20 products per call. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "description": "The product name to search for.",
                    "type": "string"
                },
                "site": {
                    "description": "Temu site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "US",
                        "EU"
                    ],
                    "default": "UnKonw"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "name"
            ]
        },
    },
    {
        "name": "temu_product_trend",
        "description": """Query product historical trend data, returning monthly trends for sales count, cumulative sales count, sales amount, average price, comment count, and star rating. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "The product ID to query.",
                    "type": "string"
                },
                "query_start": {
                    "description": "Optional. Start date of the trend query range, format yyyy-MM-dd. Default: past 1 year. When querying beyond 1 year, each call costs 10 credits.",
                    "type": "string",
                    "default": None
                },
                "query_end": {
                    "description": "Optional. End date of the trend query range, format yyyy-MM-dd. Defaults to current time.",
                    "type": "string",
                    "default": None
                },
                "site": {
                    "description": "Temu site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "US",
                        "EU"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "temu_shop_request",
        "description": """Query Temu seller (shop) details. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "shop_id": {
                    "description": "The shop ID to query.",
                    "type": "string"
                },
                "site": {
                    "description": "Temu site.",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "US",
                        "EU"
                    ],
                    "default": "UnKonw"
                }
            },
            "required": [
                "shop_id"
            ]
        },
    },
    {
        "name": "tiktok_author",
        "description": """Query TikTok platform author details by author ID, US site only. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "author_id": {
                    "description": "The author ID to query (in practice accepts the author handle such as `xmw_us`).",
                    "type": "string"
                }
            },
            "required": [
                "author_id"
            ]
        },
    },
    {
        "name": "tiktok_category_name_search",
        "description": """Search related TikTok categories by name, returns category name and nodeid. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "search_name": {
                    "description": "The product name to search for.",
                    "type": "string"
                },
                "site": {
                    "description": "TikTok site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "MY",
                        "PH",
                        "VN",
                        "TH",
                        "ID",
                        "GB",
                        "JP"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "search_name"
            ]
        },
    },
    {
        "name": "tiktok_category_report",
        "description": """Query the category data report for a given category on the TikTok e-commerce platform.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "description": "Category node_id, can be obtained via tiktok_category_name_search or tikto_category_search_from_name.",
                    "type": "string"
                },
                "site": {
                    "description": "TikTok site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "MY",
                        "PH",
                        "VN",
                        "TH",
                        "ID",
                        "GB",
                        "JP"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "node_id"
            ]
        },
    },
    {
        "name": "tiktok_category_search_from_name",
        "description": """Search related categories on the TikTok platform by name. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "description": "The name of the category to search for.",
                    "type": "string"
                },
                "site": {
                    "description": "TikTok site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "MY",
                        "PH",
                        "VN",
                        "TH",
                        "ID",
                        "GB",
                        "JP"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "name"
            ]
        },
    },
    {
        "name": "tiktok_product_detail",
        "description": """Query product details on the TikTok platform.""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "Product ID.",
                    "type": "string"
                },
                "site": {
                    "description": "TikTok site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "MY",
                        "PH",
                        "VN",
                        "TH",
                        "ID",
                        "GB",
                        "JP"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "tiktok_product_trend",
        "description": """Query TikTok platform product trend, returning multiple dimensions: sales, price, star rating, review count, new promo video count, new promo author count. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "Product ID.",
                    "type": "string"
                },
                "site": {
                    "description": "TikTok site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "MY",
                        "PH",
                        "VN",
                        "TH",
                        "ID",
                        "GB",
                        "JP"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "tiktok_product_video",
        "description": """Query promo videos of a TikTok product. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "Product ID.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "site": {
                    "description": "TikTok site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "MY",
                        "PH",
                        "VN",
                        "TH",
                        "ID",
                        "GB",
                        "JP"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "tiktok_product_video_author",
        "description": """Query promo authors of a product on the TikTok platform. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "Product ID.",
                    "type": "string"
                },
                "site": {
                    "description": "TikTok site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "MY",
                        "PH",
                        "VN",
                        "TH",
                        "ID",
                        "GB",
                        "JP"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "tiktok_similar_product",
        "description": """Query similar products of a product on the TikTok platform; can be used to analyze the sales situation of this type of product. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_name": {
                    "description": "The product name to query.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                },
                "site": {
                    "description": "TikTok site.",
                    "type": "string",
                    "enum": [
                        "Unknow",
                        "US",
                        "MY",
                        "PH",
                        "VN",
                        "TH",
                        "ID",
                        "GB",
                        "JP"
                    ],
                    "default": "Unknow"
                }
            },
            "required": [
                "product_name"
            ]
        },
    },
    {
        "name": "walmart_category_report_by_node_id",
        "description": """Query the real-time Top 100 best-selling product data report for a specified category on the Walmart e-commerce platform. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "node_id": {
                    "description": "The leaf category nodeId to query this specific category data.",
                    "type": "string"
                }
            },
            "required": [
                "node_id"
            ]
        },
    },
    {
        "name": "walmart_change_favorite_keyword",
        "description": """Move a favorited keyword in my Walmart platform keyword library to a specified collection; if the collection does not exist, a new one will be created. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to move.",
                    "type": "string"
                },
                "to_dict": {
                    "description": "The destination collection name.",
                    "type": "string"
                },
                "from_dict": {
                    "description": "Optional. If specified, move the keyword from this source collection.",
                    "type": "string",
                    "default": ""
                }
            },
            "required": [
                "keyword",
                "to_dict"
            ]
        },
    },
    {
        "name": "walmart_del_favorite_keyword",
        "description": """Delete a specific favorited keyword from my Walmart platform keyword library. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to delete.",
                    "type": "string"
                },
                "dict": {
                    "description": "Optional. If specified, delete the keyword under the specified collection.",
                    "type": "string",
                    "default": ""
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "walmart_favorite_keyword",
        "description": """Add a keyword favorite in my Walmart platform keyword library. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to favorite.",
                    "type": "string"
                },
                "dict": {
                    "description": "Optional. If specified, add the keyword to the specified collection.",
                    "type": "string",
                    "default": ""
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "walmart_get_favorite_keyword",
        "description": """Query the keywords in my Walmart platform keyword library. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dict": {
                    "description": "Optional. If specified, query the keywords under the specified collection; to query all keywords, pass the value `all`.",
                    "type": "string",
                    "default": ""
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 100 records.",
                    "type": "integer",
                    "default": 1
                }
            }
        },
    },
    {
        "name": "walmart_get_favorite_keyword_dict",
        "description": """Query the collection list of my Walmart platform keyword library. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 100 records.",
                    "type": "integer",
                    "default": 1
                }
            }
        },
    },
    {
        "name": "walmart_keyword_detail",
        "description": """Query the details of a hot-search keyword on the Walmart e-commerce platform. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to query.",
                    "type": "string"
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "walmart_keyword_extends",
        "description": """Query the extension keywords of a hot-search keyword on the Walmart e-commerce platform; can be used by sellers to look up related keywords, discover long-tail keywords, or mine personalized needs. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to query.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "walmart_keyword_list",
        "description": """Query the real-time hot-search keyword list on the Walmart e-commerce platform, sorted by monthly search volume. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "rank_min": {
                    "description": "The start of the rank range (e.g. 1).",
                    "type": "integer"
                },
                "rank_max": {
                    "description": "The end of the rank range (e.g. 100).",
                    "type": "integer"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "rank_min",
                "rank_max"
            ]
        },
    },
    {
        "name": "walmart_keyword_search_from_name",
        "description": """Query a hot-search keyword on the Walmart e-commerce platform by name. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "description": "The keyword name to query.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "name"
            ]
        },
    },
    {
        "name": "walmart_keyword_search_results",
        "description": """Query the natural-position product list in the last 15 days' search results for a hot-search keyword on the Walmart e-commerce platform. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {
                    "description": "The keyword to query.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "keyword"
            ]
        },
    },
    {
        "name": "walmart_product_detail_by_product_id",
        "description": """Query the details of a product on the Walmart e-commerce platform. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "Product ID, single product ID query only.",
                    "type": "string"
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "walmart_product_traffic_terms",
        "description": """Reverse-lookup keywords for a product on the Walmart e-commerce platform, returns the keywords the product has been exposed under recently. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "The product ID to be queried.",
                    "type": "string"
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "walmart_product_trend_by_product_id",
        "description": """Query the historical trend data of a product on the Walmart e-commerce platform, supports multi-dimensional trend analysis such as monthly sales volume / sales amount / price / rank / reviews / star rating. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "Product ID, single product ID query only.",
                    "type": "string"
                },
                "trend_type": {
                    "description": "The trend type to query",
                    "type": "string",
                    "enum": [
                        "UnKonw",
                        "SalesVolume",
                        "SalesAmount",
                        "Price",
                        "Rank",
                        "Reviews",
                        "Star"
                    ],
                    "default": "UnKonw"
                },
                "begin_date": {
                    "description": "The start time for historical lookback (format: yyyy-MM-dd), defaults (when not passed, or when the parameter is invalid) to return data for the last 1 years.",
                    "type": "string",
                    "default": ""
                },
                "end_date": {
                    "description": "The end time for historical lookback (format: yyyy-MM-dd), defaults (when not passed, or when the parameter is invalid) to return data up to the current time.",
                    "type": "string",
                    "default": ""
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "walmart_product_variation_sales_by_product_id",
        "description": """Query the variation (child item) sales breakdown of a product on the Walmart e-commerce platform. (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {
                    "description": "Product ID, single product ID query only.",
                    "type": "string"
                },
                "begin_date": {
                    "description": "The query start date (format: yyyy-MM-dd), defaults (when not passed, or when the parameter is invalid) to return data for the last 30 days.",
                    "type": "string",
                    "default": ""
                },
                "end_date": {
                    "description": "The query end date (format: yyyy-MM-dd), defaults (when not passed, or when the parameter is invalid) to return data up to the current time.",
                    "type": "string",
                    "default": ""
                },
                "page": {
                    "description": "The page index of the query result. Defaults to page 1. Each page returns 20 records.",
                    "type": "integer",
                    "default": 1
                }
            },
            "required": [
                "product_id"
            ]
        },
    },
    {
        "name": "sorftime_raw_call",
        "description": """透传调用任意 Sorftime MCP 工具（用于访问未在 bridge 中单独注册 Schema 的工具）""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "要调用的 Sorftime 工具名称"},
                "arguments": {"type": "object", "description": "工具参数（JSON 对象）"}
            },
            "required": ["tool_name", "arguments"]
        },
    },
]


def build_tools() -> List[Tool]:
    core_tools = _load_core_tools()
    return [Tool(name=t["name"], description=t["description"], inputSchema=t["inputSchema"]) for t in core_tools]


async def call_sorftime(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Call Sorftime MCP endpoint via HTTP"""
    if not SORFTIME_MCP_KEY:
        raise RuntimeError(
            "Environment variable SORFTIME_MCP_KEY is not set. "
            "If this is your first time, run `python3 scripts/install.py` for one-click setup, "
            "or provide your Sorftime MCP Key directly to your AI agent. "
            "Get your Key at: https://open-intl.sorftime.com/mcp"
        )

    # Auto-correct parameter names: uses the same PARAM_ALIASES rules as scripts/utils/mcp_client.py.
    # The bridge is the single entry point for all calls (--one-shot / MCP server / raw_call),
    # so we validate here to avoid the “script path has correction, bridge path doesn't” bug.
    try:
        _parent = str(Path(__file__).resolve().parent)
        if _parent not in sys.path:
            sys.path.insert(0, _parent)
        from utils.mcp_client import _validate_and_normalize_params
        arguments = _validate_and_normalize_params(tool_name, dict(arguments))
    except ImportError:
        pass  # utils 不可用时降级为不校验，保持桥接可独立运行

    url = f"{SORFTIME_MCP_URL}?key={SORFTIME_MCP_KEY}"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }

    timeout = float(os.getenv("SORFTIME_HTTP_TIMEOUT", "30.0"))
    proxy = os.getenv("SORFTIME_PROXY")
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, proxy=proxy) as client:
        resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
        resp.raise_for_status()
        raw_text = resp.text

    # Sorftime 返回 SSE 格式：event: message\ndata: {...}\n\n
    # 尝试从 SSE 中提取 data 行
    data_json = None
    for line in raw_text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            data_json = line[len("data:"):].strip()
            break

    if not data_json:
        # 如果不是 SSE，尝试直接解析 JSON
        data_json = raw_text.strip()

    try:
        data = json.loads(data_json)
    except json.JSONDecodeError:
        return json.dumps({"error": True, "status": "parse_error", "message": raw_text.strip()[:500], "hint": "Server returned non-JSON response. Check parameter names and required fields."}, ensure_ascii=False)

    # 提取 text 内容
    if "result" in data and "content" in data["result"]:
        is_error = data["result"].get("isError", False)
        for item in data["result"]["content"]:
            if item.get("type") == "text":
                text = item.get("text", "")
                # 尝试解码 Unicode 转义
                try:
                    if "\\u" in text:
                        text = text.encode("utf-8").decode("unicode_escape")
                except Exception:
                    pass
                if is_error:
                    return json.dumps({"error": True, "status": "server_error", "message": text, "hint": "Check parameter names, required fields, and tool availability. Retry or contact Sorftime support."}, ensure_ascii=False)
                return text

    return json.dumps(data, ensure_ascii=False, indent=2)


async def run_server() -> None:
    server = Server("sorftime-seller-agent")

    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return build_tools()

    @server.call_tool()
    async def call_tool(name: str, arguments: Optional[Dict[str, Any]] = None) -> List[TextContent]:
        arguments = arguments or {}
        if name == "sorftime_raw_call":
            actual_name = arguments.pop("tool_name", "")
            actual_args = arguments.pop("arguments", {})
            result = await call_sorftime(actual_name, actual_args)
        else:
            result = await call_sorftime(name, arguments)
        return [TextContent(type="text", text=result)]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


async def run_one_shot(tool_name: str, args_json: str) -> None:
    arguments = json.loads(args_json) if args_json else {}
    try:
        if tool_name == "sorftime_raw_call":
            actual_name = arguments.pop("tool_name", "")
            actual_args = arguments.pop("arguments", {})
            result = await call_sorftime(actual_name, actual_args)
        else:
            result = await call_sorftime(tool_name, arguments)
    except RuntimeError as e:
        # 参数校验等本地错误：输出干净的一行报错而非 traceback
        print(f"[Parameter Error] {e}", file=sys.stderr)
        sys.exit(2)
    # Ensure output is always valid JSON for --one-shot callers
    if not result or not result.strip():
        print(json.dumps({"error": True, "message": "Server returned empty response", "hint": "The tool may require additional required parameters. Check the tool schema."}, ensure_ascii=False))
    else:
        try:
            json.loads(result)
            print(result)
        except (json.JSONDecodeError, TypeError):
            # Not JSON — but may be valid structured text (e.g. product_trend "2024年08月=347,..." or product_detail key：value format)
            text = str(result).strip()
            # Try parsing as comma-separated key=value pairs (product_trend format)
            if '=' in text and ('月=' in text or '年=' in text or ',' in text):
                try:
                    pairs = {}
                    for part in text.split(','):
                        part = part.strip()
                        if '=' in part:
                            k, v = part.split('=', 1)
                            k = k.strip(); v = v.strip()
                            try: pairs[k] = int(v)
                            except ValueError:
                                try: pairs[k] = float(v)
                                except ValueError: pairs[k] = v
                    if pairs:
                        print(json.dumps({"data": pairs}, ensure_ascii=False))
                        return
                except Exception:
                    pass
            # Try parsing as key：value newline format (product_detail format)
            if '：' in text:
                try:
                    from utils.mcp_client import _parse_kv_text
                    parsed = _parse_kv_text(text)
                    if parsed:
                        print(json.dumps({"data": parsed}, ensure_ascii=False))
                        return
                except Exception:
                    pass
            # If nothing matched, output as raw text wrapped in JSON (NOT as error)
            print(json.dumps({"data": text, "format": "raw_text", "hint": "Response is non-JSON text. Parsed as raw."}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--one-shot":
        tool = sys.argv[2]
        args = sys.argv[3] if len(sys.argv) > 3 else "{}"
        asyncio.run(run_one_shot(tool, args))
    else:
        asyncio.run(run_server())