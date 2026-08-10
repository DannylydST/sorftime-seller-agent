# Closed-Loop Product Selection Workflow

> **Version**: 3.3 | **Turns**: 100 (Path 1) / 115 (Path 2) | **Seller Panel**: 7 members | **Platforms**: 7 | **Business Models**: 6 | **Validated**: 20 rounds, 82.7% avg adoption
>
> **v3.6.0 note**: this is a REFERENCE workflow, opt-in only. It runs when the user invokes
> `/goal` / `/loop` or explicitly asks for "closed-loop / 完整选品工作流". Daily queries never
> enter this workflow. Within the workflow, phases are MANDATORY — do not skip.

## Quick Start

```
/goal /sorftime-seller-agent Execute Closed-Loop Product Selection for {category} on {platform}. Seller: {stage}, ${budget}, {model}, country={cn|us|uk|de|other}. Rounds: {N}.
```

中文：`/goal /sorftime-seller-agent 跑完整选品工作流，瑜伽垫，$15K，进阶卖家`

**Rounds parameter**: `{N}=1` means test one category and stop; `{N}=3` scans 3 categories. Seller controls depth vs speed. Stop after `{N*35}` turns (~35 turns/round).

---

## Phase Execution Protocol

### Phase 0: Seller Input Gate (Turns 1-3) — MANDATORY INTERACTION
Ask: Budget, Platform, Stage, Model, **Seller Country**, Goal (Path 1 or 2). **DO NOT call any MCP tool until the seller explicitly chooses a path.**

Present BOTH paths in this exact format:
> "Based on your profile ({stage}, ${budget}, {country} seller), two paths are available:
> **Path 1 (HPI Product Sniper)**: full-category HPI ranking → find undervalued individual products. Fast results.
> **Path 2 (Market Mapper)**: analyze subcategory competition first → pick products within winning categories. Strategic.
> My recommendation: {Path X}, because {reason}. But you decide — Path 1, Path 2, or both?"

Default recommendation: Path 1 for budget<$10K / beginner / arbitrage / "one good product fast"; Path 2 for brand-owner / factory / professional / "a category to build in"; Both for growing $10K+; unsure → Path 2 then Path 1.

**Seller Country is a first-class parameter** — it changes sourcing, logistics, tax, risk, and compliance:

| Dimension | CN (Chinese cross-border) | US (US domestic) | UK (UK domestic) | DE (German domestic) |
|-----------|--------------------------|------------------|------------------|----------------------|
| Sourcing | 1688 (中文) — native | 1688 (EN keywords) — CNY→USD | 1688 (EN keywords) — CNY→GBP | 1688 (EN keywords) — CNY→EUR |
| Logistics | Sea freight + duty + customs | Sea freight + US duty (same as CN — importing from China) | Sea freight + UK duty + 20% VAT | Sea freight + EU duty + 19% VAT |
| COGS | Lower (factory-direct, CNY native) | Same factory price, but CNY→USD conversion + labeling burden | Same, CNY→GBP | Same, CNY→EUR |
| 1688 viability | ✅ Native experience | ⚠️ Works (verified: English keywords return 100 results), but all titles/descriptions in Chinese | ⚠️ Same limitations | ⚠️ Same limitations |
| COGS fallback | 1688_low × 1.3 | price × 0.30 (higher US wholesale markup) | price × 0.35 (EU wholesale) | price × 0.35 (EU wholesale) |
| Tax | Amazon collects/remits | Sales tax nexus | VAT registered (recover import VAT) | VAT registered |
| Returns | Disposal only (no domestic address) | Restock/resell possible | 14-day mandatory withdrawal | 14-day mandatory withdrawal |
| Compliance Risk | HIGH (unfamiliar FCC/FDA/CPC) | LOW | MEDIUM (UKCA) | MEDIUM (WEEE/GPSR/VerpackG) |
| IP Risk | HIGH (complaint vulnerability) | LOW | LOW | LOW |
| Language | May need listing translation help | Native English | Native English | German required |

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

ADJUST TAX BY SELLER COUNTRY:
- `cn` → No US sales tax obligation (Amazon collects/remits). Return cost: disposal only (no domestic return address).
- `us` → Sales tax nexus consideration. Return cost: domestic return address, restock/resell possible.
- `uk`/`de` → VAT registered: input VAT recoverable on import. Return cost: EU mandatory 14-day withdrawal.

### Phase E: Risk Assessment (Turns 56-65)
4-tier risk + brand monopoly + seasonal + review quality + IP clearance + compliance + platform-specific.

ADJUST RISK BY SELLER COUNTRY:
- `cn` → HIGHER: compliance unfamiliarity (FCC/FDA/CPC), IP complaint vulnerability, account suspension risk
- `us` → LOWER: compliance familiarity, stronger IP enforcement access, domestic liability insurance available
- `uk`/`de` → MEDIUM: product liability strict, WEEE/GPSR/UKCA mandatory, language-specific listings

### Phase D2: Seller Review Panel (Turns 66-80) 🚨 MANDATORY — DO NOT SKIP
**SPAWN 7 independent sub-agents via Agent tool in parallel.** The main agent MUST NOT vote — only the panel votes. Each panelist receives the full data package (P&L + trends + traffic + sourcing + risks). Each scores 5 dimensions (0-10), votes GO/CAUTION/NO-GO, writes role-specific reasoning.

Seats (country-aware): Seat1 Peer Match (same stage+budget+model+COUNTRY)×2 · Seat2 Peer Alt (same country, budget×0.8)×1 · Seat3 Mentor (one stage up, SAME country)×1.5 · Seat4 Conservative×1 · Seat5 Opportunity×1 · Seat6 Platform Specialist (platform+COUNTRY dynamics)×1.5 · Seat7 Financial Auditor (country-specific P&L, tax, duties)×1.

**Seat7 MUST return before final verdict** — if timeout, retry with a simplified P&L-only prompt. Every panelist vote MUST include 2-3 sentence role-specific reasoning in the deliverable, not just the vote.

- GO: ≥4/7 votes GO + Platform Specialist (Seat 6) ≠ NO-GO
- NO-GO: ≥4/7 NO-GO OR Financial Auditor (Seat 7) NO-GO with specific P&L evidence
- CAUTION: else
- Panel may OVERRIDE algorithmic thresholds with documented reasoning.

### Phase F: Final Deliverable (Turns 81-95)
Go/No-Go Decision Table (confidence-labeled). TOP 3 deep-dive. Risk registry with severity+mitigation. Actionable next steps. Budget utilization vs seller budget. Raw data appendix. Panel vote tally + dissent summary. **No fabricated data — UNAVAILABLE is acceptable.**

🚫 **ANTI-ABSOLUTISM RULE**: NEVER use absolute language. BANNED phrases: "this product WILL succeed", "guaranteed profit", "100% safe", "definitely", "certainly", "no risk". REQUIRED qualifiers: "based on available data", "estimates suggest", "historical trends indicate", "panel assessment is", "verify independently before committing capital".

The Executive Summary MUST include: "All supply chain data is from 1688 (Chinese B2B platform) and is FOR REFERENCE ONLY. Financial projections are ESTIMATES based on current API data. Verify with actual supplier quotes, freight forwarders, and a small-batch PPC test before committing your full budget."

Every GO verdict MUST be accompanied by: "Proceed to supplier negotiation and sample order. Do NOT commit full capital until [specific condition] is verified."

### Phase G: Post-Launch Monitoring (Turns 96-100) 🚨 MANDATORY
Generate a complete, copy-paste-ready `/loop` command with: 30/60/90-day checks via `product_detail` + `product_trend`, reorder trigger (inventory <30 days cover), ACoS checkpoint (day 45, alert if >150% of projection), review rating alert (<4.3 triggers quality investigation).

Output the EXACT `/loop` command (NOT `/goal`):
```
/loop 30d /sorftime-seller-agent Check {ASIN} on {platform}: product_detail(price/BSR/reviews/rating) + product_trend(SalesVolume)30d. Alerts: sales<30%proj D60->re-evaluate, ACoS>150%est D45->pause, rating<4.3->QC, stock<30d->reorder.
```

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

Every phase writes output to disk.

Output directory: `${SORFTIME_OUTPUT_DIR:-~/Documents/sorftime}/{date}-{category}-{platform}/`

Override via `SORFTIME_OUTPUT_DIR` env var. Falls back to `~/Documents/sorftime`.

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
