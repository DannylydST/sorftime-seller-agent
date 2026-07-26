# Listing Audit & Optimization

> Category: Tactical | Seller Stage: Beginner/Growing | Platform: Amazon / Walmart

## Core Logic

Identify keyword coverage gaps and title density weaknesses between your listing and top competitors. Rank gaps by a Coverage Gap Score to surface the highest-priority optimization targets.

## Methodology Principles

**Core Differentiation: Full-spectrum ranking, not binary filtering.** Most competitor tools set a hard threshold — "only include keywords where > 50 ASINs index on this term," or "filter out keywords with search volume < 1000." This approach outright discards massive numbers of long-tail keywords. Sorftime's approach: every keyword receives a weighted rank in the Coverage Gap Index. A keyword with low search volume but high conversion rate, where competitors have universally built coverage while you have none, can still rank very high. Hard-threshold systems discard these keywords. A ranking system places them at their deserved position — prioritize the head during optimization, and the tail remains accessible for later review.

**Sorftime Exclusive Advantage:** `ASINRequestKeywordv2` can simultaneously pull keyword data for your ASIN plus 5-10 competitor ASINs, performing cross-comparison entirely within the Sorftime system — no manual spreadsheet merging required. `KeywordSearchResults` returns results sorted by organic rank, revealing which keywords you rank for beyond page 3 — these are your "invisible gaps."

## Trigger Phrases

- "Audit this listing's keyword coverage for me"
- "Why can't this listing's traffic go up"
- "Compare keyword layout differences between me and competitors"
- "Does this ASIN still have room for keyword optimization"

## Conversation Mode Execution (agent-x / MCP Channel)

### Step 1: Full-Spectrum Pull → Index Ranking
No hard-threshold filtering. Call `ASINRequestKeywordv2` to pull the full keyword dataset for the target ASIN (search volume, ranking, indexing status). Simultaneously pull keyword data for 3-5 core competitor ASINs. Rank by Coverage Gap Score:
```
Gap Score = Σ (Number of competitor ASINs indexing the keyword - Whether your ASIN indexes it) × Search Volume Weight × Rank Disparity Factor
```
**Keywords with zero search volume are not automatically discarded** — they can still earn a Gap Score because "multiple competitors are using them" and appear in the ranking. Likewise, "keywords with huge search volume that no competitor covers" will rank lower — they may be false high-demand keywords (with no actual conversions); the index automatically down-weights them. Discussion by tier:
- Gap Score > 80: Competitors have full coverage; you are absent → top priority
- Gap Score 30-80: Partial competitor coverage → secondary priority
- Gap Score < 30: Scattered coverage → incremental additions

**Sorftime Exclusive:** `ASINRequestKeywordv2` handles multi-ASIN comparison in a single call, eliminating the need to call multiple external APIs and manually merge results. Each call returns data already grouped by ASIN, ready for scoring.

### Step 2: Top N Deep Analysis
Take the top 20 gap keywords and call `KeywordSearchResults` to inspect the organic search result distribution for each keyword:
- How many ASINs in the Top 20 for this keyword are your direct competitors
- Your competitors' average rank on this keyword
- Title density for this keyword among Top ASINs (proportion with the keyword in their title)
- Comprehensive evaluation of "conquest difficulty" — not just search volume, but search volume × competitor density × your own rank disparity

### Step 3: Cross-Validation
Call `ProductDetail` to verify the actual title, bullet points, description, and A+ content of your current listing. Identify:
- Which gap keywords can be directly embedded into the title → top priority
- Which fit into bullet points → secondary priority
- Which require A+ or backend keyword supplementation → last
- Output a "title rewrite version recommendation" ordered by priority

## Results Interpretation Framework

1. **Common Traits of Top-Ranked Items:** Keywords with Gap Score > 50 are typically mid-tail keywords with search volume 500+ and competitor coverage > 60%. These are **must-claim territory**.
2. **"Gray Zone" Products:** Keywords with Gap Score 10-30 but competitor coverage < 40% — search volume may be as low as 200 or even lower. Hard-threshold systems (filtering out search volume < 500) would discard them, but these keywords often represent areas competitors have not yet invested in. **First-mover advantage applies.**
3. **Red Flags:** Your ASIN has zero indexing on a high-search-volume keyword — this may indicate an Amazon crawling issue (listing content doesn't cover that semantic field) or a lack of synonymous expressions in your title/bullet points. Investigate first.

## Risk Notes

- Keyword optimization must not degenerate into keyword stuffing — natural language density must stay within reasonable bounds, or the listing will be flagged for keyword spamming
- Competitor ASIN selection directly affects Gap Score accuracy — choosing the wrong competitors skews the gap analysis
- Search volume data has inherent latency (typically 24-48 hours). Seasonal keyword search volume fluctuates significantly; a single week's data can lead to misjudgment
- Large coverage gap does not equal immediate optimization priority — consider the keyword's actual conversion rate
- The Rank Disparity Factor requires regular updates — competitors may also be continuously optimizing; Gap Scores are dynamic
- The same keyword can perform very differently across marketplaces (Amazon.com vs Amazon.co.uk); cross-marketplace analysis must be run separately

## Composable Pipelines

This Card → [Review Mining & Pain Point Extraction](/review-mining.md) → Inject pain-point keywords discovered from negative reviews into listing copy optimization → [Traffic Structure Analysis](/traffic-structure.md) to verify whether organic traffic share has improved due to keyword gap filling

**Reverse Pipeline:** ASINs found to have insufficient organic keyword coverage in [Traffic Structure Analysis](/traffic-structure.md) → This Card diagnoses which specific keywords are missing → Return to Traffic Structure Card post-optimization to validate the effect
