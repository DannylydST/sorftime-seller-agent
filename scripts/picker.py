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

# Windows GBK console cannot print emoji (UnicodeEncodeError). Force UTF-8 output.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.cache import TTL_PRESETS, get, set
from utils.category_guard import (filter_products, format_risk_section,
                                  format_risk_warning_table,
                                  format_low_risk_tips_table, recommend_safe)
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


def analyze_seller_insights(products: list, stage: str = "grower", risk_warnings: list = None, profile_name: str = "newbie") -> str:
    """Generate seller-friendly opportunity & risk analysis from the FULL product list"""
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

    # 6. Risk Overview (advisory — products remain visible, risk is surfaced)
    if risk_warnings:
        hard_count = sum(1 for e in risk_warnings if e["risk_level"] == "hard")
        capital_count = sum(1 for e in risk_warnings if e["risk_level"] == "capital")
        ops_count = sum(1 for e in risk_warnings if e["risk_level"] == "ops")
        trap_count = sum(1 for e in risk_warnings if e["risk_level"] == "trap")
        flagged = len(risk_warnings)
        total = len(products)
        lines.append(f"- **Risk Overview 🛡️**: {flagged}/{total} products carry elevated risk "
                     f"(🔴Hard {hard_count} / 🟡Capital {capital_count} / 🟠Ops {ops_count} / ⚠️Trap {trap_count}). "
                     f"All products remain visible — review the Risk Advisory table below and decide, or have an "
                     f"independent review agent red-team the shortlist.")
        if profile_name in ("newbie", "grower") and (hard_count + capital_count) > 0:
            lines.append(f"  - 💡 {hard_count + capital_count} products fall in hard/capital risk categories "
                         f"(supplements, apparel, electronics, etc.). They're viable only if you have the "
                         f"credentials or supply-chain capability — otherwise skip them during review.")

    lines.append("")
    return "\n".join(lines)


def run_blueocean(platform: str, site: str, keyword: str, stage: str = "grower", profile: dict = None,
                  json_path: str = "", show_risks: bool = False):
    """Blue Ocean mode: Hidden Earning Index + Product Search (advisory — never removes products)"""
    results = []
    product_data = None
    all_warnings = []
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
        pp_annotated, pp_warnings, pp_tips = filter_products(pp_data if isinstance(pp_data, list) else [], profile)
        if pp_annotated:
            results.append((pp_label, pp_annotated))
        all_warnings.extend(pp_warnings)
        all_low_risk_tips.extend(pp_tips)

    # 2. Product Search
    if platform == "amazon":
        ps_params = {"amz_site": site, "search_name": keyword or "best seller"}
        if stage == "newbie":
            ps_params["ratings_count_min"] = 0
            ps_params["ratings_count_max"] = 500
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
        ps_annotated, ps_warnings, ps_tips = filter_products(ps_data if isinstance(ps_data, list) else [], profile)
        product_data = ps_annotated
        if product_data:
            results.append((ps_label, product_data))
        all_warnings.extend(ps_warnings)
        all_low_risk_tips.extend(ps_tips)

    # Output — advisory mode never outputs an all-blocked page; products are always shown
    if not any(data for _, data in results):
        print(f"# Blue Ocean Discovery Report: {keyword or 'Popular Category'} ({platform.upper()} {site})")
        print()
        print("No product data returned from the API for this keyword. Try a different keyword or verify the site.")
        return

    print(format_profile_badge(profile))

    print(f"# Blue Ocean Discovery Report: {keyword or 'Popular Category'} ({platform.upper()} {site})")
    print()
    for name, data in results:
        print(f"## {name}")
        print(compress(name.replace(" (cached)", ""), data))
        print()

    if product_data:
        print(analyze_seller_insights(product_data, stage, all_warnings, profile.get("name", "newbie").lower()))

    # Quantitative Risk Summary
    if product_data:
        inv_risk = estimate_inventory_risk(product_data)
        crowding = calculate_crowding_index(product_data)
        print(format_risk_summary(inv_risk, crowding, profile.get("name", "newbie").lower()))

    # JSON dump for the post-selection independent review (SKILL.md §1.1.5)
    if json_path and product_data:
        try:
            import os
            os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(product_data, f, ensure_ascii=False, indent=1)
            print(f"> Shortlist saved to `{json_path}` — feed it to review_shortlist.py --keyword \"{keyword}\"")
        except Exception as e:
            print(f"⚠️  Could not write shortlist JSON: {e}")

    # Beginner-friendly safe shortlist (a HIGHLIGHT — all products stay visible above)
    if product_data and profile.get("name") == "Beginner Seller":
        safe_picks = recommend_safe(product_data, profile)
        if safe_picks:
            print("### 🟢 Beginner Safe Shortlist (Recommended Starting Point)")
            print("These products are lowest-risk and fit a beginner profile ($10-45, <1000 reviews, active sales). "
                  "Review them first — but keep the full list above in mind too.")
            print()
            print(compress("product_search", safe_picks))
            print()

    if all_warnings:
        print(format_risk_section(all_warnings, profile, show_risks))

    if all_low_risk_tips:
        print(format_low_risk_tips_table(all_low_risk_tips))


def run_newbie(platform: str, site: str, keyword: str, profile: dict = None, json_path: str = "",
               show_risks: bool = False):
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
        "ratings_count_min": 0,
        "ratings_count_max": 500,
        "price_min": 15,
        "price_max": 40,
    }
    cached = get("product_search", ps_params)
    if cached:
        data = cached
        label = "product_search (cached)"
    else:
        data = call_tool_json("product_search", ps_params)
        set("product_search", ps_params, data, TTL_PRESETS["product_search"])
        label = "product_search"

    # Compatible with MCP response envelope {"doc":...,"data":[...]} vs plain array [...]
    if isinstance(data, dict) and "data" in data:
        data = data.get("data", [])

    annotated, warnings, low_risk_tips = filter_products(data if isinstance(data, list) else [], profile)

    print(format_profile_badge(profile))

    print(f"# Beginner-Friendly Discovery: {keyword or 'Low-Barrier Products'} ({platform.upper()} {site})")
    print()
    print(f"Search scope: review count < 500, price $15–40 — lowering the competitive barrier.")
    profile_name = profile.get("name", "Beginner Seller")
    print(f"Using **{profile_name}** profile — risk is surfaced as ADVISORY warnings, no products are hidden.")
    print()

    if not annotated:
        print("No product data returned from the API for this keyword. Try a different keyword.")
        return

    print(f"## {label}")
    print(compress("product_search", annotated))
    print()
    print(analyze_seller_insights(annotated, stage="newbie", risk_warnings=warnings,
                                  profile_name=profile.get("name", "newbie").lower()))

    # JSON dump for the post-selection independent review (SKILL.md §1.1.5)
    if json_path and annotated:
        try:
            import os
            os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(annotated, f, ensure_ascii=False, indent=1)
            print(f"> Shortlist saved to `{json_path}` — feed it to review_shortlist.py --keyword \"{keyword}\"")
        except Exception as e:
            print(f"⚠️  Could not write shortlist JSON: {e}")

    # Quantitative Risk Summary
    inv_risk = estimate_inventory_risk(annotated)
    crowding = calculate_crowding_index(annotated)
    print(format_risk_summary(inv_risk, crowding, profile.get("name", "newbie").lower()))

    if warnings:
        print(format_risk_section(warnings, profile, show_risks))

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

    # v3.0 advisory mode: products are never hidden. These flags are kept for backward
    # compatibility and now only affect warning emphasis / the safe-shortlist highlight.
    parser.add_argument("--allow-hard", action="store_true",
                        help="[v3.0 legacy] Deprecated — nothing is blocked in advisory mode. Kept for backward compat.")
    parser.add_argument("--allow-capital", action="store_true",
                        help="[v3.0 legacy] Deprecated — nothing is blocked in advisory mode. Kept for backward compat.")
    parser.add_argument("--allow-ops", action="store_true",
                        help="[v3.0 legacy] Deprecated — nothing is blocked in advisory mode. Kept for backward compat.")
    parser.add_argument("--skip-traps", action="store_true",
                        help="[v3.0 legacy] Deprecated — traps are advisory warnings, not filters.")

    # Backward compatible
    parser.add_argument("--explicit-category", action="store_true",
                        help="User explicitly specified a category (backward-compatible, equivalent to --allow-capital --allow-ops)")

    # JSON shortlist output for the independent review step
    parser.add_argument("--json", dest="json_path", default="",
                        help="Save the annotated shortlist to this JSON file (for review_shortlist.py)")

    # Force full risk table even for pro/factory/brand profiles (which collapse by default)
    parser.add_argument("--show-risks", action="store_true",
                        help="Expand the full risk warning table (pro/factory/brand collapse it by default)")

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
        run_blueocean(args.platform, args.site, args.keyword, args.stage, profile, args.json_path, args.show_risks)
    elif args.mode == "newbie":
        run_newbie(args.platform, args.site, args.keyword, profile, args.json_path, args.show_risks)


if __name__ == "__main__":
    main()
