---
name: sorftime-seller-agent
description: "Sorftime Seller Agent — Expert-level cross-border e-commerce data analysis and product sourcing intelligence for Amazon, Walmart, TikTok Shop, 1688, Shopee, and TEMU sellers. A single skill that turns any MCP-enabled AI agent (Claude Code, OpenClaw, Cursor, Copilot) into a Sorftime marketplace intelligence expert. Covers product discovery, competitor analysis, keyword strategy, profit calculation, ASIN deep-dive, blue ocean finding, market intelligence, and more. Auto-adapts output for beginner, growing, and professional seller stages."
trigger: "sorftime/product sourcing/competitor/keyword/profit/market intelligence/ASIN/category/blue ocean/seasonal/amazon/tiktok/shopee/temu/walmart/hidden profit/supply chain/monitor/analyze this data/review this product/content review/MCP debug/bridge/install/market panorama/competitor deep-dive/keyword strategy/blue ocean finder/listing audit/review mining/pricing strategy/traffic structure/negative review replacement/brand monopoly/brand gap/keyword scatter/lightweight profit/FBA fee/seasonal products/variant gap/new product burst/FBM to FBA/cross-platform price gap/listing optimization/price band/sweet spot/hidden profit index/ecommerce seller/seller tools/选品/竞品/关键词/利润/市场看板/ASIN/类目/蓝海/季节性/隐赚/货源/监控"
version: 3.0.0
user-invocable: true
metadata:
  openclaw:
    emoji: "🛒"
    requires:
      bins: ["python3"]
      env: ["SORFTIME_MCP_KEY"]
    primaryEnv: "SORFTIME_MCP_KEY"
---

# Sorftime Seller Agent

> One skill. Any AI agent. Instant marketplace intelligence for global sellers.

## 🔴 Language Rule (Mandatory)

**Match the user's language. Always.** If the user writes in English → respond in English. If the user writes in Chinese → respond in Chinese. Never mix. This overrides everything else in this skill.

## Core Positioning

This skill is the **single unified entry point** for all Sorftime MCP capabilities. It integrates:

- **MCP Bridge Layer**: Direct access to Sorftime's full suite of data tools (current count in `references/tool-matrix.md`, auto-synced)
- **Intelligence Layer**: Product discovery engine, competitor analysis, keyword optimization, profit calculation, monitoring & alerts
- **Output Adaptation Layer**: Auto-formats results by seller stage (Beginner / Growing / Professional)
- **Content Quality Layer**: Quality guidelines for AI-generated content output
- **Platform Exploration Layer**: Automated discovery of Sorftime modules and fields

**Users describe what they need — the skill auto-routes to the right scripts and tool chains.**

---

### ⚠️ MCP Parameter Name Traps (Must Read — Highest Frequency Pitfall)

> **The same business concept uses DIFFERENT parameter names across different Sorftime tools.** With 86+ tools, parameter naming is not consistent between product, keyword, category, and cross-platform tools.

**Always verify the actual `inputSchema.properties` of the target tool before calling it.** Never guess parameter names based on what another tool uses.

**Most common parameter mismatch errors:**

| Concept | Product Tools Use | Keyword Tools Use | Category Tools Use | Cross-Platform Use |
|---------|:---:|:---:|:---:|:---:|
| Search term | `search_name` | `keyword` | `category_name` / `product_name` | — |
| Marketplace | `amz_site` | `keyword_support_site` | `amz_site` | `site` |
| Category ID | `node_id` | — | `top_node` | `node_id` |
| Product ID | `asin` | — | — | `product_id` |

**Typical failure scenarios:**
- Using `product_search`'s `search_name` parameter on `keyword_detail` → fails. Correct: `keyword`
- Using `amz_site` on `keyword_list` → fails. Correct: `keyword_support_site`
- Using `node_id` on `category_search_from_top_node` → fails. Correct: `top_node`

**How to avoid:**
1. **Check Schema before calling**: `mcp_client.py` has built-in parameter validation + auto-correction. Common aliases (e.g. `search_name` → `keyword`) are auto-corrected with a stderr notification
2. **If it fails, check parameter names FIRST**: An `isError` response is most likely a wrong parameter name — not a server outage
3. **When adding new tools, add aliases**: If new tools use different naming conventions, add a mapping in `scripts/utils/mcp_client.py`'s `PARAM_ALIASES`

---

## 🌐 Sorftime International Platform

> **Platform URL**: https://open-intl.sorftime.com — the dedicated international platform for global sellers.

### Registration & Account

| Item | Detail |
|------|--------|
| **Sign-Up** | https://open-intl.sorftime.com → "Log In / Sign Up" |
| **Login Methods** | Google account (recommended) or email/password |
| **Free Trial** | New accounts receive **free trial credits** — start using MCP immediately without payment |
| **Payment** | PayPal (credit/debit cards via PayPal checkout) |
| **MCP Key Location** | After login → navigate to the **MCP** tab → copy your Key |
| **Contact** | Email: service@sorftime.com |

### Product Access

| Product | Status | Description |
|---------|--------|-------------|
| **MCP** | ✅ Live | AI agent toolset — plug-and-play model integration for Claude, Cursor, etc. |
| **CLI** | 🔜 Coming Soon | Command-line client for scripting and batch processing |
| **API** | 🔜 Coming Soon | HTTP data interface for custom system integration |

### Supported Platforms
Amazon · Walmart · Shopee · TikTok · TEMU · 1688 — across 21 global sites.

---

## 🚀 Agent Onboarding Protocol (Mandatory)

> **Goal**: When a user first says "help me find products" or provides a Key, the agent MUST auto-detect → guide → install → retry, without throwing technical errors.

### Trigger Conditions (any one triggers onboarding)

1. User explicitly says configuration-related things: "configure Sorftime" / "first time" / "how to start" / "here's my key"
2. User directly provides a Key (any string that looks like an API key)
3. A data request fails with `[SORFTIME_ONBOARDING_REQUIRED]` or `SORFTIME_MCP_KEY not set`

### Execution Flow (must follow order)

#### Step 1 — Detect
Run `python3 scripts/healthcheck.py` to quickly determine which is missing: Key, dependencies, or MCP connection.

#### Step 2 — Guide to Get Key (if Key is missing)
If the user hasn't provided a Key, proactively provide the acquisition path:
- Registration URL: https://open-intl.sorftime.com — Sorftime International (overseas) platform
- Sign up with **Google account** or email/password
- After registration, navigate to the **MCP** page at https://open-intl.sorftime.com/mcp to copy your MCP Key
- **New users get free trial credits** upon registration — no payment required to start
- Payment options: PayPal (credit card via PayPal)
- Suggested phrasing: "Create a free account at open-intl.sorftime.com (Google login supported), grab your MCP Key from the MCP page, and I'll set everything up. New accounts come with free trial credits."

#### Step 3 — Auto-Install
Once you have the Key, immediately run:
```bash
python3 scripts/install.py --unattended --key <user-provided-Key>
```
- `--unattended` ensures no interactive prompts
- Result is JSON: `{"status":"ok","key_saved":true,"test_passed":true}`

#### Step 4 — Mandatory Post-Success Action
- **If onboarding was triggered by a data request** (e.g. "help me find products") → **MUST retry the original request** and return results to the user
- If onboarding was an explicit user request → confirm success and provide a testable example (e.g. `get_time` or a simple product search)

#### Step 5 — Failure Handling
If `install.py` returns `test_passed: false` or `status: error`:
1. Check if the Key was copied completely (common: missing trailing characters)
2. Confirm the Sorftime account has MCP service enabled
3. Check network connectivity to `open-intl.sorftime.com`
4. Report the specific error to the user with next-step suggestions

### First-Time User Guide (Simplified for Users)

| Step | User Action | Agent Action |
|------|-------------|--------------|
| 1 | Say "help me find products" or "configure Sorftime" | Detect configuration status |
| 2 | Create a free account at https://open-intl.sorftime.com (Google login or email). Go to MCP page and copy your Key. Send to agent. | Auto-run `install.py --unattended --key <Key>` |
| 3 | Wait 10-20 seconds | Auto-test connection, save config, retry original request |
| 4 | Start using immediately with free trial credits | — |

### FAQ Quick Reference

| Problem | Solution |
|---------|---------|
| "[SORFTIME_ONBOARDING_REQUIRED]" | Immediately execute onboarding flow (Steps 1-4) |
| "Connection test failed" | Check Key completeness / account MCP status / network to open-intl.sorftime.com |
| Don't know where to get Key | Direct user to https://open-intl.sorftime.com → register (Google login supported) → MCP page → copy Key |
| "Schema is X days old" | Run `python3 tests/auto_sync.py` to pull latest tool schemas |
| How to pay / pricing | Direct user to https://open-intl.sorftime.com — PayPal supported. Free trial credits available on registration. |

---

## Scenario Routing Table (Mandatory)

| User Says | Internal Route | Key Script |
|-----------|---------------|------------|
| "find products" / "blue ocean" / "market opportunity" / "product discovery" | → Discovery Engine + Stage Adaptation | `picker.py --mode <newbie\|blueocean>` |
| "analyze this ASIN" / "competitor analysis" / "traffic keywords" | → Competitor Analysis | `analyst.py --mode competitor` |
| "keyword research" / "long-tail keywords" / "search terms" | → Keyword Analysis | `analyst.py --mode keyword` |
| "calculate profit" / "break-even" / "FBA fees" | → Profit Calculator | `calculator.py` |
| "monitor price" / "watch this product" / "daily report" | → Monitoring Engine | `monitor.py --mode add/daily/alert` |
| "TikTok/TEMU/Shopee + analysis" | → Multi-Platform Router | `platform_router.py --platform <name>` |
| "Walmart product discovery/analysis" | → Walmart Automation | `walmart_picker.py` / `walmart_analyst.py` |
| "review my content" / "quality check" | → Content Quality Guidelines | Execute guidelines flow (see below) |
| "configure Sorftime" / "first time" / "MCP Key" | → Auto Onboarding | `install.py --unattended --key <KEY>` |
| "explore Sorftime" / "what features exist" / "available fields" | → Platform Explorer | `explorer/*.js` + Playwright |
| "install/debug/run tests" / "MCP not connecting" | → Bridge Operations | `install.py` / `run_tool_tests.py` / `healthcheck.py` |

### Methodology Card Routing (v3.0)

When users mention specific tactical scenarios, route to the corresponding methodology card for the complete analysis framework. Cards located in `references/methodology-cards/`.

| User Says | Route to Card | Key Script + Index |
|-----------|--------------|-------------------|
| "analyze market" / "market panorama" / "is it worth it" | → `comprehensive/market-panorama.md` | `picker.py` + 11-dimension composite score |
| "competitor deep-dive" / "compare competitors" | → `comprehensive/competitor-deepdive.md` | `analyst.py --mode competitor` + Threat Index |
| "keyword strategy" / "keyword layout" / "search optimization" | → `comprehensive/keyword-strategy.md` | `analyst.py --mode keyword` + Opportunity Index |
| "find blue ocean" / "blue ocean categories" / "market gaps" | → `comprehensive/blue-ocean-finder.md` | `picker.py --mode blueocean` + Hidden Profit Index ⭐ |
| "listing audit" / "optimize listing" / "title optimization" | → `comprehensive/listing-audit.md` | Keyword Coverage Gap Index |
| "review analysis" / "negative review insights" / "buyer pain points" | → `comprehensive/review-mining.md` | Pain Point Severity Index |
| "pricing strategy" / "price positioning" / "price bands" | → `comprehensive/pricing-position.md` | Price Band Opportunity Index |
| "traffic analysis" / "traffic sources" / "organic traffic" | → `comprehensive/traffic-structure.md` | Organic Traffic Health Index |
| "hidden profit index" / "hidden profit" / "hidden gems" / "undervalued products" | → `tactical/invisible-profit.md` ⭐ (独家方法论) | `potential_product` + Sorftime 独家 Hidden Profit Index — 全维度加权综合评分，专门发现"评论少但卖得好、广告费低但利润高"的被忽视产品 |
| "low rating replacement" / "low rating opportunity" / "improve product" | → `tactical/low-review-winner.md` | Replacement Opportunity Index (full ranking, not maxRating≤4.2) |
| "brand monopoly" / "brand concentration" / "brand gap" | → `tactical/brand-gap-entry.md` | Brand Monopoly Vulnerability Index |
| "keyword scatter" / "search dispersion" / "traffic dispersion" | → `tactical/keyword-scatter.md` | Keyword Opportunity Index |
| "lightweight products" / "low FBA fee" / "high profit light goods" | → `tactical/lightweight-profit.md` | Profit Efficiency Index (full ranking, not minPrice≥$20) |
| "seasonal" / "holiday selection" / "peak season positioning" | → `tactical/seasonal-position.md` | Seasonal Boom Index |
| "variant gap" / "variant opportunity" / "missing child ASINs" | → `tactical/variant-gap.md` | Variant Gap Index |
| "new product burst" / "new bestseller" / "new product tracking" | → `tactical/new-product-burst.md` | New Product Burst Index |
| "FBM to FBA" / "fulfillment arbitrage" | → `tactical/fbm-arbitrage.md` | FBA Conversion Arbitrage Index |
| "cross-platform price gap" / "Walmart vs Amazon" | → `tactical/cross-platform-gap.md` ⭐ | Cross-Platform Price Gap Index (Sorftime exclusive dual-platform) |
| "listing optimization" / "poor listing" / "optimization takeover" | → `tactical/poor-listing-grab.md` | Listing Optimization Potential Index |
| "price band gap" / "pricing sweet spot" | → `tactical/price-band-sweetspot.md` | Demand Density ÷ Competitor Density |

### Methodology Core Principle (Differentiator vs Competitors)

**Full ranking, no hard thresholds.** Each methodology card uses weighted index full-ranking — a $19.99 product won't disappear because it's $0.01 below a threshold, and a 4.3-star product won't be excluded for being 0.1 above a cutoff. Sellers see the complete picture and make their own decisions.

**vs Other Solutions:**

| Dimension | Other Solutions | Sorftime |
|-----------|----------|----------|
| Filtering | Hard thresholds (`minPrice≥$20 AND maxRating≤4.2`) — cliff effect | Full-ranking by composite index — no blind spots |
| Data Depth | Basic metrics | 160+ dimensions + proprietary indices |
| AI Integration | Limited, manual operation | MCP-native, 86 standardized tools for AI agents |
| Platform Coverage | Amazon only | 40+ platforms |
| Interface | GUI-heavy, steep learning curve | CLI + AI Agent, natural language |

---

## 🛡️ Parameter Discipline (READ BEFORE ANY TOOL CALL)

**The #1 recurring failure: guessing parameters instead of checking the schema.** This must stop.

### Mandatory: Schema-First Protocol

Before calling ANY Sorftime MCP tool, you MUST verify exactly 3 things:

| # | Check | How |
|---|-------|-----|
| 1 | **Required parameters** | `grep -A30 '"<tool_name>"' scripts/sorftime_bridge.py` — read `required` array |
| 2 | **Parameter names** (case-sensitive!) | Same grep — read `properties` keys. `node_id` ≠ `nodeId` ≠ `nodeid` |
| 3 | **Enum values** | `amz_site` must be `"US"`/`"GB"`/`"DE"` etc., NOT `"amazon.com"` or `"美国"` |

### Common Parameter Traps

| Wrong (Agent guesses) | Correct (Schema says) | Tool affected |
|------------------------|----------------------|---------------|
| `"yoga US"` (free text) | `{"node_id":"3743561","amz_site":"US"}` | `category_keywords` |
| `"yoga US 7月"` | `{"node_id":"3743561","start_date":"2026-07-01","end_date":"2026-07-31","amz_site":"US"}` | `category_report_from_history` |
| `"amzSite":"US"` | `"amz_site":"US"` | Amazon tools |
| `"site":"US"` | `"amz_site":"US"` | Amazon tools (not TikTok/Shopee) |
| `"keywordSupportSite"` | `"amz_site"` (some tools), `"keyword_support_site"` (others) | Varies by tool |
| Missing `node_id` entirely | `node_id` is required in `category_keywords`, `category_report`, etc. | Category tools |
| Date `"2025H1"` | `"2025-01-01"` / `"2025-06-30"` (yyyy-MM-dd, max 40-day range) | `category_report_from_history` |

### Quick Schema Lookup

```bash
# Dump any tool's full parameter spec in one line:
python3 -c "
import json, ast, sys
src = open('scripts/sorftime_bridge.py').read()
# Find the tool schema block
start = src.index('\"name\": \"$TOOL_NAME\"')
block = src[start:start+3000]
# Parse out required params and properties
print(block)
"
```

### If a Tool Returns "No relevant data" or Code=10

1. **DO NOT** conclude "the tool is broken" or "data doesn't exist"
2. **DO** re-check the 3 schema checks above
3. **DO** test with the exact parameters from a known-working call
4. Only after verifying correct parameters 3 times → then escalate as possible data gap

---

## ⚡ Loop & Goal Automation

For recurring tasks (daily competitor monitoring, weekly keyword refresh, monthly Hidden Profit Index scan), use Claude Code's `/loop` and `/goal` commands with pre-built templates. **58 battle-tested recipes** covering all seller stages and platforms are available in the Wiki:

→ **[Loop & Goal Command Templates](https://github.com/DannylydST/sorftime-seller-agent/wiki/Loop-Goal-Command-Templates)**

Example — Weekly Hidden Profit Index refresh:
```
/loop 7d Run Hidden Profit Index TOP20 for keywords "yoga mat"/"resistance bands".
      Compare with last week. Highlight top 3 fastest-rising products.
```

---

## Execution Principles

1. **Identify first, then execute**: Complex requests → use `router.py` or `persona.py` to identify intent and seller stage, then route to methodology card
2. **Ask when information is insufficient**: Never guess ASINs, keywords, or marketplaces — ask
3. **Schema freshness check**: At the first Sorftime usage in each session, run `python3 scripts/healthcheck.py`. If it reports "Schema is X days old" (>7 days), **proactively notify the user**: "Schema is X days old — new tools may be available on the server. Sync now?" — only sync after user confirmation (`python3 tests/auto_sync.py`). Never silently sync (involves file modification). If a tool call returns "not found" or "unsupported", the first step is to suggest syncing Schema
4. **Cache-first**: Repeated queries auto-hit SQLite cache (`~/.sorftime-cache/`)
5. **Structure results**: Raw JSON must be formatted before presenting to users — never dump raw JSON
6. **Out of scope**: Log unsupported requests to `~/.sorftime-cache/unsupported-requests.log` and provide alternatives
7. **Batch scenarios**: When users say "batch/bulk/monitor/scheduled", use MCP tools with batched calls + Python scripts; space requests appropriately to avoid rate limiting

---

## I. Data Intelligence Layer (Discovery / Competitor / Profit / Monitoring)

### 1.1 Discovery Engine `picker.py`

```bash
# Default: beginner seller profile (strictest filtering)
python3 scripts/picker.py --mode newbie --platform amazon --site US --keyword "kitchen storage"
python3 scripts/picker.py --mode blueocean --platform amazon --site US --keyword "pet supplies"

# Factory-direct seller profile (allows capital-intensive and operations-complex categories)
python3 scripts/picker.py --mode blueocean --platform amazon --site US --keyword "yoga mat" --profile factory

# Per-category override: allow capital-intensive (clothing/shoes/bags) but still filter traps
python3 scripts/picker.py --mode blueocean --platform amazon --site US --keyword "dress" --allow-capital

# View seller profile descriptions
python3 scripts/picker.py --profile-help
```

**Auto-analysis dimensions:**
- Brand monopoly (top 3 brands > 40% market share → alert)
- Amazon Basics penetration
- Low-review high-sales opportunities (reviews < 100 but high sales volume)
- Price wars (< $10 clustering → avoid)
- Beginner-friendliness (auto-apply reviews < 500, monopoly coefficient < 40%)
- **Quantified risk summary**: estimated return rate, initial capital requirement, inventory turnover days, brand concentration, new product survival rate, price dispersion

**Four-Tier Risk Filtering System (v2.0):**

| Risk Level | Category Coverage | Default Filter | Override Switch |
|------------|-------------------|---------------|-----------------|
| 🔴 **Hard Block** | Food/beverage/supplements/medical devices/functional cosmetics/baby food/pesticides/alcohol | All profiles | `--allow-hard` (⚠️ not recommended) |
| 🟡 **Capital-Intensive** | Apparel/shoes/bags/jewelry/wigs/furniture/mattresses/large appliances/bicycles | Beginner + Growing | `--allow-capital` |
| 🟠 **Operations-Complex** | Electronics/liquids/flammables/IP-licensed/auto parts/safety equipment/BBQ grills/glass fragile items | Beginner only | `--allow-ops` |
| ⚠️ **Trap Signals** | Fake reviews/merged reviews/price wars/red ocean/seasonal/heavy goods/hijacking/size hell | All profiles | `--skip-traps` (⚠️ not recommended) |

**Seller Profiles:**

| Profile | Hard Block | Capital | Operations | Traps | Suitable For |
|---------|-----------|---------|------------|-------|-------------|
| `newbie` | ✅ | ✅ | ✅ | ✅ | Beginners, limited capital |
| `grower` | ✅ | ✅ | ❌ | ✅ | Growing sellers, moderate risk tolerance |
| `pro` | ✅ | ❌ | ❌ | ✅ | Professional sellers with teams |
| `factory` | ✅ | ❌ | ❌ | ✅ | Factory-direct, supply chain advantage |
| `brand` | ✅ | ❌ | ❌ | ✅ | Brand owners, in-house compliance |

**Other high-risk categories** (not auto-filtered, but flagged during analysis):
- Accessories (hats/scarves/gloves/socks/belts): 5-15% return rate
- Eyewear/sunglasses: 10-20% return rate, prescription/style issues
- Phone cases/screen protectors: extreme red ocean, razor-thin margins, patent minefield
- Stationery/office supplies: low ASP, thin margins, commoditized
- Holiday decorations: extremely short sales window, post-season inventory risk
- Books/CD/DVD: low margins, shrinking market

**Transparent filtering**: Every excluded product shows its specific reason and risk level, helping sellers understand the rationale. Experienced sellers can use `--profile` or per-category overrides to see the full analysis.

### 1.2 Analyst Engine `analyst.py`

```bash
python3 scripts/analyst.py --mode competitor --platform amazon --site US --asin B08N5WRWNW
python3 scripts/analyst.py --mode keyword --platform amazon --site US --keyword "yoga mat"
python3 scripts/analyst.py --mode market --platform amazon --site US --node-id 1064954
```

### 1.3 Profit Calculator `calculator.py`

```bash
python3 scripts/calculator.py --platform amazon --price 29.99 --cost 8.5 --weight 1.2
```

Output: gross margin, break-even daily sales, return rate sensitivity. FBA fee is estimated by weight — verify with actual dimensional weight from product detail.

### 1.4 Monitoring Engine `monitor.py`

```bash
python3 scripts/monitor.py --mode add --type asin --value B08N5WRWNW --platform amazon --site US
python3 scripts/monitor.py --mode daily
python3 scripts/monitor.py --mode alert
```

---

### 1.5 Walmart Discovery Engine `walmart_picker.py`

```bash
# Walmart blue ocean discovery (default: newbie profile, strictest filtering)
python3 scripts/walmart_picker.py --mode blueocean --keyword "yoga mat"

# Walmart beginner-friendly discovery (reviews < 200, price $15-40)
python3 scripts/walmart_picker.py --mode newbie --keyword "kitchen storage"

# Factory-direct seller profile
python3 scripts/walmart_picker.py --mode blueocean --keyword "toy" --profile factory
```

**Walmart-specific adaptations:**
- Review threshold < 200 (Amazon is < 500), reflecting Walmart's overall lower review counts
- Auto-analyzes Walmart self-operated (1P) share, WFS penetration
- Reuses the four-tier risk filtering system

### 1.6 Walmart Analyst Engine `walmart_analyst.py`

```bash
# Competitor analysis (detail + traffic keywords + sales/rating trends)
python3 scripts/walmart_analyst.py --mode competitor --product-id 15689567602

# Keyword analysis (detail + long-tail keywords + top products)
python3 scripts/walmart_analyst.py --mode keyword --keyword "toilet paper"

# Market analysis (category report + top product profiles + category overview)
python3 scripts/walmart_analyst.py --mode market --node-id 5438
```

---

## II. Output Adaptation Layer (Seller Stage Detection & Formatting)

**Must call `persona.py` first to identify stage:**

```bash
python3 scripts/persona.py --text "I'm a beginner, looking for blue ocean products on Amazon US"
```

Then format by stage:

```bash
python3 scripts/stage_formatter.py --stage beginner --input /tmp/result.md
```

| Stage | Output Characteristics |
|-------|----------------------|
| **beginner** | Explains terminology, emphasizes "why this matters" and "what to do next" |
| **growing** | Highlights data changes, opportunities, competitive risk alerts |
| **pro** | Direct conclusions, recommends batch/API solutions, minimal preamble |

---

## III. Content Quality Layer

When the user asks "review my content" / "quality check", follow these guidelines:

### Step 1: Context-Aware Review
- Check if the content references specific data points without citing them
- Verify any competitive claims are substantiated
- Ensure tone and format match the intended audience (sellers, developers, etc.)

### Step 2: Quality Dimensions

**A. Factual Accuracy**
> Verify any data claims, statistics, or assertions against available Sorftime data.

**B. Actionability**
> Does the content enable the reader to take a specific next step?
> Vague advice → flag for improvement. Concrete, data-backed guidance → passes.

**C. Brand Consistency**
> Does the content align with Sorftime's positioning as AI-Powered Marketplace Intelligence?

**D. Audience Fit**
> Is the technical depth appropriate for the target audience (beginner/growing/pro)?

### Step 3: Output Scoring (0-100)

| Score | Verdict |
|-------|---------|
| ≥ 75 | ✅ Ready to publish |
| 40-74 | 🔄 Needs revision (provide specific fixes) |
| < 40 | ❌ Do not publish (fundamental issues) |

---

## IV. Platform Exploration Layer (Feature Map / Field Verification)

When user says "explore Sorftime" / "what features are available" / "available fields" / "verify fields":

```bash
# Example: extract all field definitions from a page
node scripts/explorer/content-capture.js <url>
```

Core principles:
- One module at a time
- Existence ≠ usable — must click to verify
- Use checkbox to select data rows (5+ rows) to trigger comparison
- Save checkpoint after each tab switch
- `*.sorftime.com` goes DIRECT (no proxy)

---

## V. MCP Bridge & Operations Layer

### 5.1 Installation

```bash
python3 scripts/install.py
```

Auto-completes: virtual environment creation, CC/OpenClaw detection, prompts for `SORFTIME_MCP_KEY`, connection test, config snippet output.

### 5.2 Quick Tool Invocation

```bash
# Test connection
python3 scripts/sorftime_bridge.py --one-shot get_time '{}'

# Product search
python3 scripts/sorftime_bridge.py --one-shot product_search '{"amz_site":"US","search_name":"kitchen storage"}'

# Hidden Profit Index ⭐ (Sorftime 独家方法论)
# 全品类跨排名 — 综合评分发现被忽视的高利润潜力产品。不传 search_name 即为全品类拉通排序
python3 scripts/sorftime_bridge.py --one-shot potential_product '{"amz_site":"US"}'

# Hidden Profit Index — 关键词/类目内筛选
python3 scripts/sorftime_bridge.py --one-shot potential_product '{"amz_site":"US","search_name":"yoga mat"}'
```

### 5.3 Full Test Suite

```bash
python3 tests/run_tool_tests.py
```

### 5.4 Schema Auto-Sync

When Sorftime MCP server updates tools (add/remove/modify schemas), the skill auto-detects and syncs.

```bash
# Full sync: fetch server schema → diff → generate → apply
python3 scripts/sync_manager.py full

# Detect changes only (no writes)
python3 scripts/sync_manager.py diff

# Auto-sync entry (executes when changes detected)
python3 tests/auto_sync.py
```

Sync scope:
- `scripts/sorftime_bridge.py` — update `_FALLBACK_CORE_TOOLS` with latest server schema
- `references/tool-matrix.md` — regenerate categorized tool matrix
- `tests/fixtures/*.yaml` — update test case parameter structures
- `~/.sorftime-cache/schema-store/` — versioned storage, supports rollback

Each sync auto-creates backup in `.sync-backups/`, with one-click rollback:
```bash
python3 scripts/sync_manager.py rollback YYYYMMDD_HHMMSS
```

### 5.5 Drift Detection

```bash
python3 tests/drift_detector.py
```

Compares local `references/tool-matrix.md` against `scripts/sorftime_bridge.py`'s `_FALLBACK_CORE_TOOLS`. Alerts on inconsistency. Note: this checks local file consistency only, not against the server.

---

## VI. Multi-Platform Parameter Quick Reference

| Platform | Marketplace Param | Product ID Param | Keyword Param | Category Param |
|----------|-------------------|------------------|---------------|----------------|
| Amazon | `amz_site` (AE/AU/BR/CA/DE/ES/FR/GB/IN/IT/JP/MX/SA/US) | `asin` | `search_name` | `node_id` |
| TikTok | `site` (US/GB/ID/JP/MY/PH/TH/VN) | `product_id` | — | `node_id` (⚠️ not `category_id`) |
| Shopee | `site` (MY/PH/VN/TH/ID/SG/TW/BR) | `product_id` | — | `category_id` |
| TEMU | `site` (US/EU) | `product_id` | — | `category_id` |
| Walmart | — (US only, no site param) | `product_id` | `keyword` | `node_id` |
| 1688 | — (China only) | `product_id` | — | — |

**Amazon parameter name traps** (3 different names for "marketplace"):
- `amz_site`: 19 tools (product_search, product_detail, category_report, potential_product, etc.)
- `keyword_support_site`: 12 tools (keyword_detail, keyword_extends, keyword_search_results, keyword_list, etc.)
- `site`: 1 tool — `product_customers_say` (⚠️ exception to the Amazon convention)
- All 14 Amazon sites verified in schema; SG is NOT in the enum (contrary to older docs).

### Walmart Tool Usage Guide

Walmart marketplace parameter is always `site`, currently supports `US`. All Walmart tools prefixed with `walmart_`.

**Core Query Tools:**

| Tool | Required Fields | Optional Fields | Description |
|------|----------------|-----------------|-------------|
| `walmart_keyword_search_results` | `keyword` | `page` | Organic-ranking products (last 15 days) |
| `walmart_keyword_detail` | `keyword` | — | Search volume/competition/avg price overview |
| `walmart_keyword_list` | `rank_min`, `rank_max` | `page` | Hot keyword ranking (by monthly search volume) |
| `walmart_keyword_extends` | `keyword` | `page` | Keyword expansion mining |
| `walmart_product_detail_by_product_id` | `product_id` | — | Product detail (price/sales/rating/brand/attributes) |
| `walmart_product_traffic_terms` | `product_id` | `page` | Reverse-lookup traffic keywords (with impression share/rank position) |
| `walmart_product_trend_by_product_id` | `product_id` | `trend_type`, `begin_date`, `end_date` | Historical trends: `SalesVolume`/`SalesAmount`/`Price`/`Rank`/`Reviews`/`Star` |
| `walmart_product_variation_sales_by_product_id` | `product_id` | `begin_date`, `end_date`, `page` | Child ASIN sales breakdown |
| `walmart_category_report_by_node_id` | `node_id` | — | Real-time category Top 100 sales report |

**Favorites Tools:**

| Tool | Required Fields | Description |
|------|----------------|-------------|
| `walmart_favorite_keyword` | `keyword` | Add keyword to favorites, optional `dict` for list name |
| `walmart_get_favorite_keyword` | — | Query favorited keywords, optional `dict` (`all` for all) |
| `walmart_get_favorite_keyword_dict` | — | Query favorites list names |
| `walmart_change_favorite_keyword` | `keyword`, `toDict` | Move keyword to target list, optional `fromDict` |
| `walmart_del_favorite_keyword` | `keyword` | Delete keyword, optional `dict` for specific list |

**Key Field Notes:**
- `trend_type` enum values: **`SalesVolume`** / `SalesAmount` / `Price` / `Rank` / `Reviews` / `Star` — **cannot use Chinese values**
- `rank_min`/`rank_max` in `walmart_keyword_list` are **required** — server errors without them
- `node_id` format: Walmart category IDs may contain underscores (e.g. `1072864_8490340`), type **string**
- Product detail's `NodeTree` field can reverse-lookup category: `["Category Name", "node_id", "Date", "Rank"]`

**Known Limitations:**
- `walmart_product_variation_sales_by_product_id`: some products without variants return "no relevant data"
- `walmart_category_report_by_node_id`: invalid `node_id` returns "no relevant data" — extract valid IDs from `NodeTree` or search results
- Favorites tools return "no relevant data" when keyword list is empty

---

## VII. Gotchas

- **MCP SDK version lock**: This skill requires **MCP 1.x** (not 2.x). `requirements.txt` locks to `mcp>=1.0.0,<2.0.0`. MCP 2.x has breaking API changes (`Server` → `MCPServer`, `stdio_server` signature change). If bridge startup shows "MCP 2.x is not yet supported" or `AttributeError: 'Server' object...`, run `python3 scripts/install.py --upgrade` to downgrade to 1.x.
- **Schema auto-sync**: `healthcheck.py` checks schema freshness. If it reports "Schema is X days old", run `python3 tests/auto_sync.py` to pull the latest tool list — the server may have added new tools. Sync updates `references/tool-matrix.md`, `sorftime_bridge.py` schemas, and `tests/fixtures/`. Recommended: weekly, or immediately when a tool call returns "tool not found"
- **🚫 ANTI-PATTERN: Never pre-filter HPI with hard thresholds.** Do NOT pass `price_min`/`price_max`/`month_sales_volume_min`/`review_count` filters to `potential_product` before ranking. The Hidden Profit Index exists to surface products that traditional filtering kills. Verified test (2026-08-03): passing `price $15-45, sales>200` to "kitchen storage" eliminated the #1 HPI product ($59.99, HPI 13.38) and the #7 HPI product ($8.99, HPI 13.22). **Correct sequence**: (1) full HPI ranking with NO filters → (2) safety exclusion via 4-tier risk filter only → (3) analyze why each product ranks high → (4) flag what hard thresholds would have missed → (5) let the seller decide. See [Wiki: Case Study](https://github.com/DannylydST/sorftime-seller-agent/wiki/Exclusive-Methodology#-case-study-products-the-hidden-profit-index-found-2026-08-03).
- When `SORFTIME_MCP_KEY` is not set, the bridge raises `RuntimeError` — configure the env var or run `install.py` first
- `potential_product` (Hidden Profit Index ⭐ — Sorftime exclusive methodology). `search_name` parameter is **optional**: omit for **all-category cross-ranking**, include to filter within a keyword's search results. Returns `potential_index` — a **composite recommendation score (relative value)**, not a single-dimension absolute metric. Higher scores indicate stronger overall performance across "low entry barrier, low ad spend, high profit margin" dimensions. When explaining to sellers, focus on the logic behind the index (finding overlooked high-profit products), not per-dimension breakdown calculations. ⚠️ **CRITICAL: A high HPI score does NOT override category risk.** Always cross-check results against the four-tier risk filter (hard-block/capital-intensive/operations-complex/trap-signals) before presenting to sellers. Food, supplements, electronics compliance, seasonal products, and licensed/branded goods must be excluded or flagged regardless of HPI. See `references/methodology-cards/tactical/invisible-profit.md#risk-notes` for the full exclusion table
- Amazon keyword tools (`keyword_detail` / `keyword_extends` / `keyword_search_results`) use `keyword_support_site` for marketplace; all other Amazon tools use `amz_site`. **⚠️ Exception: `product_customers_say` uses `site`** (not `amz_site`), the only Amazon tool to do so. **See the "MCP Parameter Name Traps" section above — parameter name mismatches are the #1 cause of call failures**
- TikTok Shop currently does not provide `product_search`; direct search needs to `product_detail` or `category_report`
- **⚠️ TikTok has NO `category_tree` endpoint** (unlike Amazon/Shopee/TEMU). The two search tools (`tiktok_category_name_search` / `tiktok_category_search_from_name`) only discover **leaf-level** categories by keyword — they cannot enumerate top-level categories or traverse parent-child hierarchies. Exact-matching official top-level names (e.g. "Beauty & Personal Care") returns nothing or unrelated leaves. This is a known server-side gap. See `references/tiktok-rankings.json` for the pre-computed workaround.
- **TikTok category discovery SOP** (always tier 1 first):
  1. **TIER 1 (0s, 0 API calls)**: Read `references/tiktok-rankings.json` — pre-computed rankings of 228 leaf categories with monthly sales, MoM, avg price, and heuristic parent-category aggregation. Covers the vast majority of active categories. Use for: "top categories", "what's selling", market overview questions.
  2. **TIER 2 (~1min, batch API)**: `python3 scripts/discover_tiktok.py --sweep` — parallel keyword scan to refresh or expand category coverage. Use when: rankings are stale (>7 days) or searching for a niche not in the rankings. Auto-persists to `references/tiktok-categories.json`.
  3. **TIER 3 (per-call API)**: `python3 scripts/discover_tiktok.py <keyword>` — single-keyword search. Use for: targeted lookup of one specific category name. Do NOT use for broad discovery — TIER 2 is faster and more complete.
  Anti-patterns: Do NOT iterate letters brute-force. Do NOT call tools without `site`. Do NOT expect exact-match top-level category names to work.
- **Shopee trend tools return flat interleaved arrays**, not `[{date, value}]` objects. Both `shopee_category_trend` and `shopee_product_trend` return `[date1, val1, date2, val2, ...]`. Parse by pairing: `list(zip(data[::2], data[1::2]))`. Date elements are integers in `YYYYMMDD` format (daily) or `YYYYMM` (monthly), not ISO strings. `shopee_product_trend` accepts optional `query_start` / `query_end` (format `yyyy-MM-dd`) to scope the date range; omitting them defaults to ~1 year.
- **Shopee `shopee_category_trend` has 72+ `trend_index` values** (default: `MonthlySalesVolume`). Key ones: `MonthlySalesVolume`, `MonthlySalesAmount`, `AveragePrice`, `AverageStarRating`, `SellerCount`, `BrandCount`, `FlagshipStoreRatio`, plus time-windowed variants (`Listed1Month*`, `Listed3Month*`, `Top3*`, `Top10*`). Always check the schema enum for the full list — it's extensive and covers market concentration, new-product dynamics, and store-type breakdowns.
- **Shopee `shopee_keyword_search` looks up the keyword index, not product listings**. It accepts partial/prefix matching (e.g. "phone" finds "phone lanyard"; case-insensitive). Multi-word phrases like "phone case" may return no data if they aren't indexed as a keyword. To browse hot keywords without a search term, pass `{"rank_min": 1, "rank_max": N}`. For product discovery by freeform search term, use `shopee_keyword_relation_results` — note this returns **products** (with fields: title, product_id, sales_count, price, ratings, shop_name), not related keywords, despite the tool name.
- **TikTok `tiktok_category_report` top50 products do NOT include `product_id`** — the report is market overview only (title/brand/sales/price/seller/ratings). To get a product_id for detail/trend/video analysis, use `tiktok_product_detail` or discover via keyword search.
- **TEMU product field is `product_name`** (not `title` like Amazon/Shopee). `temu_category_request` returns product_id + product_name, usable for downstream `temu_product_trend` / `temu_product_request`.
- **Shopee `shopee_product_search` `shop_location` parameter**: 1=本土店 (local), 2=跨境店 (cross-border). Use for cross-border feasibility analysis — compare page_count between the two. Response is nested: `data.products[]` not `data[]`.
- **Shopee keyword favorites tools return raw arrays** (not `{doc, data}` wrapper). `shopee_favorite_keyword` add returns "Favorite succeeded" in error-format JSON. `shopee_get_favorite_keyword_dict` returns `["dict_name", ...]`, `shopee_get_favorite_keyword` returns `["keyword", ...]`. Don't expect the standard response envelope.
- **Shopee site enum (8 站全部实测通过)**: `MY`, `PH`, `VN`, `TH`, `ID`, `SG`, `TW`, `BR` (plus `UnKonw` default). All 15 Shopee tools share the same site list. Always pass `site` explicitly — it's optional in schema but server behavior without it is inconsistent.
- **Python API**: Prefer the bridge CLI (`python3 scripts/sorftime_bridge.py --one-shot <tool> '<json>'`) for one-off calls — it handles all path/env complexity. If you need programmatic access:
  ```python
  import sys; sys.path.insert(0, 'scripts')  # REQUIRED — utils is under scripts/
  from utils.mcp_client import call_tool, call_tool_json
  ```
  `call_tool(name, args)` returns str. `call_tool_json(name, args)` returns parsed dict. Do NOT try `import MCPClient` or `import mcp_client` — those names don't exist. Never run `python3 -c "from utils..."` from outside the skill root directory.
- Some Sorftime tools return Chinese narrative prefix before JSON — `utils/mcp_client.py` and `sorftime_bridge.py` handle this parsing
- Requests beyond registered tool scope: `utils/mcp_client.py` auto-remaps deprecated tools or intercepts with alternatives
- `mcporter` HTTP transport may intermittently break on large responses — complex queries prefer `--one-shot` main path
- `picker.py` defaults to `--profile newbie` (strictest filtering). Switch profiles via `--profile grower/pro/factory/brand` or use per-category overrides (`--allow-capital` / `--allow-ops`). Filtered products are listed in report with specific risk level and reason
- `--explicit-category` is backward-compatible, equivalent to `--allow-capital --allow-ops`
- **Schema auto-sync**: `sorftime_bridge.py` loads dynamic schema from `schema_store` on startup; falls back to `_FALLBACK_CORE_TOOLS` if never synced. Run `python3 tests/auto_sync.py` regularly
- **Walmart `trend_type` must be in English**: `walmart_product_trend_by_product_id`'s `trend_type` uses English enum values (`SalesVolume`/`SalesAmount`/`Price`/`Rank`/`Reviews`/`Star`) — **cannot use Chinese**. Server returns "please enter the trend type to query" if omitted
- **Walmart `rank_min`/`rank_max` required**: `walmart_keyword_list` requires both `rank_min` and `rank_max`. Recommended range `1-100`, 100 results per page
- **Walmart category ID format**: `node_id` is string, may contain underscores (e.g. `1072864_8490340`). Extract from product detail's `NodeTree`: `["Category Name", "node_id", "Date", "Rank"]`
- **Walmart data scope**: search results cover last 15 days of organic-ranking products, sorted by monthly sales descending. Traffic keyword data includes `ShowShare` (impression share) and `RecentlyPosition`/`OrganicPosition`/`AdPosition` (recent/organic/ad rank positions)
- **Amazon `product_reviews` may return "No reviews found"** — try a higher-volume ASIN. The tool returns rich review data (35+ reviews with variant_attribute/review_date/star_rating/title) when available. `product_traffic_terms` + `competitor_product_keywords` confirmed working (keyword-level search volume/bid/exposure data). `similar_product_feature` uses `product_name` parameter (not `asin` — auto-corrected). `product_customers_say` uses `site` (not `amz_site`) — the only Amazon tool diverging from both `amz_site` and `keyword_support_site`. `category_report_from_history` and `category_keywords` returned no data in tests — possibly limited server-side historical/ keyword coverage.
- **Amazon `product_variations` returns child ASINs but variant attributes may be empty** — the tool returns 55+ child ASINs but `attribute` and `month_sales_volume_range` may be blank for some products. Verify data quality before using.
- **Walmart `walmart_product_trend_by_product_id` and `walmart_product_variation_sales_by_product_id` return raw interleaved arrays** like Shopee trend tools: `[date, val, date, val...]`. 730 daily data points for trends, 62 for variation sales. Parse with `zip(data[::2], data[1::2])`.
- **1688 tools have 5 endpoints** (verified 2026-07-30): `ali1688_similar_product` (keyword search, returns 100 items with title/price/product_id/store_name/service_score/sales_of_30d), `ali1688_product_search` (multi-dimension filter with 20+ params including supplier_type:1=实力商家/2=超级工厂, repurchase_rate, rights: "1,2,3", service_score), `ali1688_product_request` (detail: price/moq/supplier_info, 16 fields), `ali1688_product_variations` (SKU breakdown: price/stock/weight/dimensions per variant), `ali1688_product_search_from_image` (reverse image search). `ali1688_product_search` params are all optional — pass none to browse, or combine filters for precision sourcing. Supplier type codes: 1=实力商家, 2=超级工厂.

---

## VIII. Tool Matrix

Complete tool list and counts in `references/tool-matrix.md` (auto-sync generated, always matches server).

Core frequently-used tools:
`get_time`, `category_report`, `product_search`, `product_detail`, `product_reviews`, `product_variations`, `product_traffic_terms`, `keyword_detail`, `keyword_search_results`, `keyword_extends`, `potential_product`, `category_name_search`, `category_search_from_top_node`, `similar_product_feature`, `competitor_product_keywords`, `ali1688_similar_product`, `tiktok_category_report`, `tiktok_product_detail`, `sorftime_raw_call`

**Walmart core tools (14):**
`walmart_keyword_search_results`, `walmart_keyword_detail`, `walmart_keyword_list`, `walmart_keyword_extends`, `walmart_product_detail_by_product_id`, `walmart_product_traffic_terms`, `walmart_product_trend_by_product_id`, `walmart_product_variation_sales_by_product_id`, `walmart_category_report_by_node_id`, `walmart_favorite_keyword`, `walmart_get_favorite_keyword`, `walmart_get_favorite_keyword_dict`, `walmart_change_favorite_keyword`, `walmart_del_favorite_keyword`

> **Walmart is US-only**: none of the 15 Walmart tools have a `site` parameter — the marketplace is hardcoded to US. No parameter needed.
>
> **1688 is China-only**: 5 tools, no site parameter. Factory-direct sourcing only.
>
> **TEMU currently supports US + EU only** (2 sites). TEMU has the richest category-level filtering (40+ optional filter params on `temu_category_search`).
>
> **TikTok site availability varies**: 8 sites in the schema, but VN returns "No data available" for category searches. GB/JP/ID/MY/PH/TH/US confirmed working.

---

## IX. Cross-Platform Adaptation & Migration

This skill is cross-platform compatible, supporting macOS / Linux / Windows.

### Environment Variables (Optional)

| Variable | Purpose | Default |
|----------|---------|---------|
| `SORFTIME_MCP_KEY` | MCP authentication key | Read from `.env` |
| `SORFTIME_CACHE_DIR` | Cache/data directory | `~/.sorftime-cache` (Windows: `%LOCALAPPDATA%\sorftime-cache`) |
| `SORFTIME_HTTP_TIMEOUT` | MCP request timeout (seconds) | `30.0` |
| `SORFTIME_SCHEMA_AUTO_SYNC` | Auto-sync Schema on startup | `false` |
| `SORFTIME_PROXY` | HTTP proxy address | None |

### Migrating to a New Device

1. Copy the skill directory to the new machine
2. Ensure Python >= 3.10 is installed
3. Run `python3 scripts/install.py` to rebuild the virtual environment
4. Provide `SORFTIME_MCP_KEY`, or manually write to the skill root `.env`

### Auto-Detected Agent Environments

Claude Code, OpenClaw, Cowork, Claude.ai Web, and other mainstream environments are auto-detected — no manual configuration needed.

### Related Files

- `scripts/utils/platform_utils.py` — Cross-platform utility functions
- `scripts/utils/version.py` — Version management
- `requirements.txt` — Dependency list
