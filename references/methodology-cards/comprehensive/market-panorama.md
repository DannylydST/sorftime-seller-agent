# Market Panorama Analysis

> Type: Comprehensive | Seller Stage: All | Platform: Amazon / Walmart / Shopee

## Core Logic

Whether a category is worth entering is not determined by a single metric (e.g., high sales volume or low competition). It is evaluated across 11 weighted dimensions producing a composite score -- the top-ranking categories are not necessarily the highest in volume, but they are the "most efficient battleground" in terms of ROI.

## Methodology Principles

Traditional product research tools rely on "hard-threshold filtering": only show products with monthly sales > 300, price > $15, rating > 4.0. This approach has fatal flaws:

- **Cliff-edge elimination of boundary products**: A product with 280 monthly sales but extremely high margins and ultra-low competition gets excluded outright by the hard threshold -- the seller never sees it.
- **Dimensions are not weightable**: All conditions are AND-connected. There is no way to express a trade-off like "slightly lower sales but far better competition."
- **High manual trial-and-error cost**: Every threshold adjustment requires a full re-run with no directional guidance on which way to tune.

Sorftime's full-ranking approach is fundamentally different -- **every product/subcategory receives a composite index score, ranked and visible, with no hard cutoff**:

```
Composite Score = w₁ x Market Size Score + w₂ x Growth Trend Score + w₃ x Competition Intensity Score
                + w₄ x Price Ceiling Score + w₅ x Brand Concentration Score + w₆ x Seasonality Score
                + w₇ x Review Barrier Score + w₈ x Return Rate Score + w₉ x Logistics Fit Score
                + w₁₀ x Ad Cost Score + w₁₁ x Compliance Risk Score
```

- Weights w₁-w₁₁ are dynamically adjusted by seller stage: Beginners emphasize Competition Intensity (w₃); Professional sellers emphasize Ad Cost (w₁₀).
- The Composite Score is a continuous 0-100 value. No product disappears because it "fell below some threshold."
- A category with extremely low competition but modest market size will still rank high -- the seller decides whether to accept the trade-off.

## Trigger Scenarios

- "Can you analyze whether this category is worth entering?"
- "Analyze the pet supplies niche for me"
- "Compare Home vs. Kitchen -- which is easier to break into?"
- "I want to find categories with low competition but decent volume"

## Conversational Execution (agent-x / MCP Channel)

### Step 1: Full Pull --> Index Ranking
```bash
python3 scripts/picker.py --mode category-report --keyword "pet supplies" \
  --domain 1 --sort-by composite_score
```
Use CategoryReport as the primary data source. No hard-threshold filtering. All 11 dimensions returned, composite ranking fully visible.

### Step 2: Deep Dive into Top Categories
```bash
python3 scripts/analyst.py --mode category-trend --category "Pet Supplies"
python3 scripts/analyst.py --mode product-search --keyword "Pet Supplies" \
  --sort-by review_speed
```
Use CategoryTrend ⭐ to view 12-month trajectories of sales volume, price, and review count.
Use ProductSearch to check review velocity of TOP products (identify breakout incubation windows).

### Step 3: Cross-Validation
- Use ProductRequest to pull pricing ranges and FBA fees of leading products, validating the price-ceiling assessment.
- Brand concentration (CR4/CR8) requires a separate query: what share do the top 4 brands hold? > 40% = brand-moat market; new entrants need a differentiated wedge.

## Interpretation Framework

1. **Common traits of top-ranking categories**: Look for overlapping characteristics -- are they clustered in a certain price band? Do they all target a specific use case? Do they all have brand backing? These traits are the "entry ticket."

2. **"Grey Zone" categories** (Hidden Goldmines ⭐): A category with a middling composite rank (30-50) but extremely high Competition Intensity score (meaning competition is very low) and extremely high Price Ceiling score -- in a hard-threshold system, this category would be filtered out because "monthly sales aren't high enough." Full-ranking lets the seller see these "unbalanced overachievers."

3. **Risk signals**:
   - Negative Growth Trend score + High Review Barrier score = Declining market. Not recommended.
   - Brand Concentration > 50% + Review Barrier > 1000 = Monopolistic market. Not viable without disruptive differentiation.
   - Seasonality score > 80 = Peak-season-driven shipments and peak-season-driven competition. Beginners easily fall into inventory traps.

## Risk Notes

- The Composite Score depends on weight settings. Beginner default weights favor "low competition," potentially missing high-competition, high-reward categories.
- CategoryReport data refreshes monthly. Sudden changes within the month (e.g., policy shocks, black-swan events) may not be reflected.
- Cross-border e-commerce policy changes (tariffs, compliance requirements) are not directly captured in the 11 dimensions and must be monitored separately.

## Workflow Chain

This Card --> Competitor Deep Dive (validate composite assessment) --> Keyword Strategy Optimization (build the entry plan)

Typical flow: Top categories surfaced by Market Panorama --> Competitor Deep Dive to identify leading players' weaknesses --> Keyword Strategy to target long-tail keywords for market entry.
