# Hidden Profit Index (HPI) Mining ⭐ (Sorftime Exclusive Methodology)

> Category: Tactical Strategy | Seller Stage: Beginner+ | Platform: Amazon
> **Sorftime's proprietary recommendation engine — not a transparency tool.**

## Core Logic

**What HPI is**: A composite recommendation score (relative value) that ranks products by their "hidden profit potential" — how likely a product is to deliver strong margins with low entry barriers, low ad competition, and manageable review thresholds. Higher score = better overall profile across these dimensions.

**What HPI is NOT**: A per-dimension breakdown calculator. Sellers don't need to compute individual sub-scores. The value of HPI is the **composite signal** — it surfaces products that traditional single-dimension filtering (price ≥ X, reviews ≤ Y) would miss entirely.

Leverage Sorftime's exclusive Product Potential Index to mine the **full dataset** for product opportunities that get eliminated by traditional filtering rules but carry exceptionally high hidden profit potential.

## Methodology

**Key Distinction: Full-Ranking vs Hard-Threshold Filtering**

Traditional product selection uses absolute hard thresholds as filters:
```
minPrice >= $20  AND  minRating >= 3.5  AND  monthlySales >= 300
```
A product priced at $18.99, with 800 monthly sales and a 4.6 rating gets outright eliminated — because it "doesn't meet the price threshold." This discrete judgment locks out a large number of borderline good products.

Sorftime's **Product Potential Index ⭐** uses a full-ranking approach:
```
Full Ranking = Price Score (20%) + Rating Score (15%) + Sales Score (30%) + Profit Score (varies %)
```
Every product scores on every dimension — the scores just differ in magnitude. A $18.99 product simply scores "slightly lower on the price dimension," but if its sales score is stellar and profit score outstanding, its composite rank can still land in the top 10. **No product gets discarded because a single dimension falls below a threshold.**

The **Hidden Profit Index (HPI)** specifically refers to those "Edge Dark Horse" products that rank high in the composite sort but would absolutely have been filtered out by traditional hard thresholds.

## Trigger Phrases
- "Help me find undervalued product opportunities"
- "What products have others overlooked?"
- "Blue ocean product recommendations"
- "What products have a high Hidden Profit Index?"

## Execution Steps

### Conversation Mode (agent-x)
```
Step 1: picker.py --mode blueocean --sort-by potential_index --limit 100
        → Sort by HPI descending, full ranking, no hard thresholds
Step 2: Pick top 20, use analyst.py to deep-dive each product's cost structure
        analyst.py --detail --asins ASIN1,ASIN2,ASIN3...
Step 3: Highlight high-ranking products that "would have been filtered out by traditional methods"
        → Tag the reason (low price / mediocre rating) alongside their true profit performance
Step 4: Cross-validate: check CategoryReport to confirm the competitive landscape hasn't deteriorated
```

## Interpretation Notes
1. Top-ranked products: balanced high scores across dimensions, no weaknesses — but not necessarily the most profitable
2. **Edge Dark Horse (Grey Zone Gems)**: Focus on products where 1-2 dimensions are low but composite rank is in the top 10%. Competitors using hard thresholds cannot capture these.
3. Red flags: Even with a high HPI, if recent negative reviews are surging (rating dropped from 4.2 to 3.0 within 3 months), the product has an unresolved fatal flaw.

## Risk Notes
- HPI is a **composite opportunity score (relative value)**, not a profit guarantee — must be combined with cost accounting and market reality checks
- Best used for **comparative ranking within a category**: "which product in this subcategory has the highest hidden profit potential?" rather than "is this specific score good enough?"
- Low price-dimension products require verification that FBA fees are not eroding margins
- ⭐ Certain sub-dimensions (e.g. trend acceleration) require at least 3 months of historical data; reference value is limited for new categories

## Combo Strategy
This Strategy → Low Rating Replacement (validate demand pain points) → Keyword Scatter (find traffic entry points) → Launch
