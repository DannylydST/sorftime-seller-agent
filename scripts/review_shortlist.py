#!/usr/bin/env python3
"""
Independent Shortlist Reviewer (v3.0)

A deterministic "second pair of eyes" that runs AFTER product selection.
It is intentionally SEPARATE from the discovery risk model (category_guard) so a
flaw in one layer doesn't silently pass through both. It checks dimensions the
discovery engine does NOT:

  1. Margin sanity         — low ASP + no sales = no room for FBA+ads+profit
  2. IP / trademark scan   — branded terms, "patent pending", celebrity/IP names
  3. Review anomaly        — suspiciously few reviews for huge sales (merging/violations)
  4. Seasonal dependency   — holiday-anchored product outside its window
  5. Compliance red flags  — FDA/FCC/CPC-sensitive terms the risk model may have missed

Output: per-product verdict GO / CAUTION / NO-GO with evidence. This is ADVICE —
it does not remove products. In the agent flow, pair it with an independent
review SUB-AGENT (fresh context) that reads this output + the shortlist and
renders the final recommendation.

Usage:
  python3 scripts/review_shortlist.py <shortlist.json> [--keyword "yoga mat"] [--json]
  # shortlist.json = the annotated product array from picker.py (has _risk_level)
  # --keyword      = optional search term; products that don't match it get NO-GO
  #                  (category-relevance check — prevents off-topic pollution)
"""

import argparse
import json
import re
import sys
from pathlib import Path

# Windows GBK console cannot print emoji. Force UTF-8 output.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.category_guard import assess_product


# ============================================================================
# Independent check dimensions (deliberately NOT from category_guard)
# ============================================================================

# IP / trademark-sensitive terms — if present, recommend caution before sourcing
IP_TERMS = [
    "patent pending", "patented", "trademark", "disney", "marvel", "pokemon",
    "nintendo", "star wars", "nfl", "nba", "mlb", "ncaa", "coca", "logo",
    "licensed", "official", "collab", "hello kitty", "batman", "spider-man",
]

# Complimentary red flags for safety-sensitive categories
COMPLIANCE_TERMS = [
    "fda", "medical grade", "surgical", "clinical", "therapeutic",
    "pharmaceutical", "antiseptic", "hypoallergenic for infants",
]

# Seasonal anchors — outside their window these tie up capital
SEASONAL_ANCHORS = {
    "christmas": (10, 12), "xmas": (10, 12), "halloween": (9, 10),
    "valentine": (1, 2), "easter": (3, 4), "thanksgiving": (10, 11),
    "fourth of july": (6, 7), "back to school": (7, 8), "母亲节": (4, 5),
    "圣诞节": (10, 12), "万圣节": (9, 10), "情人节": (1, 2),
}


def _f(val):
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def _i(val):
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _get(item, keys, default=""):
    for k in keys:
        if k in item and item[k] is not None:
            return item[k]
    return default


def _extract_text(item: dict) -> str:
    """Title + category fields, for keyword-relevance check."""
    parts = []
    for key in ["title", "Title", "Product Name", "标题",
                "category", "node_name", "top_category", "subcategory",
                "所属大类", "所属细分类目", "类目", "keywords", "关键词"]:
        val = item.get(key, "")
        if val:
            parts.append(str(val))
    return " ".join(parts).lower()


def _is_relevant(keyword: str, item_text: str) -> bool:
    """Rough category-relevance: significant keyword tokens must appear in product text.
    Catches keyword-pollution (e.g. supplements/towels returned for a 'yoga mat' query)."""
    if not keyword:
        return True  # no keyword provided → cannot judge relevance
    kw_tokens = [t for t in keyword.lower().split() if len(t) > 2]
    if not kw_tokens:
        return True
    return any(t in item_text for t in kw_tokens)


def review_product(item: dict, keyword: str = "") -> dict:
    """Run independent checks on one product. Returns {verdict, reasons, checks}."""
    title = str(_get(item, ["title", "Title", "Product Name"], "")).lower()
    item_text = _extract_text(item)
    price = _f(_get(item, ["price", "current_price", "Price"], 0))
    sales = _i(_get(item, ["monthly_sales_volume", "month_sales_volume", "ListingSalesVolumeOfMonth", "Sales Volume"], 0))
    reviews = _i(_get(item, ["review_count", "Review Count", "ReviewsCount"], 0))
    rating = _f(_get(item, ["rating", "star_rating", "Star Rating"], 0))

    reasons = []
    hard_flags = 0
    caution_flags = 0

    # 0. Category-relevance: off-topic products (keyword pollution) are NO-GO.
    if not _is_relevant(keyword, item_text):
        reasons.append(f"Off-topic: title/category does not match query '{keyword}' — keyword-pollution product")
        hard_flags += 1

    # 1. Margin sanity: low ASP with no volume = no profit room after FBA + ads + COGS
    if 0 < price < 8 and sales < 2000:
        reasons.append(f"Margin: ${price} ASP with {sales}/mo — likely no room after FBA($3-5)+ads($1-2)+COGS")
        hard_flags += 1
    elif price < 8 and sales >= 2000:
        reasons.append(f"Margin: ${price} ASP but {sales}/mo volume — check if margin survives FBA+ads")
        caution_flags += 1

    # 2. IP / trademark scan
    ip_hits = [t for t in IP_TERMS if t in title]
    if ip_hits:
        reasons.append(f"IP: contains {ip_hits} — infringement/trademark risk, verify authorization before sourcing")
        hard_flags += 1

    # 3. Review anomaly: huge sales with tiny reviews => merged/fake listings
    if reviews > 0 and sales > 50000 and reviews < 500:
        reasons.append(f"Review anomaly: {sales}/mo sales but only {reviews} reviews — possible merged/violating listing")
        caution_flags += 1

    # 4. Seasonal dependency outside window
    import datetime
    month = datetime.datetime.now().month
    for anchor, (start, end) in SEASONAL_ANCHORS.items():
        if anchor in title:
            in_window = (start <= month <= end) or (start > end and (month >= start or month <= end))
            if not in_window:
                reasons.append(f"Seasonal: '{anchor}' product outside its {start}-{end} window — clearance risk after peak")
                caution_flags += 1

    # 5. Compliance red flags
    comp_hits = [t for t in COMPLIANCE_TERMS if t in title]
    if comp_hits:
        reasons.append(f"Compliance: contains {comp_hits} — verify certifications (FDA/FCC/CPC) before sourcing")
        caution_flags += 1

    # Verdict
    if hard_flags > 0:
        verdict = "NO-GO"
    elif caution_flags > 0:
        verdict = "CAUTION"
    else:
        verdict = "GO"

    return {
        "asin": _get(item, ["ASIN", "asin", "ProductId", "product_id"], "N/A"),
        "title": str(_get(item, ["title", "Title"], ""))[:45],
        "price": price,
        "monthly_sales": sales,
        "reviews": reviews,
        "risk_level": item.get("_risk_level", "safe"),
        "verdict": verdict,
        "reasons": reasons,
    }


def main():
    parser = argparse.ArgumentParser(description="Independent Shortlist Reviewer")
    parser.add_argument("input", help="Path to shortlist JSON (annotated product array)")
    parser.add_argument("--keyword", default="", help="Original search keyword — enables category-relevance check")
    parser.add_argument("--json", action="store_true", help="Emit raw JSON")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    if isinstance(data, dict) and "data" in data:
        data = data["data"]

    results = [review_product(p, args.keyword) for p in data]

    if args.json:
        print(json.dumps({"verdicts": results}, ensure_ascii=False, indent=2))
        return 0

    counts = {"GO": 0, "CAUTION": 0, "NO-GO": 0}
    for r in results:
        counts[r["verdict"]] += 1

    print("# Independent Shortlist Review")
    print()
    print(f"> {len(results)} products reviewed independently. Verdict: "
          f"GO {counts['GO']} / CAUTION {counts['CAUTION']} / NO-GO {counts['NO-GO']}")
    print()
    print("| Verdict | Risk | ASIN | Title | Price | Sales | Reasons |")
    print("|---------|------|------|-------|-------|-------|---------|")
    for r in results:
        badge = {"GO": "🟢GO", "CAUTION": "🟡CAUTION", "NO-GO": "🔴NO-GO"}[r["verdict"]]
        reasons = "; ".join(r["reasons"]) if r["reasons"] else "—"
        print(f"| {badge} | {r['risk_level']:7} | {r['asin']} | {r['title']} | {r['price']} | {r['monthly_sales']} | {reasons[:80]} |")

    print()
    print("> This is ADVICE, not censorship — every product stays in the shortlist. "
          "For the final call, spawn an independent review SUB-AGENT (fresh context, "
          "no prior data) and have it challenge the GO picks against these flags.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
