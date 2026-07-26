# Keyword Strategy Optimization

> Type: Tactical | Seller Stage: All | Platform: Amazon / Walmart

## Core Logic

Keyword strategy is not about finding the "highest search volume terms" and stacking them. It is about ranking keywords by Opportunity Score -- a term with massive search volume but dominated by entrenched competitors is less valuable than a term with moderate search volume, dispersed clicks, and reasonable bid prices.

## Methodology Principles

The traditional three-part keyword playbook is entirely built on hard-threshold thinking:

1. **"Only target keywords with search volume > 1000"** -- A precise long-tail keyword with 800 search volume and extremely high conversion rate gets eliminated by the cutoff.
2. **"Don't bid on anything above $1 CPC"** -- A keyword with $1.2 CPC but 3x the conversion rate may actually yield a lower ACOS.
3. **"Only look at the top 3 pages of competition"** -- Judging difficulty by absolute SERP rank ignores differences in competitor listing quality.

Sorftime's Opportunity Index turns keywords into a continuous ranking spectrum:

```
Opportunity Index = μ₁ x Search Volume Score + μ₂ x Click Concentration (inverse) + μ₃ x Bid Affordability Score
                  + μ₄ x Associated ASIN Quality Score + μ₅ x Seasonal Velocity + μ₆ x Ad Penetration Score
                  + μ₇ x Supply-Demand Ratio ⭐

Where:
  Search Volume Score = min-max normalized log(monthly search volume) -- prevents head terms from dominating
  Click Concentration (inverse) = lower Top 3 ASIN click share is better
  Bid Affordability Score = your target margin / suggested bid (higher ratio is better)
  Supply-Demand Ratio ⭐ = search volume / number of supplying ASINs (Sorftime exclusive metric)
```

- There is no hard threshold of "search volume below N means don't analyze." All keywords are ranked by Opportunity Index.
- A keyword with 800 search volume, low click concentration, and reasonable bids can outrank a keyword with 5000 search volume that is dominated by 3 head terms.
- The Supply-Demand Ratio is a Sorftime-exclusive dimension ⭐ -- a keyword with 2000 search volume but only 50 competing ASINs represents a greater opportunity than one with 5000 search volume and 500 ASINs.

## Trigger Scenarios

- "Expand the keywords for this product"
- "Which keywords should this ASIN focus its bids on?"
- "Analyze whether this keyword is viable"
- "Compare the competitive difficulty of these keywords"
- "See which keywords my competitors rank well for"

## Conversational Execution (agent-x / MCP Channel)

### Step 1: Full Keyword Discovery --> Opportunity Index Ranking
```bash
python3 scripts/picker.py --mode keyword-extends --keyword "dog leash" \
  --domain 1 --sort-by opp_score --top 100
```
Use KeywordExtends ⭐ to expand from the seed keyword into a full keyword set (no search volume floor). Rank by Opportunity Index. Keywords with 300 search volume can still rank if other dimensions are strong enough.

### Step 2: Deep Dive into Priority Keywords
```bash
python3 scripts/analyst.py --mode keyword-search-results --keyword "dog leash" \
  --domain 1
python3 scripts/analyst.py --mode asin-request-keyword --asin "B0XXXXXXXX" \
  --domain 1
```
- **KeywordSearchResults ⭐**: View ASIN distribution on the SERP for this keyword, ad share, and top-10 competitor ratings/prices.
- **ASINRequestKeywordv2**: See which keywords your own ASIN ranks well for; check for overlap with high Opportunity Index keywords.

### Step 3: Cross-Validation
- Use ProductSearch with `--sort-by review_speed` to check the share of new products among top listings for the keyword -- a high new-product share signals easy market entry.
- ❌ Common mistake: Judging keywords by search volume alone without examining the actual competitive structure on the SERP. A keyword with 5000 search volume where the top 3 are all flagship brand products (e.g., "iPhone case") leaves virtually no exposure opportunity for new products -- the Opportunity Index's Click Concentration score automatically depresses such keywords.
- ⭐ The Supply-Demand Ratio is the core anchor of this strategy: keywords with a ratio > 10 represent "demand far exceeding supply." Register monitoring and prioritize listing once confirmed.

## Interpretation Framework

1. **Common traits of high Opportunity Index keywords**: Moderate-to-strong search volume (1000-5000), low click concentration (Top 3 < 40%), Supply-Demand Ratio > 5 -- these keywords have traffic, dispersed opportunity, and a demand gap.

2. **"Grey Zone" keywords ⭐** (quality terms excluded by hard-threshold systems):
   - Search volume 700, extremely low click concentration (Top 3 at only 20%), Supply-Demand Ratio of 12 -- disappears under "search volume > 1000" filtering, but in reality is a textbook "small but profitable" keyword.
   - CPC $1.50 but estimated conversion rate of 15% (double the category average) -- pure bid-level filtering would exclude it, but the Bid Affordability dimension scores it highly.

3. **Risk signals**:
   - High Opportunity Index but Click Concentration score > 80 (too concentrated) --> Verify whether dominated by brand terms. If so, the opportunity is illusory.
   - Search Volume Seasonality > 70 --> Off-peak ad performance will be significantly reduced.
   - Ad Penetration > 60% (SERP is >60% ad placements) --> Traffic is purely ad-driven; organic ranking accumulation will be difficult.

## Risk Notes

- The Opportunity Index is based on historical data (past 30 days). It does not predict search volume spikes (e.g., trending events driving sudden demand).
- Supply-Demand Ratio accuracy depends on ASIN coverage. When category boundaries are fuzzy (e.g., "dog leash" spans multiple subcategories), supply-side data may have deviations.
- Suggested bids are reference values. Actual bids are affected by competitor dynamics -- setting up monitoring for real-time tracking is recommended.
- Keyword strategy is highly dependent on product fit. A keyword with a high Opportunity Index will see sharply reduced conversion if it doesn't fully match your product.

## Workflow Chain

This Card --> Market Panorama (validate the overall health of the category containing these keywords) --> Competitor Deep Dive (analyze the strengths and weaknesses of top competitors for these keywords)

Typical flow: Top keywords by Opportunity Index --> Panorama analysis of the categories those keywords belong to --> Select a keyword cluster with Supply-Demand Ratio > 10 --> Teardown top competitors' negative reviews in that cluster --> Build a differentiated listing plan and launch.
