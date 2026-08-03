# Changelog

All notable changes to Sorftime Seller Agent.

---

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
