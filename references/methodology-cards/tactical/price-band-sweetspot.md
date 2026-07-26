# Price Band Sweet Spot

> Category: Tactical Strategy | Seller Stage: Growing+ | Platform: Amazon / Walmart / Shopee

## Core Logic

Within every category, a specific price range exists — too low means thin margins and a red ocean, too high means demand drops off a cliff → identify the price band with the highest demand density and lowest competition density as your entry starting point.

## Methodology Principles

Hard-threshold filtering's approach is "find products priced between $15-$25" — this rigid bucketing logic completely ignores category-specific characteristics and competitive structure differences. For example: in the power bank category, the $15-$20 price band concentrates 60% of ASINs but contributes only 35% of total sales (red ocean within a red ocean), while $25-$30 has only 15% of ASINs yet contributes 25% of sales (a blue-ocean tail). Hard-threshold filtering would directly recommend $15-$20, but the Price Band Opportunity Index would rank $25-$30 higher. Another example: the $10-$12 band appears to have moderate competition, but if the category's core customer base is highly price-sensitive, $10 generates 5x the sales volume of $12 — hard-threshold filtering cannot perceive this "price-elasticity cliff."

**Price Band Opportunity Index** = Demand Density in each price band / Competitor Density in that band. Demand density is estimated via total sales volume / total search volume within the price range; competitor density is measured by the number of active ASINs in that band. Only full-ranking can push "high-demand bands you haven't noticed" ahead of "bands that look busy but whose margins have been competed away."

## Trigger Phrases

- "What price should I set for this category"
- "Find price range opportunities"
- "Which price segment has low competition and high demand"
- "Is there still opportunity in this price range"

## Execution Steps

### Conversational Mode (agent-x)

```
Step 1: CategoryReport to obtain category price distribution
        - Full ASIN pool bucketed by $5 or $10 increments
        - For each price bucket, tally: ASIN count, total sales, total revenue, average rating
        Sort by: Price Band Opportunity Index descending

Step 2: Take the Top 3 price bands → ProductSearch deep-dive into each band:
        - Product profile of Top 10 ASINs (branded/unbranded ratio)
        - Review distribution of Top 10 ASINs (review moat height)
        - Variant strategy of Top 10 ASINs

Step 3: Profit verification:
        - Estimate FBA fees and sourcing cost at the sweet-spot price point
        - Calculate gross margin rate (ensure > 30%)
        - Check whether major brands occupy that price band
```

## Interpretation Guidelines

1. **Common traits of sweet-spot pricing**: the band's average ASIN review count is significantly lower than adjacent bands (indicating greater new-entrant opportunity), the degree of branding is moderate (some room for unbranded players), sales distribution is relatively even (no single dominant player).
2. **The grey-zone sweet spot**: category median price is $18, but the $22-$28 band has very few ASINs — the gap between demand and supply. Hard-threshold filtering will never tell you "why the price band everyone avoids is actually a blue ocean."
3. **Multi-platform sweet-spot divergence**: Amazon's sweet spot skews mid-to-high price (consumers are accustomed to the Prime premium); Walmart's sweet spot skews mid-to-low price (Walmart's brand positioning); Shopee's sweet spot is the lowest (Southeast Asia has the highest price sensitivity). Cross-platform sellers using Sorftime's cross-platform data can observe these differences.
4. **Price-elasticity cliffs**: some categories have a clear demand cliff at a certain price point (e.g., $19.99 to $24.99, sales drop 40%) — these cliff points are often systemic cutoffs caused by cost ceilings (FBA fee tiers, tariff thresholds, etc.).

## Risk Warnings

- **Price bands are dynamic**: the sweet spot discovered today may be flooded by new entrants within 3 months. Recommend re-running the analysis every 30 days.
- **High demand does not equal high margin**: a price band with high demand density may also carry high FBA fees (e.g., oversized items), potentially resulting in negative margins.
- **FBA fee tier traps**: Amazon FBA fees have cliff-like jumps at certain size/weight tier boundaries — pricing at $19.99 that just triggers a higher fee tier may yield lower actual profit than $17.99.
- **Brand blocking risk**: certain price bands are occupied by major brands using a low-spec, low-price product line as a blocker. Independent sellers at the same price point will be crushed by the brand premium.

## Combo Playbook

This Strategy → Variant Gap Discovery (fill missing variants within the sweet-spot price band) → Listing Optimization (optimize overlooked listings in the sweet-spot price band) → FBM to FBA Conversion (FBM sellers' products inside the sweet spot have the highest conversion value)
