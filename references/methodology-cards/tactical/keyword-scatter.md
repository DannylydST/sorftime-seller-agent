# Keyword Scatter Opportunity

> Category: Tactical Strategy | Seller Stage: Growing+ | Platform: Amazon/Walmart

## Core Logic
High search volume + low click concentration = no brand or product monopolizes traffic for this keyword → You have a window of opportunity. — Search demand is real, but "consumers haven't decided who to click yet."

## Methodology

**Key Distinction: Full-Ranking vs Hard-Threshold Filtering**

Traditional keyword-based product selection often uses hard thresholds:
```
searchVolume >= 5000  AND  clickMonopolyRate <= 30%  AND  PPC <= $1.50
```
A keyword with 4800 search volume and 32% click monopoly rate gets discarded — even if its conversion rate is far above category average and its product count is just right for a new seller to enter.

Sorftime's **Keyword Opportunity Index ⭐** uses full-ranking:
```
Opportunity Index = Search Volume Score x (1 - Click Concentration) x (1 / SPR Score)
```
Every keyword scores continuously on each dimension: search volume (higher absolute = higher score), monopoly (lower concentration = higher score), and competition (lower SPR = higher score). A keyword at 4800 search volume simply scores marginally lower than one at 5000, but if it excels on "low monopoly + low competition," its composite rank can easily surpass a keyword with 8000 search volume but 70% of clicks captured by the Top3 products.

**Why click concentration is the key metric**:
- Low concentration (< 25%) = consumers browse and compare, no single player dominates → High opportunity for new entrants
- High concentration (> 60%) = brand or bestseller monopoly, new entrant conversion is extremely difficult
- But full-ranking doesn't draw a line at 25% — 24% and 26% are just score differences

## Trigger Phrases
- "Show me keywords not monopolized by top sellers"
- "High traffic but low competition keywords"
- "Blue ocean keywords"
- "Are there traffic entry opportunities in my category?"

## Execution Steps

### Conversation Mode (agent-x)
```
Step 1: KeywordSearchResults --keyword <coreKeyword> --limit 100
        → Get brand distribution and click data for search results

Step 2: KeywordExtends --keyword <coreKeyword> --type long-tail
        → Expand long-tail keywords, obtain search volume, click concentration, and SPR data

Step 3: Keyword Opportunity Index ranking → Top 20 keywords
        picker.py --mode keyword-opportunity \
          --keyword <coreKeyword> --sort-by opportunity_index --limit 50

Step 4: For Top 5 keywords, use ProductSearch to find existing products
        → Confirm whether there are "mediocre quality but traffic-dominant" products that can be displaced
```

## Interpretation Notes
1. Top keyword characteristics: medium-to-high search volume + top-3 click share below 30% + SPR < 0.5 (organic results dominant)
2. **Grey Zone Keywords**: Keywords with 2000-4000 search volume are the most likely to be overlooked by competitors (hard-threshold tools cut at 5000), but they are long-tail precise and often have higher conversion rates
3. Red flags: High search volume + low click concentration + SPR > 1.5 — this means the top results are all advertising-driven, and your organic ranking has little chance to break through; requires a high ad budget

## Risk Notes
- The Keyword Opportunity Index is based on **search-side** data, not conversion-side data — high opportunity != high conversion
- ⭐ Low scatter may be due to severe product homogenization (all generic/OEM products); in this case, even with opportunity, differentiation is hard
- Must distinguish "low concentration due to dispersed demand" from "low concentration because search volume is too small for anyone to bother" — the latter offers little opportunity

## Combo Strategy
This Strategy → Low Rating Replacement (check search results for poorly-reviewed products to displace) → Brand Gap Entry (assess category landscape) → Hidden Profit Index (validate profit)
