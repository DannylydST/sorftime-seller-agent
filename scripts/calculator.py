#!/usr/bin/env python3
"""
Profit Calculator — Quick estimate of gross margin and break-even across platforms
From the seller's perspective: not just calculate profit, but also flag risks, break-even thresholds, and cost sensitivity
"""

import argparse


def calc_amazon_fba(price: float, cost: float, weight_kg: float, platform_fee_rate: float = 0.15) -> dict:
    """Amazon FBA profit estimate (with risk alerts and sensitivity analysis)"""
    # FBA fulfillment fee rough estimate: $2.5/kg + $3.5 base
    fba_fee = max(3.5, weight_kg * 2.5 + 1.5)
    platform_fee = price * platform_fee_rate
    ad_cost = price * 0.15  # Assuming 15% ad spend
    total_cost = cost + fba_fee + platform_fee + ad_cost
    profit = price - total_cost
    margin = (profit / price) * 100 if price else 0

    # Break-even daily sales volume
    fixed_monthly = 0  # Simplified model, assuming no fixed monthly fees
    breakeven_daily = _breakeven_daily(profit)

    # Return rate sensitivity analysis (returns eat profit + ~$2-5 return processing fee per unit)
    return_impact = _return_sensitivity(profit, price, fba_fee)

    return {
        "Selling Price": f"${price:.2f}",
        "Product Cost": f"${cost:.2f}",
        "FBA Fee (Est.)": f"${fba_fee:.2f}",
        "Referral Fee (15%)": f"${platform_fee:.2f}",
        "Ad Cost (15%)": f"${ad_cost:.2f}",
        "Total Cost": f"${total_cost:.2f}",
        "Net Profit per Unit": f"${profit:.2f}",
        "Gross Margin": f"{margin:.1f}%",
        "Break-Even Daily Sales": breakeven_daily,
        "Return Rate Profit Erosion": return_impact,
        "Overall Recommendation": _suggest(margin) + " | " + _fba_warning(weight_kg),
    }


def calc_tiktok(price: float, cost: float) -> dict:
    platform_fee = price * 0.05
    ad_cost = price * 0.20
    total = cost + platform_fee + ad_cost
    profit = price - total
    margin = (profit / price) * 100 if price else 0
    breakeven_daily = _breakeven_daily(profit)

    return {
        "Selling Price": f"${price:.2f}",
        "Product Cost": f"${cost:.2f}",
        "Referral Fee (5%)": f"${platform_fee:.2f}",
        "Ad/Influencer Cost (20%)": f"${ad_cost:.2f}",
        "Net Profit per Unit": f"${profit:.2f}",
        "Gross Margin": f"{margin:.1f}%",
        "Break-Even Daily Sales": breakeven_daily,
        "Overall Recommendation": _suggest(margin) + " | TikTok requires heavy product testing + short video/influencer content costs",
    }


def calc_temu(price: float, cost: float) -> dict:
    deduction = price * 0.30
    profit = price - cost - deduction
    margin = (profit / price) * 100 if price else 0
    breakeven_daily = _breakeven_daily(profit)

    return {
        "Selling Price": f"${price:.2f}",
        "Product Cost": f"${cost:.2f}",
        "Platform + Logistics Deduction (Est. 30%)": f"${deduction:.2f}",
        "Net Profit per Unit": f"${profit:.2f}",
        "Gross Margin": f"{margin:.1f}%",
        "Break-Even Daily Sales": breakeven_daily,
        "Overall Recommendation": _suggest(margin) + " | TEMU's actual payout after price review is often lower — use final settlement price.",
    }


def calc_shopee(price: float, cost: float) -> dict:
    # Shopee commission + transaction fee ~5-8%, logistics markup complex — simplified
    platform_fee = price * 0.07
    logistics = price * 0.15  # Logistics markup ~10-20%
    ad_cost = price * 0.08
    total = cost + platform_fee + logistics + ad_cost
    profit = price - total
    margin = (profit / price) * 100 if price else 0
    breakeven_daily = _breakeven_daily(profit)

    return {
        "Selling Price": f"${price:.2f}",
        "Product Cost": f"${cost:.2f}",
        "Referral Fee (7%)": f"${platform_fee:.2f}",
        "Logistics (Est. 15%)": f"${logistics:.2f}",
        "Ad Cost (8%)": f"${ad_cost:.2f}",
        "Net Profit per Unit": f"${profit:.2f}",
        "Gross Margin": f"{margin:.1f}%",
        "Break-Even Daily Sales": breakeven_daily,
        "Overall Recommendation": _suggest(margin) + " | Shopee commission & logistics vary significantly by site — verify with official rates.",
    }


def calc_walmart(price: float, cost: float, weight_kg: float) -> dict:
    # Walmart referral fee 15%, WFS fees similar to FBA
    platform_fee = price * 0.15
    wfs_fee = max(3.5, weight_kg * 2.5 + 1.5)
    ad_cost = price * 0.12
    total = cost + platform_fee + wfs_fee + ad_cost
    profit = price - total
    margin = (profit / price) * 100 if price else 0
    breakeven_daily = _breakeven_daily(profit)

    return {
        "Selling Price": f"${price:.2f}",
        "Product Cost": f"${cost:.2f}",
        "WFS Fee (Est.)": f"${wfs_fee:.2f}",
        "Referral Fee (15%)": f"${platform_fee:.2f}",
        "Ad Cost (12%)": f"${ad_cost:.2f}",
        "Net Profit per Unit": f"${profit:.2f}",
        "Gross Margin": f"{margin:.1f}%",
        "Break-Even Daily Sales": breakeven_daily,
        "Overall Recommendation": _suggest(margin) + " | " + _fba_warning(weight_kg).replace("FBA", "WFS"),
    }


def _breakeven_daily(profit_per_unit: float) -> str:
    """Rough break-even daily sales estimate based on $500/mo fixed costs"""
    if profit_per_unit <= 0:
        return "Cannot break even (loss per unit)"
    monthly_units = 500 / profit_per_unit
    daily_units = monthly_units / 30
    return f"~{daily_units:.1f} units/day (based on $500/mo fixed costs)"


def _return_sensitivity(profit: float, price: float, fba_fee: float) -> str:
    """Calculate how different return rates erode net profit"""
    # Rough model: each return costs = profit + return processing fee (~$3.5)
    loss_per_return = profit + 3.5
    if profit <= 0:
        return "Product already at a loss — returns will amplify losses"

    lines = []
    for rate in (0.03, 0.05, 0.10):
        effective_profit = profit - (loss_per_return * rate)
        effective_margin = (effective_profit / price) * 100
        flag = "⚠️" if effective_margin < 10 else ""
        lines.append(f"Return rate {rate*100:.0f}% → Effective net profit ${effective_profit:.2f}/unit ({effective_margin:.1f}%) {flag}")
    return "; ".join(lines)


def _suggest(margin: float) -> str:
    if margin >= 30:
        return "Strong profit — worth pursuing"
    elif margin >= 18:
        return "Moderate profit — control ad spend and return rate"
    elif margin >= 10:
        return "Thin margin — optimize costs or increase price"
    else:
        return "Margin too low — not recommended"


def _fba_warning(weight_kg: float) -> str:
    return f"FBA fee is weight-based estimate ({weight_kg}kg). Verify with exact dimensional weight from product detail."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", default="amazon", choices=["amazon", "tiktok", "shopee", "temu", "walmart"])
    parser.add_argument("--price", type=float, required=True)
    parser.add_argument("--cost", type=float, required=True)
    parser.add_argument("--weight", type=float, default=0.5, help="Weight (kg), used for Amazon/Walmart FBA/WFS estimate")
    args = parser.parse_args()

    if args.platform == "amazon":
        result = calc_amazon_fba(args.price, args.cost, args.weight)
    elif args.platform == "tiktok":
        result = calc_tiktok(args.price, args.cost)
    elif args.platform == "temu":
        result = calc_temu(args.price, args.cost)
    elif args.platform == "shopee":
        result = calc_shopee(args.price, args.cost)
    elif args.platform == "walmart":
        result = calc_walmart(args.price, args.cost, args.weight)
    else:
        result = calc_amazon_fba(args.price, args.cost, args.weight)

    print(f"# {args.platform.upper()} Profit Estimate")
    print()
    for k, v in result.items():
        print(f"- **{k}**: {v}")


if __name__ == "__main__":
    main()
