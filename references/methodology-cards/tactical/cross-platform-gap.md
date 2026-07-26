# Cross-Platform Price Gap Arbitrage

> Category: Tactical Strategy | Seller Stage: Professional | Platform: Amazon + Walmart

## Core Logic

Identical or highly similar products exhibit systematic pricing differences between Amazon and Walmart → leverage Sorftime's exclusive dual-platform data to identify price gap opportunities — source from the lower-priced platform, sell on the higher-priced platform.

## Methodology Principles

**Sorftime Exclusive Capability**: the only service provider in the industry with structured data from both Amazon and Walmart simultaneously. No other tool can offer cross-platform comparable product pricing analysis.

Hard-threshold filtering's approach is `price_gap_pct >= 20%` — find "products where Amazon price exceeds Walmart price by more than 20%." This absolute-value filter (hard threshold) misses two important opportunity types: first, low-price products with large percentage gaps but small absolute profit (Amazon $8 vs Walmart $6, 25% gap rate but only $2 per-unit profit); second, high-price products with seemingly modest gap rates (Amazon $89 vs Walmart $69, 22% gap rate but $20 per-unit profit). More critically, hard-threshold filtering completely ignores cross-platform fulfillment feasibility and demand disparity — a product with 200 monthly sales on Amazon but only 5 monthly sales on Walmart has zero conversion value even at a 50% price gap.

**Cross-Platform Price Gap Index** = Price Gap Percentage x Sales-Weighted (Amazon Monthly Sales + Walmart Monthly Sales) x Cross-Platform Fulfillment Feasibility Coefficient. Only full-ranking can push "gap of $15 + stable sales on both platforms" ahead of "gap rate of 40% but 0 Walmart monthly sales."

## Trigger Phrases

- "What sells well on Walmart but is expensive on Amazon"
- "Find cross-platform margin gaps"
- "How much does this product sell for on Walmart"
- "Which platform has better margins — Amazon or Walmart"

## Execution Steps

### Conversational Mode (agent-x)

```
Step 1: Amazon ProductSearch to get category price distribution → anchor price gap baseline
        Simultaneously pull Walmart CategoryRequest for the same classification
        Calculate Cross-Platform Price Gap Index for each ASIN

Step 2: Take the Top 20 → ProductDetail (Amazon) +
        walmart_product_detail_by_product_id (Walmart) cross-verify product similarity
        Exclude: brand-exclusive products, products with clearly different sizes/packaging

Step 3: Feasibility verification:
        - Amazon-side Buy Box competitive landscape
        - Walmart-side fulfillment options (WFS/FBM)
        - Cross-border logistics costs to both FBA and WFS warehouses (costs vary by origin country)
```

## Interpretation Guidelines

1. **Characteristics of price-gap products**: Amazon brand premium is more pronounced (large brand-vs-unbranded gap), Walmart's pricing for impulse-consumption categories is more flexible, Amazon Prime's shipping-cost perception makes buyers less price-sensitive.
2. **The grey-zone sweet spot**: products with a moderate gap rate of 8-15% — hard-threshold filtering deems this "not enough," but in high-price categories (> $50), a 10% gap means significant absolute profit headroom.
3. **Walmart volume potential assessment**: low Walmart monthly sales are not necessarily bad — Walmart.com's overall traffic is growing rapidly. Sellers who position early enjoy the platform's growth dividend.
4. **Category selection preference**: standard / small-and-light items > bulky / irregularly-shaped items (lower dual-platform logistics management cost).

## Risk Warnings

- **Product similarity misjudgment**: products that look identical on Amazon and Walmart may come from different suppliers with vastly different sourcing costs. Must verify supply chain uniformity.
- **Platform policy divergence**: Walmart's pricing algorithm adjusts dynamically — a discovered price gap may be eaten by Walmart's automatic repricing, nullifying the arbitrage window.
- **Dual-line inventory management cost**: inventory must be held separately on each platform, increasing capital tie-up and dead-stock risk.
- **Brand exclusivity constraints**: some brands only sell on Amazon; Walmart's brand onboarding policies differ.

## Combo Playbook

This Strategy → Price Band Sweet Spot (verify whether the cross-platform price gap falls within each platform's sweet spot range) → FBM to FBA Conversion (use WFS on the Walmart side for fulfillment advantage) → Variant Gap Discovery (identify missing variant combinations in a cross-platform context to raise barriers)
