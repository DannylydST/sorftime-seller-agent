#!/usr/bin/env python3
"""
Product Discovery Engine — auto-compose Sorftime tools to generate discovery summaries.
Seller-first perspective: go beyond data listing to surface opportunities, flag risks, and offer actionable advice.

v2.0: Seller profile system + 4-tier risk filtering + enhanced trap signals
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.cache import TTL_PRESETS, get, set
from utils.category_guard import filter_products, format_exclusion_table, format_all_blocked_page, format_low_risk_tips_table
from utils.compressor import compress, _safe_get
from utils.mcp_client import call_tool_json
from utils.seller_profile import get_profile, format_profile_badge, format_profile_help
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


def analyze_seller_insights(products: list, stage: str = "grower", excluded: list = None, profile_name: str = "newbie") -> str:
    """Generate seller-friendly opportunity & risk analysis from product list"""
    if not isinstance(products, list) or not products:
        return ""

    lines = []
    lines.append("## Product Discovery — Opportunities & Risks")
    lines.append("")

    # 1. Brand Monopoly Risk
    top10 = products[:10]
    brand_counts = {}
    for item in top10:
        brand = _safe_get(item, ["品牌", "brand", "Brand"], "Unknown")
        brand_counts[brand] = brand_counts.get(brand, 0) + 1

    monopoly_brands = {b: c for b, c in brand_counts.items() if c >= 3}
    if monopoly_brands:
        dominant = max(monopoly_brands, key=monopoly_brands.get)
        lines.append(f"- **Brand Monopoly Risk ⚠️**: `{dominant}` holds {monopoly_brands[dominant]} spots in the TOP 10 — heavy competitive pressure for new entrants.")
    else:
        lines.append(f"- **Brand Concentration**: No single brand dominates the TOP 10. Competition is relatively dispersed — potential entry opportunity.")

    if "Amazon Basics" in brand_counts:
        lines.append(f"- **Amazon/Platform Squeeze Risk**: Amazon Basics appears in the TOP 10 — low-price first-party listings may compress margins for similar products or follow-on sellers.")

    # 2. Opportunity Window: low reviews, high sales
    opportunities = []
    for item in products[:20]:
        reviews = _to_int(_safe_get(item, ["review_count", "Review Count"], 99999))
        sales = _to_int(_safe_get(item, ["monthly_sales_volume", "Sales Volume"], 0))
        title = _safe_get(item, ["title", "Product Name"], "")[:30]
        asin = _safe_get(item, ["ASIN", "asin"], "")
        if reviews < 1000 and sales > 20000:
            opportunities.append(f"`{asin}` ({title}…) — Reviews {reviews} / Monthly sales {sales}")
        elif reviews < 500 and sales > 10000:
            opportunities.append(f"`{asin}` ({title}…) — Reviews {reviews} / Monthly sales {sales}")

    if opportunities:
        lines.append(f"- **Opportunity Window ✅**: These products have low review counts but high sales, suggesting the market isn't fully locked in by established listings — an opening for newcomers or new launches:")
        for opp in opportunities[:5]:
            lines.append(f"  - {opp}")
    else:
        lines.append(f"- **Opportunity Window**: Few low-review, high-sales products in the top 20 — the category appears relatively mature.")

    # 3. Price compression / Price War Risk
    low_price_count = sum(1 for item in products[:20] if _to_float(_safe_get(item, ["price", "Current Price"], 999)) < 10)
    if low_price_count >= 5:
        lines.append(f"- **Price War Risk 🔥**: {low_price_count} products in the TOP 20 are priced below $10 — margins may be severely compressed. Think twice before entering low-price red oceans.")
    else:
        lines.append(f"- **Price Band Health**: Low-priced products (<$10) make up a small share of the TOP 20 — the price band has some buffer room.")

    # 4. Review-sales anomaly (suspicious or viral)
    viral = [item for item in products[:20]
             if _to_int(_safe_get(item, ["review_count"], 0)) < 500
             and _to_int(_safe_get(item, ["monthly_sales_volume"], 0)) > 50000]
    if viral:
        lines.append(f"- **Anomaly Signals ⚠️**: {len(viral)} products have very few reviews (<500) but extremely high sales (>50K). This could be a viral breakout or signs of review manipulation / merged listings — further investigation recommended.")

    # 5. Beginner-tailored recommendations
    if stage == "newbie":
        newbie_friendly = [item for item in products[:20]
                           if 15 <= _to_float(_safe_get(item, ["price"], 0)) <= 40
                           and _to_int(_safe_get(item, ["review_count"], 99999)) < 500]
        if newbie_friendly:
            lines.append(f"- **Beginner Recommendations 👍**: {len(newbie_friendly)} products in the filtered results are priced $15–40 with <500 reviews — relatively friendly competitive threshold. Prioritize reviewing these product details and evaluate against your supply chain capabilities.")
        else:
            lines.append('- **Beginner Suitability**: Under the current keyword, few products match the "low reviews + mid price" criteria. Consider switching keywords or exploring long-tail niche subcategories.')

    # 6. Filter Impact
    if excluded:
        hard_count = sum(1 for e in excluded if e["risk_level"] == "hard")
        capital_count = sum(1 for e in excluded if e["risk_level"] == "capital")
        ops_count = sum(1 for e in excluded if e["risk_level"] == "ops")
        trap_count = sum(1 for e in excluded if e["risk_level"] == "trap")
        lines.append(f"- **Filter Impact 🛡️**: {len(excluded)} products were filtered from the original results (Hard Block {hard_count} / Capital-Intensive {capital_count} / Operations-Complex {ops_count} / Trap Signal {trap_count}). The accessible product pool has been narrowed — interpret the competitive landscape based on filtered results only.")
        if profile_name in ("newbie", "grower") and capital_count > 0:
            lines.append(f"  - 💡 {capital_count} of these are **capital-intensive categories** (apparel/shoes/bags/furniture, etc.). If you have factory or overseas warehouse capabilities, try `--profile factory` for the full analysis.")

    lines.append("")
    return "\n".join(lines)


def run_blueocean(platform: str, site: str, keyword: str, stage: str = "grower", profile: dict = None):
    """Blue Ocean mode: Hidden Earning Index + Product Search"""
    results = []
    product_data = None
    all_excluded = []
    all_low_risk_tips = []

    if profile is None:
        profile = get_profile("newbie")

    # 1. Hidden Earning Index (Amazon US only)
    if platform == "amazon" and site == "US":
        params = {"amz_site": "US"}
        if keyword:
            params["search_name"] = keyword
        cached = get("potential_product", params)
        if cached:
            pp_data = cached
            pp_label = "potential_product (cached)"
        else:
            pp_data = call_tool_json("potential_product", params)
            set("potential_product", params, pp_data, TTL_PRESETS.get("potential_product", 21600))
            pp_label = "potential_product"

        # Compatible with MCP response envelope {"doc":...,"data":[...]} vs plain array [...]
        if isinstance(pp_data, dict) and "data" in pp_data:
            pp_data = pp_data.get("data", [])
        pp_included, pp_excluded, pp_tips = filter_products(pp_data if isinstance(pp_data, list) else [], profile)
        if pp_included:
            results.append((pp_label, pp_included))
        all_excluded.extend(pp_excluded)
        all_low_risk_tips.extend(pp_tips)

    # 2. Product Search
    if platform == "amazon":
        ps_params = {"amz_site": site, "search_name": keyword or "best seller"}
        if stage == "newbie":
            ps_params["ratings_count_range"] = '["0","500"]'
        cached = get("product_search", ps_params)
        if cached:
            ps_data = cached
            ps_label = "product_search (cached)"
        else:
            ps_data = call_tool_json("product_search", ps_params)
            set("product_search", ps_params, ps_data, TTL_PRESETS.get("product_search", 21600))
            ps_label = "product_search"

        # Compatible with MCP response envelope {"doc":...,"data":[...]} vs plain array [...]
        if isinstance(ps_data, dict) and "data" in ps_data:
            ps_data = ps_data.get("data", [])
        ps_included, ps_excluded, ps_tips = filter_products(ps_data if isinstance(ps_data, list) else [], profile)
        product_data = ps_included
        if product_data:
            results.append((ps_label, product_data))
        all_excluded.extend(ps_excluded)
        all_low_risk_tips.extend(ps_tips)

    # Output
    # If all results are filtered, output the dedicated block page
    if not any(data for _, data in results):
        print(format_all_blocked_page(keyword, all_excluded))
        return

    print(format_profile_badge(profile))

    print(f"# Blue Ocean Discovery Report: {keyword or 'Popular Category'} ({platform.upper()} {site})")
    print()
    for name, data in results:
        print(f"## {name}")
        print(compress(name.replace(" (cached)", ""), data))
        print()

    if product_data:
        print(analyze_seller_insights(product_data, stage, all_excluded, profile.get("name", "newbie").lower()))

    # Quantitative Risk Summary
    if product_data:
        inv_risk = estimate_inventory_risk(product_data)
        crowding = calculate_crowding_index(product_data)
        print(format_risk_summary(inv_risk, crowding, profile.get("name", "newbie").lower()))

    if all_excluded:
        print(format_exclusion_table(all_excluded))

    if all_low_risk_tips:
        print(format_low_risk_tips_table(all_low_risk_tips))


def run_newbie(platform: str, site: str, keyword: str, profile: dict = None):
    """Beginner Mode: low-competition filtering + margin-friendly"""
    if profile is None:
        profile = get_profile("newbie")

    if platform != "amazon":
        print(f"# Beginner Discovery: {platform.upper()} {site}")
        print("> Beginner Mode is currently optimized for Amazon. Other platforms will use generic search.")
        print()

    ps_params = {
        "amz_site": site,
        "search_name": keyword or "easy start product",
        "ratings_count_range": '["0","500"]',
        "price_range": '["15","40"]',
    }
    cached = get("product_search", ps_params)
    if cached:
        data = cached
        label = "product_search (cached)"
    else:
        data = call_tool_json("product_search", ps_params)
        set("product_search", ps_params, data, TTL_PRESETS["product_search"])
        label = "product_search"

    included, excluded, low_risk_tips = filter_products(data if isinstance(data, list) else [], profile)

    print(format_profile_badge(profile))

    print(f"# Beginner-Friendly Discovery: {keyword or 'Low-Barrier Products'} ({platform.upper()} {site})")
    print()
    print(f"Filters: review count < 500, price $15–40 — lowering the competitive barrier.")
    profile_name = profile.get("name", "Beginner Seller")
    print(f"Using **{profile_name}** profile — corresponding risk filter rules are active.")
    print()

    # All blocked
    if not included:
        print(format_all_blocked_page(keyword, excluded))
        return

    print(f"## {label}")
    print(compress("product_search", included))
    print()
    print(analyze_seller_insights(included, stage="newbie", excluded=excluded, profile_name=profile.get("name", "newbie").lower()))

    # Quantitative Risk Summary
    inv_risk = estimate_inventory_risk(included)
    crowding = calculate_crowding_index(included)
    print(format_risk_summary(inv_risk, crowding, profile.get("name", "newbie").lower()))

    if excluded:
        print(format_exclusion_table(excluded))

    if low_risk_tips:
        print(format_low_risk_tips_table(low_risk_tips))


def main():
    parser = argparse.ArgumentParser(description="Sorftime Product Discovery Engine v2.0")
    parser.add_argument("--mode", default="blueocean", choices=["blueocean", "newbie"])
    parser.add_argument("--platform", default="amazon")
    parser.add_argument("--site", default="US")
    parser.add_argument("--keyword", default="")
    parser.add_argument("--stage", default="grower")

    # Seller profile (v2.0)
    parser.add_argument("--profile", default="newbie",
                        choices=["newbie", "grower", "pro", "factory", "brand"],
                        help="Seller profile: newbie(Beginner)/grower(Growing)/pro(Professional)/factory(Factory)/brand(Brand)")

    # Per-category override flags
    parser.add_argument("--allow-hard", action="store_true",
                        help="Allow hard-block categories (⚠️ strongly discouraged — requires FDA/EPA/regulatory credentials)")
    parser.add_argument("--allow-capital", action="store_true",
                        help="Allow capital-intensive categories (apparel/shoes/bags/furniture, etc.)")
    parser.add_argument("--allow-ops", action="store_true",
                        help="Allow operations-complex categories (electronics with batteries, liquids, auto parts, etc.)")
    parser.add_argument("--skip-traps", action="store_true",
                        help="Skip trap signal filtering (⚠️ not recommended)")

    # Backward compatible
    parser.add_argument("--explicit-category", action="store_true",
                        help="User explicitly specified a category (backward-compatible, equivalent to --allow-capital --allow-ops)")

    # Help
    parser.add_argument("--profile-help", action="store_true",
                        help="Show detailed seller profile explanation")

    args = parser.parse_args()

    if args.profile_help:
        print(format_profile_help())
        return

    # Build profile
    # Backward compatible: explicit-category is equivalent to allowing capital + ops
    allow_capital = args.allow_capital or args.explicit_category
    allow_ops = args.allow_ops or args.explicit_category

    profile = get_profile(
        profile_name=args.profile,
        allow_hard=args.allow_hard,
        allow_capital=allow_capital,
        allow_ops=allow_ops,
        skip_traps=args.skip_traps,
    )

    if args.mode == "blueocean":
        run_blueocean(args.platform, args.site, args.keyword, args.stage, profile)
    elif args.mode == "newbie":
        run_newbie(args.platform, args.site, args.keyword, profile)


if __name__ == "__main__":
    main()
