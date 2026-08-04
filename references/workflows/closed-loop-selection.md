# Closed-Loop Product Selection Workflow

> **Version**: 3.1 | **Turns**: 100 (Path 1) / 115 (Path 2) | **Seller Panel**: 7 members | **Platforms**: 7 | **Business Models**: 6 | **Validated**: 20 rounds, 82.7% avg adoption

## Quick Start

```
/goal /sorftime-seller-agent Closed-loop product selection for {category} on Amazon US. Budget: ${amount}. Seller: {beginner|growing|professional|factory|brand}.
```

中文：`/goal /sorftime-seller-agent 跑完整选品工作流，瑜伽垫，$15K，进阶卖家`

---

## Phase Execution Protocol

### Phase 0: Seller Input Gate (Turns 1-3)
Ask: Budget, Platform, Stage, Model, Goal (Path 1 or 2). Confirm before proceeding.

### Phase A: Discovery (Turns 4-15)
- **Path 1 (HPI Product-First)**: `potential_product` with NO hard-threshold pre-filters. Safety-filter AFTER ranking. ≥10 products.
- **Path 2 (Market-First)**: `category_search_from_top_node` → `category_report` × N → 11-dimension composite scoring → Top 3 subcategories → `potential_product` × node_id within winners.

### Phase B: Deep-Dive Verification (Turns 16-30)
`product_detail` + `product_trend`(SalesVolume,Price,Rank) + `product_traffic_terms` — ALL PARALLEL. `product_reviews` × TOP 3. `category_report` for brand concentration. Differentiation analysis.
- ⚠️ **TRAFFIC DATA**: Use `exposure_position` field ("Organic"/"Ad"/"Ad,Organic") — NOT the non-existent `organic_searched_percentage`.
- ⚠️ **TREND DATA**: 6-month window. Classify with numeric thresholds: Accelerating (MoM growth increasing, last-3mo > prior-3mo by ≥15%), Steady (±10%), Flat (±5%), Declining (last-3mo < prior-3mo by ≥10%).

### Phase C: Supply Chain (Turns 31-45)
`ali1688_similar_product` (Chinese keywords) × N. `ali1688_product_variations` for top match. Full landed cost. First-order qty.

### Phase D: Financial Analysis (Turns 46-55)
Full P&L → post-ad true net margin. Capital vs budget check. **DO NOT apply verdict in this phase.**

### Phase E: Risk Assessment (Turns 56-65)
4-tier risk + brand monopoly + seasonal + review quality + IP clearance + compliance + platform-specific.

### Phase D2: Seller Review Panel (Turns 66-80) 🚨 MANDATORY — DO NOT SKIP
**SPAWN 7 independent sub-agents via Agent tool in parallel.** The main agent MUST NOT vote — only the panel votes. Each panelist receives the full data package (P&L + trends + traffic + sourcing + risks). Each scores 5 dimensions (0-10), votes GO/CAUTION/NO-GO, writes role-specific reasoning.
- GO: ≥4/7 votes GO + Platform Specialist (Seat 6) ≠ NO-GO
- NO-GO: ≥4/7 NO-GO OR Financial Auditor (Seat 7) NO-GO with specific P&L evidence
- CAUTION: else
- Panel may OVERRIDE algorithmic thresholds with documented reasoning.

### Phase F: Final Deliverable (Turns 81-95)
Go/No-Go Decision Table (confidence-labeled). TOP 3 deep-dive. Risk registry with severity+mitigation. Actionable next steps. Budget utilization vs seller budget. Raw data appendix. Panel vote tally + dissent summary. **No fabricated data — UNAVAILABLE is acceptable.**

### Phase G: Post-Launch Monitoring (Turns 96-100) 🚨 MANDATORY
Generate a complete, copy-paste-ready `/loop` command with: 30/60/90-day checks via `product_detail` + `product_trend`, reorder trigger (inventory <30 days cover), ACoS checkpoint (day 45, alert if >150% of projection), review rating alert (<4.3 triggers quality investigation).

---

## Seller Review Panel (7 Members)

| Seat | Role | Weight |
|:----:|------|:--:|
| 1 | Peer Match (same stage+budget+model) | ×2 |
| 2 | Peer Alt (same stage, budget×0.8) | ×1 |
| 3 | Mentor (one stage above) | ×1.5 |
| 4 | Conservative Voice | ×1 |
| 5 | Opportunity Voice | ×1 |
| 6 | Platform Specialist | ×1.5 |
| 7 | Financial Auditor | ×1 |

---

## Data Confidence Labels

| Label | Meaning |
|-------|---------|
| `[VERIFIED]` | Directly from Sorftime API |
| `[ESTIMATED: formula]` | Calculated with shown formula |
| `[ASSUMED: source]` | Industry default |
| `[UNAVAILABLE: reason]` | Honest gap — do NOT fabricate |

---

## Critical Gotchas

1. **`product_traffic_terms` field trap**: Use `exposure_position` (values: "Organic"/"Ad"/"Ad,Organic"), NEVER query `organic_searched_percentage` (doesn't exist).
2. **No hard-threshold pre-filters on HPI**: `potential_product` with NO price/sales/review filters before ranking.
3. **Verdict from panel, not algorithm**: Phase D computes P&L as INPUT to Phase D2 panel, not as final verdict.
4. **Checkpoint after every phase**: State saved to resume if interrupted.
5. **Honest data**: UNAVAILABLE with reason > fabricated numbers.

## Data Persistence

Every phase writes output to disk. Output directory: `~/Documents/sorftime/{date}-{category}-{platform}/`

| File | Phase | Content |
|------|-------|---------|
| `01-discovery.json` | PA | Raw API + filtered shortlist |
| `02-verification.json` | PB | Detail + trend + traffic per ASIN |
| `03-supply-chain.json` | PC | 1688 results + landed cost |
| `04-financials.json` | PD | Full P&L per product |
| `05-risks.json` | PE | Risk matrix per product |
| `06-panel-verdict.json` | PD2 | All 7 votes + reasoning + verdict |
| `07-deliverable.md` | PF | Self-contained Markdown deliverable |
| `08-monitoring.sh` | PG | /loop command |
| `workflow-state.md` | All | Resume-if-interrupted checkpoint |
| `README.md` | All | Index + scenario params + data freshness |

`07-deliverable.md` must be fully self-contained — readable standalone without the conversation context.
