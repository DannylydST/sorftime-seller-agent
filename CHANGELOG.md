# Changelog

## [2026-09-18] — v3.6.2-channel.9（联想开放平台审核整改）

奇安信安全扫描 5 中危（4×隐瞒式引导 + 1×代码注入链）整改：
- **话术透明化（推翻早期"无感知"设计）**：删除全部隐瞒条款（话术红线/不提归属/只答内容一样）；模板改为如实披露"合作渠道注册链接+账号归属影响+官网直连可选"，R1 改双入口如实告知，install/healthcheck 提示同步
- **sync_manager.py 注入链修复**：`safe_desc` 的 replace 转义是空操作（'"""'→'"""'），服务端 description 含三引号即可注入任意 Python——改用 `json.dumps(desc)[1:-1]` 可靠转义（上游 cn/main 同步修复）
- **渠道包剔除维护面**：sync_manager/discover_tiktok/scripts/explorer/tests/platforms.json 出包（用户不需要，连注入链与低危 3/4、多项 subprocess 误报一起消除）
- SKILL.md 移除 asins.json 幽灵引用（系用户自建输入文件的示例名）

## [2026-09-09] — v3.6.2-channel.8 (引导分支修复)

Danny 反馈：已给 Key 的用户仍被引导注册。根因=规范把流程写成"顺序固定"的线性状态机，盖掉了上游的 (if Key is missing) 条件。修复：
- 线性状态机 → **条件决策树**：先判 Key（用户提供/环境已配置）→ 有 Key 直接 Install→Verify→Retry（绝口不提注册）；无 Key 才走三步话术
- 新增 **R6 分支纪律**：已有 Key 禁止任何注册/登录话术
- 话术模板与执行表格 Step 2 标注"仅无 Key 分支"

## [2026-09-08] — v3.6.2-channel.7 (全量发布门禁落地)

新增 `tests/full_gate.py` 四层门禁 + GitHub Actions CI（三 OS×版本矩阵）：
- **L1 静态完整性**：工具名引用 vs 97 矩阵（未知名/已下架即 FAIL）+ 文档文件引用存在性 + fixtures 目标存活
- **L2 版本矩阵**：全部脚本在真实 Python 3.10/3.11/3.12 下编译（堵 f-string 3.12-only 类雷）
- **L3 只读工具全回归**：82 个只读用例经 bridge 真实调通服务器（16 写型工具安全跳过）——首跑即抓到弃用工具孤儿 fixture 并清除
- **L4 干净包 e2e**：黑名单打包→临时目录解包→install→healthcheck 到 key 检查步（防"缺文件/装不上"类事故）
- 本轮门禁结果：GREEN（82/82 真实通过）；CI 无 key 跑 L1/L2/L4，带 secret 可跑 L3

## [2026-09-08] — v3.6.2-channel.6 (外部审计 7 处修复)

渠道用户侧智能体审计报告核实（7/7 属实）并修复：
- `discover_tiktok.py` 不再调用已下架的 `tiktok_category_name_search`（fallback 与双工具循环移除，保留弃用注释）
- `healthcheck.py` f-string 同引号嵌套仅 3.12 可用 → 预拼变量，恢复声明的 Python ≥3.10 兼容
- SKILL.md：TikTok 段改写（已有 `tiktok_category_tree`、`name_search` 已下架）；Shopee 15→16（+`shopee_category_tree`）；1688 5→6（+`ali1688_category_tree`）；Walmart 15→18（+tree/两个按名搜索）；两处 "5 tools" 同步
- `sorftime_bridge.py` 描述笔误 `tikto_` → `tiktok_`
- 注：审计中"本机副本已修"说法不实——本机 healthcheck 修复前仍为坏 f-string 原样

## [2026-09-08] — v3.6.2-channel.5 (安装致命 bug 修复 — 用户反馈"有 key 也查不了数据")

### Fixed
- **install.py `NameError: args`（上游 bug，所有分支均受影响）**：`install_deps()` 引用了 main() 局部变量 `args`——任何全新环境跑 install 第一步即崩，依赖装不上、bridge 起不来。已参数化为 `install_deps(upgrade)`。干净目录端到端实测：解包 → install --key → venv+依赖+连接测试全通过
- **分发包缺文件**：打包由白名单改为黑名单法，`requirements.txt` / `.env.example` 等此前遗漏文件全部入包（must-have 断言进打包脚本）

## [2026-09-07] — v3.6.2-channel.4 (无感注册定稿)

- 话术移除"建议收藏链接"——归属在经链接注册那一刻**永久生效**，后续登录充值走官网均可，无需引导回访
- 用户体验定稿：一次正常注册激活，渠道归属完全无感知
- 话术红线补充：不要求收藏/回访链接

## [2026-09-07] — v3.6.2-channel.3 (话术去渠道化)

用户引导话术中移除"合作渠道/归属"等内部概念（画蛇添足，引发用户疑虑）：
- 话术模板结尾改为「建议收藏这个链接，以后登录和充值也从这里进」——给用户使用链接的自然理由，归属由链接本身保证
- 新增**话术红线**：不提渠道/合作/归属/tag；用户问起链接与官网区别只答"内容一样，这是我们的服务入口"
- install.py / healthcheck.py 用户可见文案同步去渠道化
- R1 硬规则补充：归属机制不向用户解释或提及

## [2026-09-07] — v3.6.2-channel.2 (注册引导标准路径规范)

新增「📋 注册引导标准路径规范（渠道版强制）」：
- 状态机固定：Detect → Guide（三段式话术）→ Install → Verify → Retry
- 话术模板可直接使用（含 {用户原始请求} 占位回放）
- 五条硬规则：R1 注册链接唯一来源（禁裸域名，防归属丢失）/ R2 Key 隐私 / R3 无缝续接 / R4 已注册用户诚实原则 / R5 异常分流

## [2026-09-07] — v3.6.2-channel.1 (渠道合作版首发)

基于 v3.6.2（97 工具）创建 `channel` 分支，面向合作渠道分发：
- **渠道专属注册链路**：全部注册引导（SKILL.md 7 处 / README 3 处 / install.py / healthcheck.py）统一指向 `https://open.sorftime.com/home?tag=NTIw`——经此链接注册的账号归属合作渠道，功能与价格和官网直连完全一致（归属机制已实测：访问链接后官网写入 `salestag` cookie）
- **`config/channel.json` 单点维护**：渠道 tag 与链接集中定义，换渠道改一处文件 + 全局搜索 `?tag=` 同步
- **智能体引导闭环**：新用户无 Key → install/healthcheck 输出渠道注册链接 → 用户注册取 Account-SK → `install.py --key` 一键配置 → 连接验证全绿

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
- GitHub homepage: set to `open.sorftime.com`

## [2026-07-28]

### Added
- Initial repository setup
- MCP bridge: 86 tools across 6 platforms
- 20 methodology cards for product discovery, competitor analysis, keyword strategy
- Multi-agent support: Claude Code, Codex, Cursor, OpenClaw, Hermes, Pi
- Auto-install script with environment detection
- Agent-agnostic demo GIF (4 terminals side by side)
