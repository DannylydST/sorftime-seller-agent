# New Product Burst Tracking

> Category: Tactical Strategy | Seller Stage: Growing+ | Platform: Amazon

## Core Logic

Recently launched products with sales growth rates significantly outpacing category peers → decode their success factors (pricing, keywords, review strategy, ad tactics), and rapidly replicate or differentiate to follow.

## Methodology Principles

Hard-threshold filtering's approach is "ASINs launched within 30 days with monthly sales > 200" — this rigid cutoff misses enormous numbers of high-potential new products. For example: a product launched only 7 days ago averaging 15 orders/day versus one launched 28 days ago averaging 7 orders/day. Hard-threshold filtering looks only at monthly sales (105 vs 196) and ranks the latter higher, but the former's burst acceleration is 6x stronger (2.14 orders/day-day vs 0.25 orders/day-day). Another extreme: a product with 1,000 monthly sales that launched 200 days ago — hard-threshold filtering still labels it "high sales" and recommends it, but it is already mature with a flattened growth curve.

**New Product Burst Index** = Sales / Days Since Launch x Growth Acceleration (i.e., Recent Daily Sales / Early Daily Sales). In essence, it is normalized per-unit-time output multiplied by the growth slope. Only full-ranking ensures a "7-day burst star" ranks ahead of a "28-day steady climber."

## Trigger Phrases

- "What new products have appeared in this category recently"
- "Any breakout seedlings"
- "Check out competitors' newly launched products"
- "What's the new launch landscape in this category over the last three months"

## Execution Steps

### Conversational Mode (agent-x)

```
Step 1: ProductSearch filtered by launch date range (within 30 days / 60 days / 90 days)
        Sort by: New Product Burst Index descending
        Filter: exclude ASINs with monthly sales < 10 (eliminate zero-sales noise)

Step 2: Take the Top 15 → ProductDetail analyze one by one:
        - Pricing strategy (undercutting to drive volume?)
        - Review count and acquisition velocity (Vine/organic review ratio)
        - Main image quality, title keyword density
        - FBA/FBM choice

Step 3: Trend verification → AsinSalesVolume pull daily sales trend
        Check: is the growth curve healthy (organic growth vs. ad-driven)
```

## Interpretation Guidelines

1. **Common traits of top new products**: pricing typically falls within the category's Price Band Sweet Spot range, main image CTR significantly above category average, broad and precise keyword coverage.
2. **The grey-zone sweet spot**: medium-pace new products launched 30-45 days ago with monthly sales of 50-150 — hard-threshold filtering deems them "unqualified," but the Burst Index identifies that these products are in their acceleration ramp-up phase — the optimal moment to enter and follow.
3. **Burst pattern identification**: distinguish "organic burst" (steady review growth rate, high long-tail keyword traffic share) from "ad-driven burst" (mainly brand keywords, high ACOS) — the former is sustainable, the latter is not.
4. **Beware of false bursts**: product data from launches during major sales events (Prime Day / Black Friday) is distorted. Exclude major event windows.

## Risk Warnings

- **Peak at launch, then decline**: some new products manufacture a short-lived burst via deep discounts or off-Amazon traffic. Sales cliff-dive once the promotional period ends. Use AsinSalesVolume to check trends, not just first-month data.
- **Follow-play timing window**: the new product burst window is roughly 30-60 days. Past that, competitor review moats solidify and follow-play cost rises dramatically.
- **Category specificity**: for highly seasonal products or those with short product lifecycles (e.g., holiday decorations), the New Product Burst Index needs to be calibrated with a seasonal factor.

## Combo Playbook

This Strategy → Variant Gap Discovery (check what variants the top new product is missing) → Listing Optimization (evaluate whether the new product's listing quality has optimization headroom) → Price Band Sweet Spot (verify whether the new product's pricing falls within the sweet spot)
