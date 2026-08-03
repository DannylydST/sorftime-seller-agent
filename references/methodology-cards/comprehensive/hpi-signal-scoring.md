# HPI 5-Dimension Signal Scoring

> **Purpose**: Score products on 5 buyer-relevant signals, not just profit. Find products that sell well with low ad dependency, low reviews, stable pricing, growing sales, and climbing BSR.

## The 5 Signals

| Signal | Weight | What "Good" Looks Like | Red Flag |
|--------|--------|----------------------|----------|
| Ad Independence | 20% | >60% organic-only keyword share, weighted by search volume | <10% organic — lives on ad spend |
| Review Efficiency | 20% | >10x sales/review ratio, confidence-adjusted | <3x — saturated, high barrier |
| Price Discipline | 20% | Price stable or rising over 6 months; margin >30% | Price declining OR margin <20% |
| Sales Growth | 20% | Accelerating 6-month SalesVolume trend | Declining trend |
| BSR Momentum | 20% | Rank improved >50% over 6 months | Rank falling |

## Scoring Formula

```
1. Ad Independence = weighted organic-only keyword share, mapped to 0-1
   >60% = 1.0 | 30-60% = 0.7 | 10-30% = 0.4 | <10% = 0.1

2. Review Efficiency = sales / (reviews + 1)
   Confidence penalty: reviews<5 → ×0.5 | 5-10 → ×0.7 | 10-20 → ×0.85 | >20 → ×1.0
   Cap at 25x, map to 0-1

3. Price Discipline:
   Trend: stable/rising = 1.0 | slight decline(<5%/6mo) = 0.6 | significant = 0.2
   Margin check: (price - 0.35×price - fba_fee) / price
   If margin <20% → cap at 0.3 regardless of trend
   If 1688 data available: use 1688_low × 1.3 as COGS (×1.3 to adjust for bait-pricing — 
1688 listings often show the cheapest variant, the actual target SKU can be 20-50% higher).
If 1688 data unavailable: use price × 0.35 (standard) or price × 0.45 (heavy/bulky) as COGS.
Both are estimates. Sellers must verify with actual supplier quotes.

4. Sales Growth:
   Accelerating = 1.0 | steady = 0.7 | flat = 0.3 | declining = 0.1
   New product (<3mo): min(sales/(months_active × 300), 1.0)

5. BSR Momentum:
   Climbed >50% in 6mo = 1.0 | slow climb = 0.7 | stable = 0.3 | falling = 0.1

COMPOSITE = sum × 20. Max = 100.
```

## Execution Protocol

### 1. Parallel Batching
Issue ALL tool calls for one phase in a single message. Never call one-by-one.

### 2. Checkpoint per Phase
After every phase, write `hpi-state.md` with current results. This prevents context loss if turn cap hits.

### 3. Data Sources (6 calls per product)
```
Phase 1: potential_product (1 call, shared) → HPI ranking
Phase 3: product_detail (1 per product) → price, FBA, reviews, BSR, brand, node_id
Phase 4: product_trend × 3 (3 per product) → SalesVolume/Price/Rank 6-month history
Phase 5: product_traffic_terms (1 per product) → organic vs ad keyword exposure
Phase 6 (OPTIONAL): 1688 sourcing check. This is advisory only — NOT a gate.
- Call ali1688_similar_product with Chinese search keywords (1688 is a Chinese platform).
  Extract core product category in Chinese (e.g., "水槽下置物架" not "under sink organizer").
- If results found: note the price range and top 3 supplier product_ids.
- For SKU-level pricing: call ali1688_product_variations with product_id to drill into 
  specific variant prices (1688 listings often show bait lowest-SKU prices).
- If 0 results or tool errors: skip. Use COGS estimate instead. Do NOT block completion.

**Why optional**: 1688 prices have inherent limitations — bait pricing (cheapest variant 
listed as headline price), quality variability, MOQ mismatch. It is ONE data point for 
supply validation, not the definitive answer. Sellers must verify with actual supplier 
quotes regardless of what 1688 data shows.
Phase 7: category_report (1 call, shared) → brand concentration, Amazon self-owned share
Phase 8: product_reviews (TOP3 only) → defect keyword scan
```

### 4. Safety Gates (before scoring)
- star_rating < 3.8 → remove
- food/pet food/supplement/medical/baby food in title → remove
- Known major brands → remove
- review_count < 5 → flag LOW_CONFIDENCE, keep, apply ×0.5 penalty

### 5. Risk Flags (display, don't score)
- REVIEW_RED_FLAG: 3+ defect keyword mentions in negative reviews
- LOW_MARGIN: margin < 20%
- AMZ_TRAP: amazonOwned sales share > 50%
- BRAND_MONOPOLY: top3 brands > 60%
- LOW_CONFIDENCE: reviews < 5

### 6. Output Completeness Gate (before declaring done)

Every column in the table MUST have data — no "TBD", no "N/A", no empty cells. Check each:

| Column | Source | Missing = Phase Incomplete |
|--------|--------|---------------------------|
| 1688 Price | Phase 6 (OPTIONAL) | Skip — use COGS estimate. Not a gate. |
| Organic% | Phase 5 | Re-run Phase 5 for that ASIN |
| Sales/Price/BSR Trend | Phase 4 | Re-run Phase 4 for that ASIN |
| Risk Flags (AMZ_TRAP, BRAND_MONOPOLY) | Phase 7 | Re-run Phase 7 |
| REVIEW_RED_FLAG | Phase 8 | Re-run Phase 8 for TOP3 |

If any gate fails → continue processing, do not declare goal complete.

### 7. Output Format

Table: ASIN | Product | Price | Mo Sales | Reviews | ★ | FBA | Margin | Organic%(weighted) | Rev Eff(adj) | Sales Trend | Price Trend | BSR Trend | 1688 Price | Score | Risk Flags

TOP3 product-by-product explanation with specific numbers applied.
Include: Key Takeaways, Risk Flags table, Raw Trend Data appendix, Excluded Products list with reasons.

---

## Goal Command Template

```
/goal Run HPI 5D verified shortlist for <category> on Amazon US.
Save checkpoint after each phase.
Output completeness gate: all table columns must have data —
no TBD, no N/A. If any column empty, continue processing.
Output ≥5 rows with all columns + TOP3 explanations + excluded list.
stop after 70 turns
```

**70 turns minimum** — the 6 data sources per product (detail + 3× trend + traffic + 1688 = 6 calls × 10 products = 60 calls + category_report + review scan) require this. 50 turns was insufficient; the 1688 and review scan phases were consistently incomplete at 50.

The skill handles all methodology, scoring, batching, safety rules, and completeness gating automatically.
