#!/usr/bin/env python3
"""
Walmart Product Discovery Engine — One-Click Walmart Product Discovery

Reuses Amazon discovery infrastructure (risk filters, quantitative models, seller profiles),
adapted for Walmart data characteristics:
- Review threshold <200 (Walmart overall review count base is lower than Amazon)
- Monitor Walmart 1P (Seller=Walmart) and WFS penetration
- Uses keyword_search_results as core data source (no potential_product)
"""

import argparse
import sys
from pathlib import Path

# Windows GBK console cannot print emoji (UnicodeEncodeError). Force UTF-8 output.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.cache import TTL_PRESETS, get, set
from utils.category_guard import filter_products, format_risk_warning_table, format_low_risk_tips_table
from utils.compressor import compress
from utils.mcp_client import call_tool_json
from utils.seller_profile import get_profile, format_profile_badge
from utils.risk_models import estimate_inventory_risk, calculate_crowding_index, format_risk_summary


def _to_float(val) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _to_int(val) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _wget(item: dict, keys: list, default=""):
    """Case-tolerant field lookup. The live Walmart API returns lowercase snake_case
    keys (title/price/product_id/...), while older docs used PascalCase (Title/Price).
    Accept either."""
    for k in keys:
        if k in item and item[k] not in (None, ""):
            return item[k]
    return default


def _normalize_walmart_product(item: dict) -> dict:
    """Normalize Walmart fields to a key superset, reuse risk/quant modules.

    Emits BOTH the Chinese normalized keys (标题/价格/月销量/...) and English
    aliases (title/price/monthly_sales_volume/...) so compressor, insights and
    risk models all resolve fields regardless of naming convention.
    """
    price_str = str(_wget(item, ["Price", "price", "价格"], "$0")).replace("$", "").replace(",", "")
    product_id = _wget(item, ["ProductId", "product_id", "productId"], "")
    title = _wget(item, ["Title", "title", "标题"], "")
    monthly_sales = _to_int(_wget(item, ["ListingSalesVolumeOfMonth", "listing_sales_volume_of_month",
                                         "monthly_sales_volume", "月销量"], 0))
    reviews = _to_int(_wget(item, ["ReviewsCount", "reviews_count", "review_count", "评论数"], 0))
    rating = _to_float(_wget(item, ["Ratings", "ratings", "star_rating", "评分"], 0))
    brand = _wget(item, ["Brand", "brand", "品牌"], "Unknown")
    seller = _wget(item, ["Seller", "seller", "seller_name", "卖家"], "")
    ship = _wget(item, ["Shipedby", "shipedby", "delivery_type", "物流方式"], "")
    node_tree = _wget(item, ["NodeTree", "node_tree", "nodeTree", "类目路径"], [])
    label = _wget(item, ["Label", "label", "标签"], [])

    return {
        # Chinese normalized keys (original consumers)
        "asin": product_id,
        "ASIN": product_id,
        "产品ASIN码": product_id,
        "标题": title,
        "价格": _to_float(price_str),
        "月销量": monthly_sales,
        "评论数": reviews,
        "评分": rating,
        "品牌": brand,
        "卖家": seller,
        "物流方式": ship,
        "类目路径": node_tree,
        "标签": label,
        # English aliases (live-API style + risk/compressor compatibility)
        "product_id": product_id,
        "ProductId": product_id,
        "title": title,
        "price": _to_float(price_str),
        "monthly_sales_volume": monthly_sales,
        "review_count": reviews,
        "rating": rating,
        "brand": brand,
        "seller": seller,
        "delivery_type": ship,
        # Preserve raw data
        "_raw": item,
    }


def _walmart_price(item: dict) -> float:
    """Extract Walmart product price (tolerant of key casing + Chinese normalized keys)"""
    price_str = str(_wget(item, ["Price", "price", "价格"], "$0")).replace("$", "").replace(",", "")
    return _to_float(price_str)


def analyze_walmart_insights(products: list, risk_warnings: list = None, profile_key: str = "newbie") -> str:
    """Walmart-specific insights analysis"""
    if not isinstance(products, list) or not products:
        return ""

    lines = []
    lines.append("## Product Discovery — Opportunities & Risks")
    lines.append("")

    top20 = products[:20]

    # 1. Brand / Walmart 1P monopoly
    brand_counts = {}
    seller_counts = {}
    for item in top20:
        brand = _wget(item, ["品牌", "brand", "Brand"], "Unknown")
        seller = _wget(item, ["卖家", "seller", "Seller"], "Unknown")
        brand_counts[brand] = brand_counts.get(brand, 0) + 1
        seller_counts[seller] = seller_counts.get(seller, 0) + 1

    monopoly_brands = {b: c for b, c in brand_counts.items() if c >= 3}
    if monopoly_brands:
        dominant = max(monopoly_brands, key=monopoly_brands.get)
        lines.append(f"- **Brand Monopoly Risk ⚠️**: `{dominant}` occupies {monopoly_brands[dominant]} slots in TOP20 — intense competition pressure for new entrants.")
    else:
        lines.append(f"- **Brand Concentration**: No absolute monopoly brand in TOP20 — competition is relatively dispersed; opportunity to enter.")

    # Walmart 1P share
    walmart_self = seller_counts.get("Walmart", 0)
    if walmart_self >= 5:
        lines.append(f"- **Walmart 1P Squeeze Risk 🔴**: {walmart_self} Walmart 1P items (WFS fulfillment) in TOP20. 1P has natural advantages in search and conversion — avoid direct competition with similar products.")
    elif walmart_self > 0:
        lines.append(f"- **Walmart 1P Presence**: {walmart_self} Walmart 1P items in TOP20 — focus on differentiation.")

    # 2. Opportunity Window: low reviews + high sales (Walmart threshold <200)
    opportunities = []
    for item in top20:
        reviews = _to_int(item.get("评论数", _wget(item, ["ReviewsCount", "reviews_count", "review_count"], 0)))
        sales = _to_int(item.get("月销量", _wget(item, ["ListingSalesVolumeOfMonth", "listing_sales_volume_of_month", "monthly_sales_volume"], 0)))
        title = str(_wget(item, ["标题", "title", "Title"], ""))[:30]
        pid = _wget(item, ["产品ASIN码", "product_id", "ProductId"], "")
        if reviews < 200 and sales > 5000:
            opportunities.append(f"`{pid}` ({title}…) — Reviews {reviews} / Monthly Sales {sales}")

    if opportunities:
        lines.append(f"- **Opportunity Window ✅**: These products have low reviews (<200) but high sales — market not yet fully dominated by established listings:")
        for opp in opportunities[:5]:
            lines.append(f"  - {opp}")
    else:
        lines.append(f"- **Opportunity Window**: Few low-review, high-sales products in TOP20 — category maturity is relatively high.")

    # 3. Price war risk
    low_price_count = sum(1 for item in top20 if _walmart_price(item) < 10)
    if low_price_count >= 5:
        lines.append(f"- **Price War Risk 🔥**: {low_price_count} products in TOP20 priced below $10 — profit margins may be severely compressed.")
    else:
        lines.append(f"- **Price Band Health**: Low-priced products (<$10) account for a small share in TOP20 — some pricing buffer exists.")

    # 4. WFS penetration rate
    wfs_count = sum(1 for item in top20 if _wget(item, ["物流方式", "shipedby", "Shipedby"], "").upper() == "WFS")
    wfs_ratio = wfs_count / len(top20) * 100 if top20 else 0
    if wfs_ratio > 70:
        lines.append(f"- **WFS High Penetration**: {wfs_ratio:.0f}% of TOP20 use Walmart Fulfillment Services (WFS). Sellers not using WFS are at a disadvantage in delivery speed and search ranking — evaluate WFS onboarding costs.")
    elif wfs_ratio > 40:
        lines.append(f"- **WFS Moderate Penetration**: {wfs_ratio:.0f}% of TOP20 use WFS. Fulfillment methods are split — self-fulfillment still viable but pay attention to delivery speed.")
    else:
        lines.append(f"- **WFS Low Penetration**: Only {wfs_ratio:.0f}% of TOP20 use WFS — self-fulfillment environment is relatively friendly.")

    # 5. Beginner suitability
    if profile_key == "newbie":
        newbie_friendly = [
            item for item in top20
            if 15 <= _walmart_price(item) <= 40
            and _to_int(item.get("评论数", _wget(item, ["ReviewsCount", "reviews_count", "review_count"], 99999))) < 200
        ]
        if newbie_friendly:
            lines.append(f"- **Beginner Recommendations 👍**: {len(newbie_friendly)} products in the $15-40 range with <200 reviews — competitive threshold is relatively friendly.")
        else:
            lines.append("- **Beginner Suitability Note**: Under this keyword, few products match the \"low reviews + mid-range price\" criteria. Consider switching keywords or exploring long-tail niche markets.")

    # 6. Risk overview (advisory — products remain visible)
    if risk_warnings:
        hard_count = sum(1 for e in risk_warnings if e["risk_level"] == "hard")
        capital_count = sum(1 for e in risk_warnings if e["risk_level"] == "capital")
        ops_count = sum(1 for e in risk_warnings if e["risk_level"] == "ops")
        trap_count = sum(1 for e in risk_warnings if e["risk_level"] == "trap")
        lines.append(f"- **Risk Overview 🛡️**: {len(risk_warnings)}/{len(products)} products carry elevated risk "
                     f"(🔴Hard {hard_count} / 🟡Capital {capital_count} / 🟠Ops {ops_count} / ⚠️Trap {trap_count}). "
                     f"All products remain visible — review the Risk Advisory table and decide, or have an independent "
                     f"review agent red-team the shortlist.")
        if profile_key in ("newbie", "grower") and (hard_count + capital_count) > 0:
            lines.append(f"  - 💡 {hard_count + capital_count} fall in hard/capital categories — viable only with the "
                         f"right credentials or supply-chain capability.")

    lines.append("")
    return "\n".join(lines)


def _fetch_keyword_extends(keyword: str):
    """Fetch Walmart long-tail keywords"""
    params = {"keyword": keyword}
    cached = get("walmart_keyword_extends", params)
    if cached:
        return cached
    try:
        data = call_tool_json("sorftime_raw_call", {
            "tool_name": "walmart_keyword_extends",
            "arguments": params
        })
        set("walmart_keyword_extends", params, data, TTL_PRESETS.get("walmart_keyword_extends", 43200))
        return data
    except Exception:
        return None


def run_blueocean(keyword: str, profile: dict = None):
    """Walmart Blue Ocean Mode: long-tail keywords + product search + risk filtering + quantitative analysis"""
    if profile is None:
        profile = get_profile("newbie")

    print(format_profile_badge(profile))
    print(f"# Walmart Blue Ocean Discovery Report: {keyword}")
    print()

    # 1. Long-tail keywords
    extends = _fetch_keyword_extends(keyword)
    if isinstance(extends, list) and extends:
        print("## Long-Tail Keywords")
        print(compress("walmart_keyword_extends", extends))
        print()

    # 2. Product search (core data source)
    ps_params = {"keyword": keyword}
    cached = get("walmart_keyword_search_results", ps_params)
    if cached:
        ps_data = cached
        ps_label = "walmart_keyword_search_results (cached)"
    else:
        ps_data = call_tool_json("walmart_keyword_search_results", ps_params)
        set("walmart_keyword_search_results", ps_params, ps_data,
            TTL_PRESETS.get("walmart_keyword_search_results", 21600))
        ps_label = "walmart_keyword_search_results"

    # Unwrap MCP response envelope {"doc":...,"data":[...]} vs plain array [...]
    if isinstance(ps_data, dict) and "data" in ps_data:
        ps_data = ps_data.get("data", [])
    raw_products = ps_data if isinstance(ps_data, list) else []

    if not raw_products:
        print("> No product data retrieved. Please check keyword or network connection.")
        return

    # Risk assessment (advisory — never removes products, surfaces warnings instead)
    normalized = [_normalize_walmart_product(p) for p in raw_products]
    annotated, warnings, low_risk_tips = filter_products(normalized, profile)

    print(f"## {ps_label}")
    print(compress("walmart_keyword_search_results", annotated))
    print()

    profile_key = profile.get("key", "newbie")
    print(analyze_walmart_insights(annotated, warnings, profile_key))

    # Quantitative risk
    inv_risk = estimate_inventory_risk(annotated)
    crowding = calculate_crowding_index(annotated)
    print(format_risk_summary(inv_risk, crowding, profile_key))

    if warnings:
        print(format_risk_warning_table(warnings))

    if low_risk_tips:
        print(format_low_risk_tips_table(low_risk_tips))


def run_newbie(keyword: str, profile: dict = None):
    """Walmart Beginner Mode: low reviews (<200) + mid-range price ($15-40) + risk filtering"""
    if profile is None:
        profile = get_profile("newbie")

    ps_params = {"keyword": keyword}
    cached = get("walmart_keyword_search_results", ps_params)
    if cached:
        data = cached
        label = "walmart_keyword_search_results (cached)"
    else:
        data = call_tool_json("walmart_keyword_search_results", ps_params)
        set("walmart_keyword_search_results", ps_params, data,
            TTL_PRESETS.get("walmart_keyword_search_results", 21600))
        label = "walmart_keyword_search_results"

    # Unwrap MCP response envelope {"doc":...,"data":[...]} vs plain array [...]
    if isinstance(data, dict) and "data" in data:
        data = data.get("data", [])
    raw_products = data if isinstance(data, list) else []
    normalized = [_normalize_walmart_product(p) for p in raw_products]

    # Beginner pre-filter: Reviews < 200, Price $15-40
    newbie_filtered = [
        p for p in normalized
        if p.get("评论数", 99999) < 200
        and 15 <= p.get("价格", 0) <= 40
    ]

    annotated, warnings, low_risk_tips = filter_products(newbie_filtered, profile)

    print(format_profile_badge(profile))
    print(f"# Walmart Beginner-Friendly Discovery: {keyword}")
    print()
    print("Search scope: Reviews < 200, Price $15-40 (Walmart review count base is lower than Amazon — thresholds adjusted accordingly).")
    print("Risk is surfaced as ADVISORY warnings — no products are hidden.")
    print()

    if not annotated:
        print("No product data returned for this keyword.")
        return

    print(f"## {label}")
    print(compress("walmart_keyword_search_results", annotated))
    print()

    print(analyze_walmart_insights(annotated, warnings, "newbie"))

    inv_risk = estimate_inventory_risk(annotated)
    crowding = calculate_crowding_index(annotated)
    print(format_risk_summary(inv_risk, crowding, "newbie"))

    if warnings:
        print(format_risk_warning_table(warnings))

    if low_risk_tips:
        print(format_low_risk_tips_table(low_risk_tips))


def main():
    parser = argparse.ArgumentParser(description="Walmart Product Discovery Engine")
    parser.add_argument("--mode", default="blueocean", choices=["blueocean", "newbie"])
    parser.add_argument("--keyword", required=True, help="Search keyword")
    parser.add_argument("--profile", default="newbie",
                        choices=["newbie", "grower", "pro", "factory", "brand"])
    parser.add_argument("--allow-hard", action="store_true")
    parser.add_argument("--allow-capital", action="store_true")
    parser.add_argument("--allow-ops", action="store_true")
    parser.add_argument("--skip-traps", action="store_true")
    args = parser.parse_args()

    profile = get_profile(
        profile_name=args.profile,
        allow_hard=args.allow_hard,
        allow_capital=args.allow_capital,
        allow_ops=args.allow_ops,
        skip_traps=args.skip_traps,
    )
    profile["key"] = args.profile  # Preserve key for downstream logic

    if args.mode == "blueocean":
        run_blueocean(args.keyword, profile)
    elif args.mode == "newbie":
        run_newbie(args.keyword, profile)


if __name__ == "__main__":
    main()
