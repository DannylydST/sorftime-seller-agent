# Pricing Position Analysis

> Category: Comprehensive | Seller Stage: Beginner/Growing/Professional | Platform: Amazon / Walmart / Shopee

## Core Logic

Locate the optimal pricing window by ranking price bands with a Price Band Opportunity Score — find the range where "sales density is high but competitor density is low," rather than guessing an absolute price by intuition.

## Methodology Principles

**Core Differentiation: Price Band Opportunity Score ranking, not "price range filtering."** The most common competitor tool approach is having the user manually set a price range — "show me $15-25 products" — and then analyzing within that range. This has two problems: (1) the user doesn't know which range has the most opportunity, wasting trial-and-error cost; (2) boundary products ($14.99 or $25.01) are outright excluded, even though these boundary products may actually be the top-selling "position-holding products." Sorftime's approach uses full-spectrum data ranked by Price Band Opportunity Score:
```
Price Band Opportunity Score = Sales Share of the Band ÷ ASIN Density of the Band × Profit Buffer Coefficient
```
Each price band is scored independently. **$14.99 doesn't disappear because it's one cent off** — it scores in the $10-15 band, and $15.01 scores in the $15-20 band. Both are included in the comparison; they simply belong to different segments.

**Sorftime Exclusive Advantage:** `ProductSearch` supports batch retrieval of product sales estimates and price distributions by category + price band. `CategoryReport` directly returns category-level price-sales matrices. Together, these two endpoints can precisely calculate the "blue-ocean index" for each price band. Competitors typically either cannot obtain price distribution data at all, or can only produce rough estimates.

**Comparison with Industry Practice:** Most tools require you to first input a price range ($15-30), then analyze within that range — this inherently limits your field of view. You never learn whether $30-45 has a competitive vacuum. Sorftime imposes no preset; after full-band sorting, you'll naturally notice in the list: "Wait — the $30-35 band only has 5 ASINs but combined monthly sales exceed 3,000."

## Trigger Phrases

- "What's the right price for this category"
- "Show me which price range has the least competition"
- "I want to launch a new product in this category — what price gives the best advantage"
- "Is our current pricing reasonable"

## Conversation Mode Execution (agent-x / MCP Channel)

### Step 1: Full-Spectrum Pull → Index Ranking
No hard-threshold filtering. Call `ProductSearch` to pull the full product list by category, covering the entire price range. Apply no price range preset — let the data speak for itself. Rank each $5 or $10 price band by Price Band Opportunity Score:
```
Opportunity Score = Average Monthly Sales in the Band ÷ Number of ASINs in the Band × (1 - Average Review Count in the Band / 1000)
```
**Price bands with extremely low sales are not automatically discarded** — e.g., a $100+ premium band may have only 500 total sales, but with only 3 ASINs, the average sales per ASIN is actually quite high, and the Opportunity Score is not necessarily low. A hard-threshold system that says "skip any band with < 1000 sales" would simply miss the premium niche market.

### Step 2: Top N Deep Analysis
Take the top 5 price bands by Opportunity Score and call `CategoryReport` to get detailed data for each band within the category:
- Top ASINs in the band and their pricing strategies
- Historical trends for the band (3/6/12-month price-center shifts)
- Average review count distribution for products in the band (review threshold = entry barrier)
- Profit simulation: estimated net margin after deducting Amazon referral fees + FBA fees + sourcing costs
- Output a "Recommended Pricing Window" (suggested price range + expected competitive landscape)

### Step 3: Cross-Validation
Call `ProductDetail` to inspect the product configurations of the Top 10 ASINs in the highest-opportunity price band (feature differences, color/size distribution). Confirm: can your planned product configuration run a viable profit model in this price band? If the Top 10 are all established brand products, even a high Opportunity Score requires strategic adjustment (differentiation rather than head-on competition).

## Results Interpretation Framework

1. **Common Traits of Top-Ranked Items:** Price bands with Opportunity Score > 0.8 are typically mid-tier bands — not the cheapest (most intense competition), not the most expensive (low sales ceiling), but a narrow sweet spot slightly above the middle, characterized by high sales density with moderate ASIN density.
2. **"Gray Zone" Products:** Price bands with Opportunity Score 0.4-0.6 but extremely low ASIN density (< 10 ASINs) — hard-threshold systems would ignore these due to "low total sales," but these bands often sit in a category blind spot: no one sells at this price point, not because demand is absent, but because no one has discovered it. **Whoever enters first with reasonable listing quality can capture the head position in the price band at low cost.**
3. **Price Collapse Warning:** A price band's average selling price dropping more than 15% over 6 months — this band is being eroded by a price war. New entrants' profit margins will compress rapidly. Even if the current Opportunity Score isn't low, adjacent price bands should be prioritized.

## Risk Notes

- Price Band Opportunity Score is a snapshot metric — if a large number of new ASINs flood into the band in the short term, the Opportunity Score will quickly dilute
- Fluctuations in sourcing costs (exchange rates, raw materials) directly affect profit simulation accuracy; requires periodic re-runs
- Amazon FBA fee adjustments affect profit structure differently across price bands — referral fee percentages differ below and above $10
- Brand effects: in price bands with high brand concentration, even a high Opportunity Score may not translate to actual conversion rates for unbranded products, which may be far below estimates
- Price band weightings fluctuate periodically rather than remaining fixed — the price center shifts as a whole around Amazon algorithm update windows and major promotions (Prime Day, Black Friday); promotional-season analysis conclusions are only valid within that window
- Walmart and Amazon have different price band distribution logic — Walmart users are more price-sensitive; the optimal price band is typically 10-15% lower than the equivalent Amazon category

## Composable Pipelines

[Review Mining & Pain Point Extraction](/review-mining.md) → This Card → Confirm whether pricing can support the cost of product improvements → [Traffic Structure Analysis](/traffic-structure.md) to analyze traffic acquisition efficiency differences across ASINs at different price points
