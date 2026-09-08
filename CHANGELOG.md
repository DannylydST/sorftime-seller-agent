# Changelog

## [2026-09-08] — v3.6.4 (full release gate)

- `tests/full_gate.py` four-layer release gate (static integrity / py3.10-3.12 compile matrix / read-only tool regression / clean-room e2e) + GitHub Actions CI (3 OS)
- Removed orphan fixture for the retired `tiktok_category_name_search`
- Gate result this run: GREEN (82/82 read-only tools live-verified)

## [2026-09-08] — v3.6.3 (external-audit fixes: retired tool cleanup + py3.10 compat + docs counts)

- `discover_tiktok.py`: stop calling the retired `tiktok_category_name_search`
- `healthcheck.py`: f-string nested same-quote (3.12-only) → pre-joined variable; restores declared Python ≥3.10 support
- SKILL.md: TikTok section rewritten (`tiktok_category_tree` exists, `name_search` retired); Shopee 15→16; 1688 5→6; Walmart 15→18 with the 3 new tools listed
- `sorftime_bridge.py`: typo `tikto_` → `tiktok_`

## [2026-09-07] — v3.6.2 (tool sync 86→97 + healthcheck auth-detection fix)

### Updated
- **Tool matrix synced to server (97 tools, +12/-1)**: new — `reddit_comment_request` / `reddit_post_request` / `reddit_post_search` (Reddit social listening, passthrough), `ali1688_category_tree`, `shopee_category_tree`, `temu_category_tree`, `tiktok_category_tree`, `tiktok_similar_product_detail`, `walmart_category_tree`, `walmart_category_search_from_name`, `walmart_product_search_from_name`, `product_search_from_name`; removed — `tiktok_category_name_search`.
- SKILL.md / README.md tool-count references updated (86 → 97); platform coverage now notes Reddit.

### Fixed
- **healthcheck.py false-positive "Connect OK"**: server-side auth failures (`isError: true` / "Authentication required" / `NotAuthorization` / `"error": true`) arrive as normal text with returncode 0 — a stale or rotated key reported a green check. These markers now fail the check.

All notable changes to Sorftime Seller Agent.

---

## [2026-08-10] — v3.6.1

### Added (audit-layer gap-filling)
- **`verify_candidates.py`** — reusable batch `product_detail` reality-check for the review pipeline. In-process `call_tool_json` (avoids the Windows Store `python3` subprocess hijack), per-ASIN retry + stagger, auto-unwraps the `{"doc","data"}` envelope, key-tolerant field extraction, merges multi-batch output. Documented in SKILL.md §1.1.5 Step 0.
- **Pet oral / oral-entry products** (`category_guard`): dog toothpaste, dental chews, pet oral, 宠物牙膏/洁齿骨 → trap risk (hygiene/compliance).
- **Generic electric devices** (`category_guard` + `review_shortlist`): electric/电动/corded/voltage devices → ops risk / CAUTION (UL/FCC/CE certification barrier), with benign exemption for manual/hand-powered items.
- **FBA fee ratio check** (`review_shortlist`): `fba_fee / price > 35%` → CAUTION (margin fragile after COGS+ads+referral).
- **Organic traffic share** (`analyst.py` competitor mode): computes organic vs ad exposure from `exposure_position`; `<50%` organic → 🔴 buy-traffic bestseller flag, `<70%` → 🟡. Detects the round-11 "硅胶沥水垫 19/20 = 95% ad" class of products.

### Verified
- All 7 workspace audit pitfalls (pet-oral / supplement / therapeutic-claim / patent-pending / red-ocean / electric / FBA-ratio / price-vs-detail / ad-share) now auto-detected by the review framework.
- Benign exemption works (manual/hand-powered devices not flagged).
- 20/20 scenario regression passes.

---

## [2026-08-10] — v3.6.0

### Added
- **Instruction Priority — Obey the Seller**: Precise instructions (exact tool/ASIN/keyword/platform/site/output specified) execute **directly** — no routing, no methodology cards, no lens imposition, no stage reformatting. Only ambiguous/exploratory requests get the guided flow (persona → card → staged output). Output format follows the user (HTML report / `--json` / raw table / analysis on request).
- **Risk folding for professional sellers**: `pro`/`factory`/`brand` profiles collapse the full risk table to a footnote + one-line proactive hints for 🔴hard products (`risk_verbose=false`); `--show-risks` expands. `newbie`/`grower` keep the full warning table + beginner safe-shortlist. Risk is always advisory — never blocks, never hides.
- **Closed-Loop workflow → Reference (opt-in)**: The workflow runs only via `/goal`, `/loop`, or explicit "closed-loop" request. Daily queries never enter it. Full spec (with v3.3+ enhancements: seller-country P0 paths, anti-absolutism rule, `/loop` command) consolidated in `references/workflows/closed-loop-selection.md`.

### Changed
- SKILL.md: new "Instruction Priority" section; big in-file workflow block replaced by a reference pointer; Execution Principle #1 → "obey the instruction first, guide when ambiguous"; Seller Profiles table shows risk presentation per profile.
- `seller_profile.py` / `picker.py` / `walmart_picker.py`: `risk_verbose` flag + `--show-risks` + `format_risk_section` (collapsed footnote vs full table).

### Verified
- Risk folding: pro profile on yoga-mat query → 2 hard products shown as one-line hints + collapsed footnote; `--show-risks` → full table; newbie → full warnings.
- Agent-level: a "pro direct" prompt ("product_search yoga mat US sorted by monthly sales, data only") was executed directly — raw table returned, no lens/no risk table.
- 20/20 scenario regression passes.

---

## [2026-08-10] — v3.5.0

### Added
- **🛡️ Advisory Risk Model (replaces hard blocking)**: The 4-tier risk system is now advisory — products are **never hidden**. Every result carries a risk badge (`🔴hard`/`🟡capital`/`🟠ops`/`⚠️trap`/`🟢safe`) + a specific warning, surfaced after results. False-positive classes fixed via word-boundary matching + context overrides (non-slip ≠ apparel, alcohol wipes ≠ chemicals, microwave-safe containers ≠ appliances, SPF clothing ≠ cosmetics, apple slicer ≠ Apple brand, fashion masks ≠ medical, watch bands ≠ jewelry). Bilingual keyword coverage closed (English medical-device terms added).
- **🧐 Independent Shortlist Review**: New `scripts/review_shortlist.py` — deterministic second-opinion (category-relevance with `--keyword`, margin sanity, IP/trademark, review anomaly, seasonal window, compliance red flags) → `GO / CAUTION / NO-GO`. `picker.py --json` writes the annotated shortlist for seamless handoff.
- **🔀 mcp SDK 1.x/2.x dual-support**: Bridge version-branches the Server API (v1 decorator / v2 constructor, per official 2.0 migration guide) + self-heal guard for unsupported SDK majors. Works on any mcp version; self-repairs on first start.

### Changed
- `category_guard.py` → advisory `assess_product`/`filter_products` (never removes products; returns annotated list + risk warnings).
- `picker.py` / `walmart_picker.py` → full-pool display + risk badges + beginner safe-shortlist highlight; `--json` output; heavy-goods trap now requires low sales (case-weight false positives fixed).
- SKILL.md §1.1.5 → mandatory Post-Selection Independent Review protocol (Layer 1 script + Layer 2 fresh-context sub-agent).
- `healthcheck.py` → UTF-8 hardening (Windows GBK emoji crash).

### Fixed
- Walmart discovery never worked against the live API (illegal `site` param, missing envelope unwrap, key-casing mismatch) — now end-to-end functional.
- venv mcp 2.0 dependency pollution blocked the bridge; self-heal + dual-support resolve.
- Doc-vs-code drift surfaced by agent-level tests: `competitor-deepdive.md` non-existent `--mode` refs, `product_reviews` 100-cap/no-pagination, `product_trend` format, walmart_picker grower example.

### Verified
- 20/20 scenario test suite (deterministic risk-gate + cached live pipeline + environment).
- mcp 1.29 and 2.0 both pass JSON-RPC handshake (initialize → tools/list 87 tools → tools/call).
- 3 agent-level runs (beginner blue-ocean, pro competitor teardown, Walmart discovery) exercised the skill end-to-end.

---

## [2026-08-04]

### Added
- **🔄 Closed-Loop Product Selection Workflow (v3.3)**: Flagship end-to-end pipeline covering product discovery → supply chain → financial analysis → risk assessment → 7-member independent Seller Review Panel → Go/No-Go deliverable → post-launch monitoring. Dual-path architecture: Path 1 (HPI Product-First — individual product discovery via `potential_product` with no hard-threshold pre-filters) and Path 2 (Market-First — category panorama via `category_report` × N → 11-dimension composite scoring → product selection within winning subcategories). Auto-routing based on seller profile (budget/stage/model). One-command trigger: `/goal /sorftime-seller-agent Execute Closed-Loop Product Selection for {category} on {platform}. Seller: {stage}, ${budget}, {model}.` Built-in workflow template in SKILL.md with full MANDATORY execution protocol.
- **🤖 7-Member Independent Seller Review Panel (Phase D2)**: GO/CAUTION/NO-GO verdicts replaced algorithmic thresholds with 7 independent sub-agent reviewers. Panel composition: Seat1 Peer Match (×2), Seat2 Peer Alt (×1), Seat3 Mentor (×1.5), Seat4 Conservative (×1), Seat5 Opportunity (×1), Seat6 Platform Specialist (×1.5, veto power), Seat7 Financial Auditor (×1, veto power). Each scores 5 dimensions (0-10): Financial Viability, Competitive Position, Risk Tolerance Fit, Execution Feasibility, Opportunity Cost. Voting rules: GO ≥4/7 AND Seat6 ≠ NO-GO. NO-GO ≥4/7 OR Seat7 veto with P&L evidence. Panel may override algorithmic thresholds. Main agent FORBIDDEN from voting.
- **💾 Data Persistence**: Every phase auto-writes output to `${SORFTIME_OUTPUT_DIR:-~/Documents/sorftime}/{date}-{category}-{platform}/`. 9 files per run: `01-discovery.json` through `08-monitoring.sh` plus `workflow-state.md` (checkpoint) and `README.md` (index). `07-deliverable.md` is a self-contained Markdown file — fully readable standalone.
- **📊 6 Business Model Variants**: Private Label, Wholesale/Resale, Factory-Direct, Brand Owner (DTC→Amazon), Retail/Online Arbitrage, Dropshipping→FBA. Each with model-specific sourcing logic, P&L structure, and risk weights.
- **🌍 7 Platform Adapters**: Amazon US/UK/DE, Walmart US, Shopee, TikTok Shop, TEMU. Platform-agnostic core with platform-specific P&L templates, fee schedules, and risk matrices.
- **📋 Data Confidence Labeling**: Every data cell carries [VERIFIED]/[ESTIMATED:formula]/[ASSUMED:source]/[UNAVAILABLE:reason]. No fabricated data — UNAVAILABLE with reason is acceptable.
- **📈 20-Round Validation**: Workflow validated across 20 diverse scenarios (6 platforms × 4 stages × 6 business models). 19/20 rounds ≥50% external seller adoption. Average adoption rate: 82.7%. Validation used real Sorftime MCP API data for 15 product categories.
- **📖 Wiki Pages**: [Closed-Loop Product Selection Workflow](https://github.com/DannylydST/sorftime-seller-agent/wiki/Closed-Loop-Product-Selection-Workflow), [Workflow Case Study](https://github.com/DannylydST/sorftime-seller-agent/wiki/Workflow-Case-Study) (Round 3: Insulated Water Bottle — 6/7 GO, 90% adoption).
- **🖼️ Flowcharts**: CN + EN versions with compact left-to-right layout (992px tall vs previous 7800px). Auto-routing decision tree, 7-member panel with Agent spawn visualization.
- **📦 Reference Spec**: `references/workflows/closed-loop-selection.md` — standalone workflow specification with Phase Execution Protocol, Seller Review Panel rules, and Data Persistence schema.

### Fixed
- **`product_traffic_terms` field trap documented**: The API returns `exposure_position` ("Organic"/"Ad"/"Ad,Organic"), `latest_organic_position`, `monthly_search_volume`. There is NO `organic_searched_percentage` field. Querying it returns null/0, falsely suggesting zero organic traffic. Verified case: B0FX56TVJP showed 0% on non-existent field but actually ranks organically on all 20 keywords. Now hard-coded into SKILL.md gotchas with correct parsing logic.
- **`product_trend` parameter name**: Correct parameter is `product_trend_type` (not `trend_type`). Documented in gotchas.
- **Hardcoded output path**: Replaced `~/Documents/sorftime/` with `${SORFTIME_OUTPUT_DIR}` env var with cross-platform defaults.

### Changed
- **SKILL.md v3.0.0 → v3.3.0**: Added Workflow Templates section with Closed-Loop Product Selection as primary workflow. Updated trigger phrases, routing table, and gotchas. Version bump reflects accumulated changes: dual-path architecture (v3.1), 5→7 member panel (v3.1), explicit MANDATORY protocol (v3.2), auto-routing + data persistence (v3.3).

## [2026-08-03]

### Added
- **⚡ Loop & Goal Command Templates**: 58 battle-tested `/loop` and `/goal` automation recipes published to [Wiki](https://github.com/DannylydST/sorftime-seller-agent/wiki/Loop-Goal-Command-Templates).
- **HPI 5D Signal Scoring Workflow**: Built-in workflow template with dedicated methodology card (`comprehensive/hpi-signal-scoring.md`). Replaces 4500-character goal commands with a single 150-character trigger. 5-dimension composite scoring (Ad Independence + Review Efficiency + Price Discipline + Sales Growth + BSR Momentum). Full pipeline: HPI ranking → safety filter → product_detail ×10 → product_trend ×30 → product_traffic_terms ×10 → 1688 (optional) → category_report → review scan → verified shortlist.
- **23rd methodology card**: `comprehensive/hpi-signal-scoring.md` — 5D scoring formula, execution protocol (parallel batching + checkpoint per phase), safety gates, risk flags, output completeness gate.
- **SKILL.md Workflow Templates section**: Built-in workflows with short goal triggers. Skill handles methodology, scoring, batching, and safety rules automatically.
- **1688 SKU drill-down**: `ali1688_product_variations` enables SKU-level pricing beyond bait-pricing headlines.

### Fixed
- **1688 declared optional**: Not a completeness gate. COGS estimate used as fallback. 1688 inherent limitations documented (bait pricing, quality variability, MOQ mismatch). Bait-pricing compensation: 1688_low × 1.3.
- **Turn count**: 50 → 70 turns (60+ API calls require it). Output completeness gate prevents premature goal completion.
- **1688 Chinese keywords**: 1688 is a Chinese platform — must search with Chinese terms, not English.

---

## [2026-07-31]

### Fixed
- **MCP 2.0 compatibility hardening**: `requirements.txt` now locks `mcp>=1.0.0,<2.0.0` to prevent `pip install mcp` (defaults to 2.x) from silently breaking the skill. MCP 2.x has breaking API changes (`Server` → `MCPServer`, `stdio_server` signature change) that are not yet supported.
- **stdio_server bug**: Fixed `stdio_server(server)` → `stdio_server()` in bridge startup (line 4176). The `server` object was being incorrectly passed as `stdin` parameter, which would fail on some MCP versions.
- **Runtime MCP version guard**: Bridge now checks MCP version on startup via `importlib.metadata`. If 2.x is detected, prints a clear "MCP 2.x is not yet supported" error with the fix command (`python3 scripts/install.py --upgrade`), instead of cryptic `AttributeError` tracebacks.

### Added
- **install.py `--upgrade` flag**: `python3 scripts/install.py --upgrade` now force-reinstalls all dependencies (`--force-reinstall`). Used to downgrade from MCP 2.x to 1.x, or repair broken venv.
- **README maintenance section**: Troubleshooting table for common dependency errors (MCP 2.x, AttributeError, ModuleNotFoundError), plus update/upgrade workflow.

### Changed
- **SKILL.md Gotchas**: Added MCP SDK version lock as first gotcha item.

---

## [2026-07-30]

### Added
- Full 1688 toolchain verified: `ali1688_product_search` (multi-dimension supplier filtering), `ali1688_product_request` (16-field detail), `ali1688_product_variations` (SKU breakdown), `ali1688_product_search_from_image` (reverse image search)
- Shopee cross-border feasibility analysis: `shopee_product_search` with `shop_location` parameter (local vs cross-border seller comparison)
- Shopee cohort analysis: `Listed1Month/3Month/6MonthSalesVolumeRatio`, `FlagshipStoreMonthlySalesRatio`, `PreferredStoreMonthlySalesRatio`
- Shopee keyword favorites chain: add/get/change/delete with multi-dict management
- Cross-platform command template (platform selection, price arbitrage, product migration)
- Amazon toolchain audit: `product_reviews`, `product_traffic_terms`, `competitor_product_keywords`, `similar_product_feature`, `product_variations`, `product_customers_say`
- Walmart full toolchain verified: all 8 core tools, trend + variation sales as raw arrays
- Shopee command template expanded: 25→30 instructions, 70+ trend_index values documented

### Fixed
- Windows segfault: deferred `import mcp` for `--one-shot` path (no longer crashes on Windows)
- Windows `install.py` f-string escape: `{e}` → `{{e}}` in test_code template
- README GIF rendering: restored original `<img>` tag (GitHub doesn't support `<video>` in READMEs)
- `filter_50_products.py`: removed hardcoded developer path (`/Users/ddclaw/...`) — now uses `~/.sorftime-cache/tool-results/` with env var override

### Changed
- README: seller-centric rewrite with "Who Is This For" + 10 use cases
- README: updated supported platforms with full site lists per platform
- SKILL.md Gotchas: +10 new entries (1688 params, TikTok product_id trap, TEMU field names, Walmart raw arrays, Amazon parameter exceptions)

## [2026-07-29]

### Added
- Shopee 8-site full verification (MY/TH/VN/ID/PH/SG/TW/BR)
- TikTok US category seed data: 229 leaf categories + pre-computed sales rankings
- TikTok `discover_tiktok.py --sweep` parallel scanning mode (16min → 1-2min)
- Shopee 8-scenario live demo with verified data
- Shopee terminology reference (70+ terms with Amazon equivalents)

### Fixed
- SKILL.md platform site enums: Amazon corrected 12→14 sites, Walmart documented as US-only, TEMU documented as US+EU only
- Amazon parameter name traps: `product_customers_say` uses `site` (3rd param name variant)
- Branch protection enabled on main

### Changed
- GitHub topics: 12→20 (added `amazon-fba`, `amazon-product-research`, `keyword-research`, `competitor-analysis`, `mcp-server`, `cross-border-ecommerce`, `tiktok-shop`, `shopee`, `temu`, `open-source`)
- GitHub homepage: set to `open-intl.sorftime.com`

## [2026-07-28]

### Added
- Initial repository setup
- MCP bridge: 86 tools across 6 platforms
- 20 methodology cards for product discovery, competitor analysis, keyword strategy
- Multi-agent support: Claude Code, Codex, Cursor, OpenClaw, Hermes, Pi
- Auto-install script with environment detection
- Agent-agnostic demo GIF (4 terminals side by side)
