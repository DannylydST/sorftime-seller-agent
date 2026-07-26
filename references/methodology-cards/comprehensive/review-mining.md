# Review Mining & Pain Point Extraction

> Category: Comprehensive | Seller Stage: Growing/Professional | Platform: Amazon / Walmart

## Core Logic

Rank product defects and feature demands by a cross-competitor Pain Point Severity Index, transforming qualitative feedback into a quantitatively ranked list of improvement priorities.

## Methodology Principles

**Core Differentiation: Pain Point Severity Index ranking, not word-frequency counting.** Many tools on the market do simple "high-frequency word counting" — "battery" appears 200 times, "noise" appears 150 times, therefore "noise" is the second-biggest pain point. But here's the problem: **people mentioning "battery" may have given 4 stars (just thought battery life was slightly short), while 80% of people mentioning "noise" gave 1-2 stars.** Sorftime's approach ranks by Pain Point Severity Index:
```
Severity Index = Mention Frequency Score × Rating Negative-Correlation Coefficient
```
A "low frequency but almost exclusively tied to negative reviews" pain point (e.g., "catching fire") will rank far above a "high frequency but mostly mentioned in passing in neutral reviews" term (e.g., "price"). Hard-threshold systems that only look at word frequency would filter out "catching fire" as a low-frequency term — a fatal omission.

**Sorftime Exclusive Advantage:** The combined `ProductReviewsQuery` + `ProductReviewsCollection` workflow retrieves both semantic labels and rating distributions from review text simultaneously, without requiring an external NLP model. Sentiment analysis accuracy is highest for English-language reviews (the primary target market). Cross-language sentiment calibration (e.g., reviews written in Chinese on Amazon.com) is supported but may involve additional variance due to differences in expression norms between languages.

Competitor approaches generally rely on either the Amazon Product Advertising API (which only returns rating summaries without full text) or external scrapers combined with self-built NLP pipelines. Sorftime handles everything in one step, with cross-ASIN pain point aggregation automatically completed within the same system.

## Trigger Phrases

- "Analyze where these 3 competitors' negative reviews cluster"
- "What are users' biggest complaints in this category"
- "If this product were redesigned, what problem should we fix first"
- "See if competitor review sections reveal any unmet needs"

## Conversation Mode Execution (agent-x / MCP Channel)

### Step 1: Full-Spectrum Pull → Index Ranking
No hard-threshold filtering. Call `ProductReviewsQuery` to retrieve review data for 3-5 core competitor ASINs in the target category. Extract from each review:
- Rating (1-5 stars)
- Review tags / keywords
- Review body text (for semantic analysis)
Build a "frequency-rating negative-correlation matrix" to calculate each keyword's Severity Index. **Keywords with frequency < 5 are not automatically discarded** — a low-frequency term with an extremely strong negative rating correlation (locked to negative reviews) will still rank high. For example, "screw loose" may appear only 3 times but all are 1-star reviews. Its raw exposure is lower than "color mismatch" at 50 mentions — but the Severity Index will rank "screw loose" higher because it directly correlates with returns.

### Step 2: Top N Deep Analysis
Take the top 10 pain point tags by Severity Index and call `ProductReviewsCollection` to pull the full review text containing each pain point:
- The complete narrative of each negative review (what exactly is the user complaining about)
- Cross-ASIN distribution of the pain point (an isolated issue with one competitor, or a category-wide systemic flaw)
- Solution direction embedded in the pain point (do negative reviews mention alternative brands or express expectations)
- Output a "Pain Point → Improvement Suggestion" mapping table

### Step 3: Cross-Validation
Call `ProductDetail` to check whether competitors' listings have already addressed these pain points (e.g., A+ modules adding drop-protection explanations, titles adding "silent" claims). If a competitor has already solved it and you haven't → high priority. If all competitors are dodging the pain point → differentiation entry opportunity.

## Results Interpretation Framework

1. **Common Traits of Top-Ranked Items:** Pain points with Severity Index > 0.6 are typically "functional defects" (leaking, breakage, incompatibility) — high-frequency, high-severity keywords are **must-fix** hard flaws.
2. **"Gray Zone" Products:** Pain points with Severity Index 0.3-0.5 but mention frequency < 20 — hard-threshold systems would classify these as "insufficient sample size" and filter them out. However, if you find these low-frequency pain points appearing across **multiple competitors'** negative reviews with highly consistent phrasing (e.g., all complaining about "metal edges that cut fingers"), this is an underestimated category-level problem. **Whoever solves it first achieves differentiation first.**
3. **Risk Signals:** A pain point's Severity Index spiking from 0.2 to 0.6 within 3 months — this indicates a worsening problem, potentially a batch quality issue or supplier component change. Requires comparison of index trend across the time dimension.

## Risk Notes

- Review data timeliness is critical — outdated reviews (> 6 months) may reflect already-fixed old problems; down-weight in index calculation
- Negative sentiment does not equal market opportunity — some pain points are physical limits (e.g., "headphones can't be small enough") that no design improvement can resolve
- ASINs with fewer than 50 reviews have high sample bias in review analysis; conclusions are reference-only
- Amazon reviews experience deletion and review manipulation — be especially wary of abnormal rating distributions during new product launch periods
- The Rating Negative-Correlation Coefficient may be distorted by "abnormal rating" behavior from review manipulation — if a competitor purchased a large volume of 5-star reviews, the true proportion of genuine negative reviews is diluted, and the Severity Index will be underestimated. Cross-validate with total review volume.

## Composable Pipelines

[Listing Audit & Optimization](/listing-audit.md) → This Card → Inject pain-point keywords discovered here into listing optimization → [Pricing Position Analysis](/pricing-position.md) to confirm whether post-optimization pricing aligns with the target user's expected price tier
