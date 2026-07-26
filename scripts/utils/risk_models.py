"""
Risk Quantification Models — capital commitment & crowding index assessment

Based on product listing data, estimates:
- Estimated return rate range
- SKU complexity score
- Initial capital commitment model
- Estimated inventory turnover days
- Brand concentration (CR3, CR5, CR10)
- Price dispersion
- New product survival rate
- Composite crowding index
"""

import statistics
from typing import Dict, List, Any


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


def _safe_get(data: dict, keys: list, default=""):
    for k in keys:
        if k in data and data[k] is not None:
            return data[k]
    return default


# ============================================================================
# Category historical return rate reference data (based on industry reports and seller experience)
# ============================================================================
CATEGORY_RETURN_RATES = {
    # Apparel, Shoes & Bags
    "clothing": (0.20, 0.40),
    "apparel": (0.20, 0.40),
    "shoes": (0.25, 0.35),
    "footwear": (0.25, 0.35),
    "bag": (0.15, 0.25),
    "handbag": (0.15, 0.25),
    "jewelry": (0.15, 0.30),
    "wig": (0.40, 0.60),
    "swimwear": (0.25, 0.40),
    # Furniture & Appliances
    "furniture": (0.08, 0.15),
    "mattress": (0.10, 0.20),
    "appliance": (0.05, 0.12),
    "bicycle": (0.08, 0.15),
    # Electronics
    "electronic": (0.08, 0.15),
    "phone accessory": (0.10, 0.18),
    # Home
    "home": (0.05, 0.12),
    "kitchen": (0.05, 0.10),
    "organizer": (0.05, 0.10),
    # Outdoor
    "outdoor": (0.08, 0.15),
    "sports": (0.08, 0.15),
    # Beauty
    "beauty": (0.08, 0.15),
    "cosmetic": (0.08, 0.15),
    # Toys
    "toy": (0.08, 0.15),
    # Pets
    "pet": (0.05, 0.10),
    # Automotive
    "automotive": (0.05, 0.12),
    # Office
    "office": (0.05, 0.10),
    "stationery": (0.05, 0.10),
    # Books & Media
    "book": (0.03, 0.08),
    "media": (0.03, 0.08),
    # Default
    "default": (0.08, 0.15),
}


def _detect_category(products: list) -> str:
    """Detect category keywords from products"""
    if not products:
        return "default"

    text = " ".join([
        str(p.get("title", "")).lower()
        for p in products[:5]
    ])

    priority = [
        ("wig", ["wig", "hair extension", "hairpiece"]),
        ("swimwear", ["swimwear", "bikini", "swimsuit"]),
        ("clothing", ["clothing", "apparel", "dress", "shirt", "pants", "jacket", "sweater", "hoodie"]),
        ("shoes", ["shoes", "sneakers", "boots", "sandals", "footwear"]),
        ("bag", ["handbag", "backpack", "luggage", "suitcase", "tote", "purse"]),
        ("jewelry", ["jewelry", "necklace", "ring", "watch", "bracelet"]),
        ("furniture", ["furniture", "sofa", "bed frame", "dresser", "cabinet"]),
        ("mattress", ["mattress", "pillow", "bedding"]),
        ("appliance", ["refrigerator", "washing machine", "microwave", "appliance"]),
        ("bicycle", ["bicycle", "treadmill", "elliptical", "exercise bike"]),
        ("electronic", ["electronic", "charger", "battery", "bluetooth"]),
        ("phone accessory", ["phone case", "screen protector", "charging cable"]),
        ("kitchen", ["kitchen", "cookware", "utensil"]),
        ("organizer", ["organizer", "storage", "container"]),
        ("beauty", ["beauty", "cosmetic", "skincare"]),
        ("toy", ["toy", "game", "puzzle"]),
        ("pet", ["pet", "dog", "cat", "animal"]),
        ("automotive", ["automotive", "car accessory", "auto part"]),
        ("office", ["office", "stationery", "desk"]),
        ("outdoor", ["outdoor", "camping", "hiking"]),
        ("sports", ["sports", "fitness", "gym"]),
        ("book", ["book", "novel", "textbook"]),
        ("media", ["cd", "dvd", "media", "music"]),
    ]

    for cat, kws in priority:
        if any(kw in text for kw in kws):
            return cat

    return "default"


def estimate_inventory_risk(products: list) -> dict:
    """
    Estimate inventory & capital commitment risk

    Returns:
        {
            "category": str,
            "return_rate": (low, high),  # Estimated return rate range
            "sku_complexity": int,  # SKU complexity score (1-10)
            "estimated_investment": (low, high),  # Initial capital commitment (USD)
            "inventory_turnover": (low, high),  # Estimated inventory turnover days
            "risk_level": str,  # "low" | "medium" | "high" | "extreme"
        }
    """
    if not products:
        return {
            "category": "unknown",
            "return_rate": (0.08, 0.15),
            "sku_complexity": 1,
            "estimated_investment": (1000, 3000),
            "inventory_turnover": (60, 90),
            "risk_level": "medium",
        }

    category = _detect_category(products)
    return_rate = CATEGORY_RETURN_RATES.get(category, CATEGORY_RETURN_RATES["default"])

    # SKU complexity: based on variant count and price dispersion
    variation_counts = []
    for p in products[:20]:
        vc = _to_int(p.get("variation_count", 0))
        if vc > 0:
            variation_counts.append(vc)

    avg_variation = statistics.mean(variation_counts) if variation_counts else 1
    if avg_variation > 50:
        sku_complexity = 10
    elif avg_variation > 30:
        sku_complexity = 8
    elif avg_variation > 15:
        sku_complexity = 6
    elif avg_variation > 8:
        sku_complexity = 4
    elif avg_variation > 3:
        sku_complexity = 3
    else:
        sku_complexity = 1

    # Initial capital commitment estimate
    prices = [_to_float(p.get("price", 0)) for p in products[:20] if _to_float(p.get("price", 0)) > 0]
    avg_price = statistics.mean(prices) if prices else 25

    # Assumption: MOQ 100-300 / SKU, cost = 30-50% of selling price
    sku_count_est = max(avg_variation, 5)
    unit_cost_low = avg_price * 0.30
    unit_cost_high = avg_price * 0.50
    moq_low = 100
    moq_high = 300

    invest_low = unit_cost_low * moq_low * sku_count_est
    invest_high = unit_cost_high * moq_high * sku_count_est

    # Inventory turnover days
    if category in ("clothing", "apparel", "shoes", "footwear", "swimwear"):
        turnover = (90, 180)  # Apparel/footwear/bags turn over slowly
    elif category in ("furniture", "mattress", "appliance", "bicycle"):
        turnover = (60, 120)
    elif category in ("electronic", "phone accessory"):
        turnover = (45, 90)
    elif category in ("book", "media", "office", "stationery"):
        turnover = (30, 60)
    else:
        turnover = (45, 90)

    # Composite risk level
    risk_score = 0
    if return_rate[1] > 0.30:
        risk_score += 3
    elif return_rate[1] > 0.15:
        risk_score += 2
    else:
        risk_score += 1

    if sku_complexity >= 6:
        risk_score += 3
    elif sku_complexity >= 4:
        risk_score += 2
    else:
        risk_score += 1

    if invest_high > 50000:
        risk_score += 3
    elif invest_high > 15000:
        risk_score += 2
    else:
        risk_score += 1

    if turnover[1] > 120:
        risk_score += 2
    elif turnover[1] > 90:
        risk_score += 1

    if risk_score >= 9:
        risk_level = "extreme"
    elif risk_score >= 7:
        risk_level = "high"
    elif risk_score >= 4:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "category": category,
        "return_rate": return_rate,
        "sku_complexity": sku_complexity,
        "estimated_investment": (round(invest_low), round(invest_high)),
        "inventory_turnover": turnover,
        "risk_level": risk_level,
    }


def calculate_crowding_index(products: list) -> dict:
    """
    Calculate crowding index

    Returns:
        {
            "brand_cr3": float,  # Top 3 brand concentration
            "brand_cr5": float,
            "brand_cr10": float,
            "price_cv": float,  # Price coefficient of variation (std/mean)
            "price_gini": float,  # Price Gini coefficient
            "newbie_survival": float,  # New product survival rate (listed <6 months & monthly sales >1000)
            "avg_reviews": float,  # Average review count
            "review_median": float,  # Median review count
            "crowding_level": str,  # "low" | "medium" | "high" | "extreme"
        }
    """
    if not products or len(products) < 5:
        return {
            "brand_cr3": 0,
            "brand_cr5": 0,
            "brand_cr10": 0,
            "price_cv": 0,
            "price_gini": 0,
            "newbie_survival": 0,
            "avg_reviews": 0,
            "review_median": 0,
            "crowding_level": "unknown",
        }

    # Brand concentration
    brand_counts = {}
    for p in products:
        brand = _safe_get(p, ["brand", "Brand"], "Unknown")
        brand_counts[brand] = brand_counts.get(brand, 0) + 1

    total = len(products)
    sorted_brands = sorted(brand_counts.values(), reverse=True)

    cr3 = sum(sorted_brands[:3]) / total if total > 0 else 0
    cr5 = sum(sorted_brands[:5]) / total if total > 0 else 0
    cr10 = sum(sorted_brands[:10]) / total if total > 0 else 0

    # Price dispersion
    prices = [_to_float(p.get("price", 0)) for p in products if _to_float(p.get("price", 0)) > 0]
    if len(prices) > 1:
        avg_price = statistics.mean(prices)
        std_price = statistics.stdev(prices)
        price_cv = std_price / avg_price if avg_price > 0 else 0
    else:
        price_cv = 0

    # Price Gini coefficient (simplified)
    if len(prices) > 1:
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        cumsum = 0
        for i, p in enumerate(sorted_prices):
            cumsum += (i + 1) * p
        price_gini = (2 * cumsum) / (n * sum(sorted_prices)) - (n + 1) / n if sum(sorted_prices) > 0 else 0
    else:
        price_gini = 0

    # New product survival rate: listed <6 months (~180 days) & monthly sales >1000
    newbies = []
    for p in products:
        launch_days = _to_int(p.get("launch_days", 999))
        sales = _to_int(p.get("month_sales_volume", p.get("Sales Volume", 0)))
        if launch_days < 180 and sales > 1000:
            newbies.append(p)

    newbie_survival = len(newbies) / total if total > 0 else 0

    # Review statistics
    reviews = [_to_int(p.get("ratings_count", p.get("Review Count", 0))) for p in products]
    avg_reviews = statistics.mean(reviews) if reviews else 0
    review_median = statistics.median(reviews) if reviews else 0

    # Crowding level
    crowding_score = 0
    if cr5 > 0.6:
        crowding_score += 3
    elif cr5 > 0.4:
        crowding_score += 2
    else:
        crowding_score += 1

    if price_cv < 0.2:
        crowding_score += 3  # Highly concentrated prices = price war
    elif price_cv < 0.35:
        crowding_score += 2
    else:
        crowding_score += 1

    if newbie_survival < 0.1:
        crowding_score += 3  # New products barely survive
    elif newbie_survival < 0.2:
        crowding_score += 2
    else:
        crowding_score += 1

    if avg_reviews > 5000:
        crowding_score += 2  # Very high average reviews = listing monopoly
    elif avg_reviews > 2000:
        crowding_score += 1

    if crowding_score >= 9:
        crowding_level = "extreme"
    elif crowding_score >= 7:
        crowding_level = "high"
    elif crowding_score >= 4:
        crowding_level = "medium"
    else:
        crowding_level = "low"

    return {
        "brand_cr3": round(cr3, 2),
        "brand_cr5": round(cr5, 2),
        "brand_cr10": round(cr10, 2),
        "price_cv": round(price_cv, 2),
        "price_gini": round(price_gini, 2),
        "newbie_survival": round(newbie_survival, 2),
        "avg_reviews": round(avg_reviews, 0),
        "review_median": round(review_median, 0),
        "crowding_level": crowding_level,
    }


def format_risk_summary(inventory_risk: dict, crowding: dict, profile_name: str = "newbie") -> str:
    """Format risk quantification summary table"""
    level_emoji = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🔴",
        "extreme": "🚨",
        "unknown": "⚪",
    }

    inv = inventory_risk
    cr = crowding

    return_rate = inv.get("return_rate", (0.08, 0.15))
    investment = inv.get("estimated_investment", (1000, 3000))
    turnover = inv.get("inventory_turnover", (45, 90))

    lines = [
        "### Risk Quantification Summary",
        "",
        "| Metric | This Category | Safe Threshold | Status |",
        "|--------|---------------|----------------|--------|",
    ]

    # Return rate
    rr_high = return_rate[1] * 100
    rr_emoji = "🔴" if rr_high > 25 else "🟡" if rr_high > 15 else "🟢"
    lines.append(f"| Est. Return Rate | {return_rate[0]*100:.0f}%-{rr_high:.0f}% | <15% | {rr_emoji} {'High' if rr_high > 15 else 'Normal'} |")

    # Initial capital
    inv_high = investment[1]
    inv_emoji = "🔴" if inv_high > 30000 else "🟡" if inv_high > 10000 else "🟢"
    lines.append(f"| Initial Capital | ${investment[0]:,}-${inv_high:,} | <$5,000 | {inv_emoji} {'High' if inv_high > 10000 else 'Normal'} |")

    # Inventory turnover
    turn_high = turnover[1]
    turn_emoji = "🔴" if turn_high > 120 else "🟡" if turn_high > 90 else "🟢"
    lines.append(f"| Inventory Turnover Days | {turnover[0]}-{turn_high} days | <90 days | {turn_emoji} {'Slow' if turn_high > 90 else 'Normal'} |")

    # Brand concentration
    cr5 = cr.get("brand_cr5", 0)
    cr_emoji = "🔴" if cr5 > 0.6 else "🟡" if cr5 > 0.4 else "🟢"
    lines.append(f"| Brand Concentration (CR5) | {cr5*100:.0f}% | <50% | {cr_emoji} {'High' if cr5 > 0.4 else 'Normal'} |")

    # New product survival rate
    survival = cr.get("newbie_survival", 0)
    surv_emoji = "🔴" if survival < 0.15 else "🟡" if survival < 0.25 else "🟢"
    lines.append(f"| New Product Survival Rate | {survival*100:.0f}% | >25% | {surv_emoji} {'Low' if survival < 0.25 else 'Normal'} |")

    # Price dispersion
    price_cv = cr.get("price_cv", 0)
    price_emoji = "🔴" if price_cv < 0.2 else "🟡" if price_cv < 0.3 else "🟢"
    lines.append(f"| Price Dispersion (CV) | {price_cv:.2f} | >0.3 | {price_emoji} {'Low (Price War)' if price_cv < 0.3 else 'Normal'} |")

    lines.append("")

    # Overall assessment
    inv_level = inv.get("risk_level", "medium")
    crowd_level = cr.get("crowding_level", "medium")

    if inv_level in ("high", "extreme") or crowd_level in ("high", "extreme"):
        lines.append(f"> **Overall Assessment**: {level_emoji.get(inv_level, '🟡')} Inventory Risk {inv_level.upper()} + {level_emoji.get(crowd_level, '🟡')} Crowding {crowd_level.upper()}")
        if profile_name in ("newbie", "grower"):
            lines.append(f"> 💡 Current profile is **{profile_name}**, category risk exceeds recommended range. To view full analysis, try `--profile pro` or `--profile factory`.")
    else:
        lines.append(f"> **Overall Assessment**: {level_emoji.get(inv_level, '🟢')} Inventory Risk {inv_level.upper()} + {level_emoji.get(crowd_level, '🟢')} Crowding {crowd_level.upper()} — Manageable.")

    lines.append("")
    return "\n".join(lines)
