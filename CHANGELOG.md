# Changelog

All notable changes to Sorftime Seller Agent.

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
