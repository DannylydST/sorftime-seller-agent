# Traffic Structure Analysis

> Category: Tactical | Seller Stage: Growing/Professional | Platform: Amazon / Walmart

## Core Logic

Decompose an ASIN's traffic source structure (organic search vs. ad traffic vs. recommendation traffic) and rank by Organic Traffic Health Index to identify ASINs over-dependent on advertising — what we call "sick traffic" ASINs.

## Methodology Principles

**Core Differentiation: Organic Traffic Health Index ranking, not single-dimension metric cutting.** Most competitor tools only tell you "this ASIN's ad traffic share is 60%" — and leave it at that. But 60% means completely different things across categories and lifecycle stages — 60% is normal for a new product; 60% for a mature product is dangerous. Sorftime's approach builds a multi-dimensional health index:
```
Organic Traffic Health = Organic Traffic Share × Organic Keyword Diversity Coefficient × Organic Rank Stability
```
**No single-dimension hard cutting** — e.g., "ad share > 50% = sick traffic." If a category's industry-average ad share is 55%, then 60% is not actually severe, while 80% is. Sorftime ranks by score rather than setting an absolute cap — an ASIN ranked lower may only have 5% more ad share than the one ranked higher, but with the Keyword Diversity Coefficient factored in, the health gap emerges naturally.

**Sorftime Exclusive Advantage:** `ProductTrafficTerms` can directly return an ASIN's organic search keyword list and rankings. `ASINRequestKeywordv2` can pull ad-targeted keyword data. These two endpoints naturally complement each other, directly computing an ASIN's "organic search coverage / ad campaign coverage" intersection and difference set. Competitors typically need to manually stitch together multiple data sources to achieve the same result.

## Trigger Phrases

- "Why does this ASIN get zero orders the moment ads stop"
- "Check whether this listing's traffic structure is healthy"
- "Compare organic traffic capability between me and competitors"
- "Why is my organic ranking so poor"

## Conversation Mode Execution (agent-x / MCP Channel)

### Step 1: Full-Spectrum Pull → Index Ranking
No hard-threshold filtering. Call `ProductTrafficTerms` to retrieve all organic search keywords and rankings for the target ASIN. Simultaneously call `ASINRequestKeywordv2` to retrieve the list of ad-targeted keywords associated with the ASIN. Cross-reference the two data sources and calculate the Organic Traffic Health Index for each ASIN:
```
Organic Traffic Health = (Organic Keyword Count ÷ Total Keyword Count) × Inverse Normalization of (Average Organic Keyword Rank) × Search Volume Share Covered by Organic Keywords
```
**ASINs with zero organic keywords are not directly discarded** — they will be ranked last, but the user can see the extreme signal that "this ASIN has zero organic traffic." A hard-threshold system might simply return no results, leaving the user completely unaware that "there exists an ASIN without a single organic keyword."

### Step 2: Top N Deep Analysis
Take the top 10 ASINs (healthiest) and bottom 5 ASINs (least healthy) for comparative analysis:
- Healthiest ASINs: What is their "organic keyword → ad keyword" ratio? What is their average organic rank range? What common listing traits do these ASINs share (review count, age, price band)?
- Least healthy ASINs: Why do they have so few organic keywords? Is it insufficient listing keyword coverage (connectable to the Listing Audit & Optimization Card), or is poor conversion caused by low review ratings → organic ranking cannot climb?
- Among ad-targeted keywords, which have no corresponding organic ranking? These are "pure cash-burn keywords" — if the category's ACOS is high for these keywords, recommend cutting or lowering bids

### Step 3: Cross-Validation
Call `KeywordSearchResults` to examine the actual search results for the lowest-ranked organic keywords, and determine:
- How heavy is the ad deployment density among the category's top ASINs (if everyone is spending heavily on ads, a traffic structure skewed toward ads is a category characteristic rather than an individual problem)
- Whether there is short-term room for your organic ranking improvement (low organic traffic during the new product launch period is normal)
- Comprehensive judgment: is the current ASIN's traffic structure problem a strategy issue, a listing quality issue, or a category characteristic

## Results Interpretation Framework

1. **Common Traits of Top-Ranked Items:** ASINs with Organic Traffic Health > 0.7 typically possess "high review base (200+), high organic rank density (Top 50 keyword coverage > 60%), low ad dependence (ads used only for gap-filling, not as the primary driver)" — they are the classic "free-traffic machines."
2. **"Gray Zone" Products:** ASINs with Organic Traffic Health 0.3-0.5 but strong organic keyword diversity (covering 30+ organic keywords) — hard-threshold systems that only look at ad share might label these ASINs as "traffic-unhealthy," but in reality they have a solid organic traffic foundation. They are merely in the new-product ramp-up phase or off-season, causing passive elevation of ad share. **These are actually the ASINs most worth investing in — they have organic traffic foundations; ads are just a catalyst.**
3. **Single-Source Dependency Risk:** An ASIN may have 80% organic traffic, but its organic keywords are concentrated in 3-5 search terms — it is highly dependent on a handful of keywords. If the rankings of these keywords fluctuate (competitor influx, algorithm adjustments), traffic undergoes a cliff-like collapse. "Healthy" with low diversity is actually fragile health.

## Risk Notes

- Traffic structure analysis cannot rely on single-day data — organic ranking fluctuating 10-20% daily is normal; use a 7-14 day average
- Ad traffic share = ad spend / total traffic, not ad order share / total orders — looking at both together yields greater accuracy
- During the new product launch period (within 30 days), low organic traffic is normal; premature traffic structure judgment leads to misdiagnosis
- Seasonal categories: traffic structure differs enormously between off-season and peak season; the data's time window must be clearly labeled
- Walmart platform's ad data granularity is coarser than Amazon's; traffic decomposition precision is slightly lower

## Composable Pipelines

[Listing Audit & Optimization](/listing-audit.md) → This Card → Verify whether organic traffic share has improved after listing optimization → [Pricing Position Analysis](/pricing-position.md) to determine whether low ad efficiency is caused by pricing issues
