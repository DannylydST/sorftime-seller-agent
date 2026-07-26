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

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.cache import TTL_PRESETS, get, set
from utils.category_guard import filter_products, format_exclusion_table, format_low_risk_tips_table
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


def _normalize_walmart_product(item: dict) -> dict:
    """Normalize Walmart fields to common fields, reuse risk/quant modules"""
    price_str = str(item.get("Price", "$0")).replace("$", "").replace(",", "")
    product_id = item.get("ProductId", "")
    return {
        # Field aliases for compatibility with existing components
        "asin": product_id,
        "ASIN": product_id,
        "产品ASIN码": product_id,
        "标题": item.get("Title", ""),
        "价格": _to_float(price_str),
        "月销量": item.get("ListingSalesVolumeOfMonth", 0),
        "评论数": item.get("ReviewsCount", 0),
        "评分": item.get("Ratings", 0),
        "品牌": item.get("Brand", "Unknown"),
        "卖家": item.get("Seller", ""),
        "物流方式": item.get("Shipedby", ""),
        "类目路径": item.get("NodeTree", []),
        "标签": item.get("Label", []),
        # Preserve raw data
        "_raw": item,
    }


def _walmart_price(item: dict) -> float:
    """Extract Walmart product price"""
    price_str = str(item.get("Price", "$0")).replace("$", "").replace(",", "")
    return _to_float(price_str)


def analyze_walmart_insights(products: list, excluded: list = None, profile_key: str = "newbie") -> str:
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
        brand = item.get("Brand", "Unknown")
        seller = item.get("Seller", "Unknown")
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
        reviews = item.get("ReviewsCount", 0)
        sales = item.get("ListingSalesVolumeOfMonth", 0)
        title = item.get("Title", "")[:30]
        pid = item.get("ProductId", "")
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
    wfs_count = sum(1 for item in top20 if item.get("Shipedby") == "WFS")
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
            and item.get("ReviewsCount", 99999) < 200
        ]
        if newbie_friendly:
            lines.append(f"- **Beginner Recommendations 👍**: {len(newbie_friendly)} products in the $15-40 range with <200 reviews — competitive threshold is relatively friendly.")
        else:
            lines.append("- **Beginner Suitability Note**: Under this keyword, few products match the \"low reviews + mid-range price\" criteria. Consider switching keywords or exploring long-tail niche markets.")

    # 6. Filter impact
    if excluded:
        hard_count = sum(1 for e in excluded if e["risk_level"] == "hard")
        capital_count = sum(1 for e in excluded if e["risk_level"] == "capital")
        ops_count = sum(1 for e in excluded if e["risk_level"] == "ops")
        trap_count = sum(1 for e in excluded if e["risk_level"] == "trap")
        lines.append(f"- **Filter Impact 🛡️**: {len(excluded)} products from original results were filtered out (Hard Block {hard_count} / Capital Intensive {capital_count} / Ops Complex {ops_count} / Trap {trap_count}).")
        if profile_key in ("newbie", "grower") and capital_count > 0:
            lines.append(f"  - Among them, {capital_count} are **capital-intensive categories**. If you have factory or overseas warehouse capabilities, try `--profile factory` for full analysis.")

    lines.append("")
    return "\n".join(lines)


def _fetch_keyword_extends(keyword: str):
    """Fetch Walmart long-tail keywords"""
    params = {"keyword": keyword, "site": "US"}
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
    ps_params = {"keyword": keyword, "site": "US"}
    cached = get("walmart_keyword_search_results", ps_params)
    if cached:
        ps_data = cached
        ps_label = "walmart_keyword_search_results (cached)"
    else:
        ps_data = call_tool_json("walmart_keyword_search_results", ps_params)
        set("walmart_keyword_search_results", ps_params, ps_data,
            TTL_PRESETS.get("walmart_keyword_search_results", 21600))
        ps_label = "walmart_keyword_search_results"

    raw_products = ps_data if isinstance(ps_data, list) else []

    if not raw_products:
        print("> No product data retrieved. Please check keyword or network connection.")
        return

    # Risk filter after field normalization
    normalized = [_normalize_walmart_product(p) for p in raw_products]
    included_norm, excluded, low_risk_tips = filter_products(normalized, profile)
    included = [p["_raw"] for p in included_norm]

    if not included:
        print("## Safety Mode Blocked")
        print()
        print("All results under this keyword belong to **High-Risk Categories** and have been filtered out in SMB seller safety mode.")
        print()
        if excluded:
            print(format_exclusion_table(excluded))
        return

    print(f"## {ps_label}")
    print(compress("walmart_keyword_search_results", included))
    print()

    profile_key = profile.get("key", "newbie")
    print(analyze_walmart_insights(included, excluded, profile_key))

    # Quantitative risk
    inv_risk = estimate_inventory_risk(included_norm)
    crowding = calculate_crowding_index(included_norm)
    print(format_risk_summary(inv_risk, crowding, profile_key))

    if excluded:
        print(format_exclusion_table(excluded))

    if low_risk_tips:
        print(format_low_risk_tips_table(low_risk_tips))


def run_newbie(keyword: str, profile: dict = None):
    """Walmart Beginner Mode: low reviews (<200) + mid-range price ($15-40) + risk filtering"""
    if profile is None:
        profile = get_profile("newbie")

    ps_params = {"keyword": keyword, "site": "US"}
    cached = get("walmart_keyword_search_results", ps_params)
    if cached:
        data = cached
        label = "walmart_keyword_search_results (cached)"
    else:
        data = call_tool_json("walmart_keyword_search_results", ps_params)
        set("walmart_keyword_search_results", ps_params, data,
            TTL_PRESETS.get("walmart_keyword_search_results", 21600))
        label = "walmart_keyword_search_results"

    raw_products = data if isinstance(data, list) else []
    normalized = [_normalize_walmart_product(p) for p in raw_products]

    # Beginner pre-filter: Reviews < 200, Price $15-40
    newbie_filtered = [
        p for p in normalized
        if p.get("评论数", 99999) < 200
        and 15 <= p.get("价格", 0) <= 40
    ]

    included_norm, excluded, low_risk_tips = filter_products(newbie_filtered, profile)
    included = [p["_raw"] for p in included_norm]

    print(format_profile_badge(profile))
    print(f"# Walmart Beginner-Friendly Discovery: {keyword}")
    print()
    print("Filters: Reviews < 200, Price $15-40 (Walmart review count base is lower than Amazon — thresholds adjusted accordingly).")
    print()

    if not included:
        print("## Safety Mode Blocked")
        if excluded:
            print(format_exclusion_table(excluded))
        return

    print(f"## {label}")
    print(compress("walmart_keyword_search_results", included))
    print()

    print(analyze_walmart_insights(included, excluded, "newbie"))

    inv_risk = estimate_inventory_risk(included_norm)
    crowding = calculate_crowding_index(included_norm)
    print(format_risk_summary(inv_risk, crowding, "newbie"))

    if excluded:
        print(format_exclusion_table(excluded))

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
