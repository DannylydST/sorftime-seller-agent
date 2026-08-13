"""
Result compressor: compress long JSON responses from Sorftime into agent/seller-friendly summaries
"""

import json
from typing import Any, Dict, List


def _safe_get(item: dict, keys: list, default="") -> Any:
    for k in keys:
        if k in item:
            return item[k]
    return default


RISK_BADGE = {
    "hard": "🔴hard",
    "capital": "🟡cap",
    "ops": "🟠ops",
    "trap": "⚠️trap",
    "safe": "🟢safe",
    "unknown": "",
}


def _risk_badge(item: dict) -> str:
    """Risk badge for annotated products (advisory mode adds _risk_level)."""
    level = item.get("_risk_level", "unknown")
    return RISK_BADGE.get(level, "")


def compress_product_list(data: list, top_n: int = 20) -> str:
    """Compress a product list into a Markdown table (with risk badge when annotated)"""
    if not isinstance(data, list):
        return f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)[:800]}\n```"

    items = data[:top_n]
    has_risk = any(item.get("_risk_level") not in (None, "safe") for item in items)
    header = "| Rank | Risk | ASIN | Title | Price | Monthly Sales | Rating | Reviews |" if has_risk else \
             "| Rank | ASIN | Title | Price | Monthly Sales | Rating | Reviews |"
    sep = "|------|------|------|------|--------|------|--------|" if has_risk else \
          "|------|------|------|------|--------|------|--------|"
    lines = [header, sep]
    for idx, item in enumerate(items, 1):
        asin = _safe_get(item, ["ASIN", "asin"])
        title = _safe_get(item, ["title"])[:30]
        price = _safe_get(item, ["price", "current_price"])
        sales = _safe_get(item, ["monthly_sales_volume", "month_sales_volume"])
        rating = _safe_get(item, ["star_rating"])
        reviews = _safe_get(item, ["review_count"])
        badge = _risk_badge(item)
        if has_risk:
            lines.append(f"| {idx} | {badge:8} | {asin} | {title} | {price} | {sales} | {rating} | {reviews} |")
        else:
            lines.append(f"| {idx} | {asin} | {title} | {price} | {sales} | {rating} | {reviews} |")

    lines.append(f"\n> Total {len(data)} results, showing first {len(items)}.")
    return "\n".join(lines)


def compress_category_report(data: list, top_n: int = 20) -> str:
    """Category report summary"""
    return compress_product_list(data, top_n)


def compress_keyword_list(data: list, top_n: int = 10) -> str:
    """Keyword list summary"""
    if not isinstance(data, list):
        return f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)[:800]}\n```"

    items = data[:top_n]
    lines = [
        f"| Keyword | Monthly Search Volume | CPC Bid | Suggested Bid | Competition |",
        "|--------|----------|-----|----------|--------|",
    ]
    for item in items:
        kw = _safe_get(item, ["keyword"])
        vol = _safe_get(item, ["search_volume"])
        cpc = _safe_get(item, ["cpc"])
        bid = _safe_get(item, ["recommended_bid"])
        comp = _safe_get(item, ["competition"])
        lines.append(f"| {kw} | {vol} | {cpc} | {bid} | {comp} |")

    lines.append(f"\n> Total {len(data)} results, showing first {len(items)}.")
    return "\n".join(lines)


def compress_potential_products(data: list, top_n: int = 20) -> str:
    """Potential index results summary"""
    if not isinstance(data, list):
        return f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)[:800]}\n```"

    # Filter out -99 and -9999 (server returns field as potential_index)
    valid = [x for x in data if _safe_get(x, ["potential_index", "potential_score", "score"], -99) not in (-99, -9999)]
    items = valid[:top_n]
    has_risk = any(item.get("_risk_level") not in (None, "safe") for item in items)

    if has_risk:
        lines = [
            f"| Rank | Risk | ASIN | Title | Potential Index | Price | Monthly Sales | Listed |",
            "|------|------|------|------|--------------|------|--------|----------|",
        ]
    else:
        lines = [
            f"| Rank | ASIN | Title | Potential Index | Price | Monthly Sales | Listed |",
            "|------|------|------|--------------|------|--------|----------|",
        ]
    for idx, item in enumerate(items, 1):
        asin = _safe_get(item, ["ASIN", "asin"])
        title = _safe_get(item, ["title"])[:30]
        score = _safe_get(item, ["potential_index", "potential_score", "score"])
        price = _safe_get(item, ["price", "current_price"])
        sales = _safe_get(item, ["monthly_sales_volume"])
        age = _safe_get(item, ["launch_days"])
        badge = _risk_badge(item)
        if has_risk:
            lines.append(f"| {idx} | {badge:8} | {asin} | {title} | {score} | {price} | {sales} | {age} |")
        else:
            lines.append(f"| {idx} | {asin} | {title} | {score} | {price} | {sales} | {age} |")

    lines.append(f"\n> Total: {len(data)} results, {len(valid)} valid (non -99/-9999), showing first {len(items)}.")
    return "\n".join(lines)


def compress_generic(data: Any, title: str = "Result") -> str:
    """Generic compression: if list of dicts, extract key fields; otherwise truncate JSON"""
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        keys = list(data[0].keys())[:6]
        lines = [f"| {' | '.join(keys)} |", f"| {' | '.join(['---'] * len(keys))} |"]
        for item in data[:15]:
            vals = [str(item.get(k, ""))[:20] for k in keys]
            lines.append(f"| {' | '.join(vals)} |")
        lines.append(f"\n> Total {len(data)} results, showing first {min(len(data), 15)}.")
        return "\n".join(lines)

    text = json.dumps(data, ensure_ascii=False, indent=2)
    if len(text) > 1200:
        text = text[:1200] + "\n... (result too long, truncated)"
    return f"```json\n{text}\n```"


def compress_walmart_product_list(data: list, top_n: int = 20) -> str:
    """Walmart product list compression (keyword_search_results / category_report)

    Supports both raw API keys (Title/Price/ProductId...) and the normalized
    Chinese keys used by walmart_picker's `_normalize_walmart_product`
    (标题/价格/月销量/评论数/评分/卖家/物流方式). Adds a Risk badge when the
    items carry `_risk_level` (advisory mode).
    """
    if not isinstance(data, list):
        return f"```json\n{json.dumps(data, ensure_ascii=False, indent=2)[:800]}\n```"

    items = data[:top_n]
    has_risk = any(item.get("_risk_level") not in (None, "safe") for item in items)
    if has_risk:
        lines = [
            f"| Rank | Risk | ProductId | Title | Price | Monthly Sales | Rating | Reviews | Seller | Fulfillment |",
            "|------|------|-----------|------|------|--------|------|--------|------|------|",
        ]
    else:
        lines = [
            f"| Rank | ProductId | Title | Price | Monthly Sales | Rating | Reviews | Seller | Fulfillment |",
            "|------|-----------|------|------|--------|------|--------|------|------|",
        ]
    for idx, item in enumerate(items, 1):
        pid = _safe_get(item, ["ProductId", "productId", "product_id", "ASIN", "asin", "产品ASIN码"])
        title = str(_safe_get(item, ["Title", "title", "标题"]))[:28]
        price = _safe_get(item, ["Price", "price", "价格"])
        sales = _safe_get(item, ["ListingSalesVolumeOfMonth", "monthly_sales_volume", "listing_sales_volume_of_month", "sales", "月销量"])
        rating = _safe_get(item, ["Ratings", "star_rating", "ratings", "评分"])
        reviews = _safe_get(item, ["ReviewsCount", "reviews", "review_count", "reviews_count", "评论数"])
        seller = _safe_get(item, ["Seller", "seller", "seller_name", "卖家"])
        ship = _safe_get(item, ["Shipedby", "shipBy", "delivery_type", "shipedby", "物流方式"])
        badge = _risk_badge(item)
        if has_risk:
            lines.append(f"| {idx} | {badge:8} | {pid} | {title} | {price} | {sales} | {rating} | {reviews} | {seller} | {ship} |")
        else:
            lines.append(f"| {idx} | {pid} | {title} | {price} | {sales} | {rating} | {reviews} | {seller} | {ship} |")

    lines.append(f"\n> Total {len(data)} results, showing first {len(items)}.")
    return "\n".join(lines)


def compress_walmart_product_detail(data: dict) -> str:
    """Walmart product detail compression"""
    if not isinstance(data, dict):
        return compress_generic(data, title="walmart_product_detail")

    lines = ["## Walmart Product Detail"]
    pid = _safe_get(data, ["ProductId", "productId", "product_id"])
    title = _safe_get(data, ["Title", "title"])
    price = _safe_get(data, ["Price", "price"])
    brand = _safe_get(data, ["Brand", "brand"])
    seller = _safe_get(data, ["Seller", "seller", "seller_name"])
    ship = _safe_get(data, ["Shipedby", "shipBy", "delivery_type", "shipedby"])
    sales = _safe_get(data, ["ListingSalesVolumeOfMonth", "monthly_sales_volume", "listing_sales_volume_of_month"])
    reviews = _safe_get(data, ["ReviewsCount", "review_count", "reviews_count"])
    rating = _safe_get(data, ["Ratings", "star_rating", "ratings"])
    node_tree = _safe_get(data, ["NodeTree", "nodeTree", "category"])

    lines.append(f"- **ProductId**: {pid}")
    lines.append(f"- **Title**: {title}")
    lines.append(f"- **Price**: {price}")
    lines.append(f"- **Brand**: {brand}")
    lines.append(f"- **Seller**: {seller} | **Fulfillment**: {ship}")
    lines.append(f"- **Monthly Sales**: {sales} | **Rating**: {rating} | **Reviews**: {reviews}")

    # NodeTree: extract valid category ID
    if isinstance(node_tree, list) and len(node_tree) >= 2:
        lines.append(f"- **Category Path**: {' > '.join(str(x) for x in node_tree)}")
        # Try to extract nodeId (numeric or with underscores)
        for segment in reversed(node_tree):
            seg = str(segment)
            if seg.replace("_", "").isdigit():
                lines.append(f"- **Category nodeId**: {seg}")
                break

    # Labels
    labels = _safe_get(data, ["Label", "label"])
    if labels:
        lines.append(f"- **Labels**: {', '.join(labels) if isinstance(labels, list) else labels}")

    # Promotions
    promos = []
    for k, label in [("PopularPick", "Popular Pick"), ("Clearance", "Clearance"), ("ReducedPrice", "Reduced Price"), ("Rollback", "Rollback"), ("FlashDeal", "Flash Deal")]:
        if data.get(k):
            promos.append(label)
    if promos:
        lines.append(f"- **Promotions**: {', '.join(promos)}")

    return "\n".join(lines)


def compress(tool_name: str, data: Any) -> str:
    """Auto-select compression strategy by tool type"""
    # Amazon tools
    if tool_name in ("product_search", "category_report", "keyword_search_results"):
        return compress_product_list(data)
    if tool_name in ("keyword_detail", "keyword_extends"):
        return compress_keyword_list(data)
    if tool_name == "potential_product":
        return compress_potential_products(data)

    # Walmart tools
    if tool_name in ("walmart_keyword_search_results", "walmart_category_report_by_node_id"):
        return compress_walmart_product_list(data)
    if tool_name == "walmart_product_detail_by_product_id":
        return compress_walmart_product_detail(data)

    return compress_generic(data, title=tool_name)
