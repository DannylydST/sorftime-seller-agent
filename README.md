# Sorftime Seller Agent

> **Turn any AI agent into your personal marketplace intelligence analyst.**
>
> Agent-agnostic, MCP-native design. Works with **Claude Code, Codex, Cursor, OpenClaw, Hermes, Pi** — any MCP-compatible AI agent.
> Instant access to 86 marketplace analysis tools. Amazon · Walmart · TikTok Shop · 1688 · Shopee · TEMU.
>
> **No dashboards. No exports. Just talk to your AI.**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)]()
[![MCP](https://img.shields.io/badge/MCP-86%20tools-orange)]()
[![Agent-Agnostic](https://img.shields.io/badge/Agent-Claude%20%7C%20Codex%20%7C%20Cursor%20%7C%20OpenClaw-purple)]()

---

## ⚡ Quick Start

### 1. Get a free Sorftime account
Visit [open-intl.sorftime.com](https://open-intl.sorftime.com) — sign up with **Google**, free trial credits included. Payment via PayPal when you need more.

### 2. Install the skill
```bash
git clone https://github.com/DannylydST/sorftime-seller-agent.git
cd sorftime-seller-agent
python3 scripts/install.py
```

### 3. Ask your AI
```
"Find blue ocean products in yoga mats on Amazon US for a beginner"
"Analyze this competitor: ASIN B08N5WRWNW"
"Calculate my profit: price $29.99, cost $8.50, weight 1.2lb"
```

---

## 🤔 Why This Exists

Amazon sellers spend **$29–$229/month** on tools like Helium 10 and Jungle Scout. You log into dashboards, click through menus, export CSV files, then switch to another tool for analysis.

**Sorftime Seller Agent skips all that.** You talk to your AI assistant — any MCP-compatible agent — and it queries marketplace data directly, analyzes it with a framework of 20 proprietary methodology cards, and gives you actionable insights.

```
Before: Log in → navigate → click → export → analyze manually  (15–30 min)
After:  "Find blue ocean yoga mat products" → results in 20 seconds
```

---

## 🧠 What It Can Do

|     | Capability | What You Say |
|-----|-----------|--------------|
| 🔍 | **Product Discovery** | "Find blue ocean kitchen products under $30" |
| 🎯 | **Competitor Intelligence** | "Break down ASIN B08N5WRWNW — traffic, keywords, pricing" |
| 🔑 | **Keyword Strategy** | "What are the best long-tail keywords for yoga mats?" |
| 💰 | **Profit Analysis** | "Calculate seller profit: $29.99 price, $8.50 cost, 1.2lb" |
| 📊 | **Market Intelligence** | "Analyze the blender category — monopoly, trends, gaps" |
| 📈 | **Automated Monitoring** | "Watch this product and alert me when the price drops" |

---

## 🤖 Agent-Friendly by Design

This skill is built as an **agent-agnostic MCP-native skill** from the ground up. It's not a Claude Code plugin. It's not a wrapper around an API. It's a self-contained MCP bridge + intelligence layer that any MCP-compatible AI agent can load and use immediately.

| Agent / IDE | How It Works | Setup |
|-------------|-------------|-------|
| **Claude Code** | `mcporter` auto-detection, one-command install | < 3 min |
| **Codex (OpenAI)** | Import as MCP server, natural language queries | < 5 min |
| **Cursor** | MCP config snippet from `install.py`, auto-detected | < 3 min |
| **OpenClaw** | Native skill directory support, auto-safeBin config | < 3 min |
| **Hermes** | MCP server import, JSON config | < 5 min |
| **Pi (Inflection)** | MCP endpoint registration | < 5 min |
| **Any MCP Agent** | Standard MCP `tools/list` → `tools/call` protocol | < 5 min |

**What makes it agent-agnostic:**

- **MCP-first architecture** — Every capability is a standard MCP tool (86 tools, auto-synced with Sorftime's server)
- **Zero agent-specific code** — No Claude-specific prompts, no Cursor-specific config. Pure MCP protocol
- **Auto-detection** — `install.py` detects your environment and outputs the right config snippet
- **Self-contained** — Ships with its own Python venv, bridge, cache, and schema store. No external deps beyond Python 3.10+
- **Bilingual routing** — Understands English and Chinese input, routes to the right analysis pipeline regardless of which agent you use

---

## 🆚 How It Compares

| | Helium 10 | Jungle Scout | **Sorftime Seller Agent** |
|---|-----------|-------------|--------------------------|
| **Interface** | GUI dashboards | GUI dashboards | **AI conversation** |
| **Platforms** | Amazon only | Amazon only | **6 platforms** |
| **Data depth** | Basic metrics | Basic metrics | **160+ dimensions + proprietary indices** |
| **AI integration** | None | None | **MCP-native, agent-agnostic** |
| **Works with** | GUI only | GUI only | **Claude Code · Codex · Cursor · OpenClaw · Hermes · Pi · any MCP agent** |
| **Automation** | Manual workflows | Manual workflows | **Agent auto-execution** |
| **Pricing** | $29–$229/mo | $29–$129/mo | **Free tier + paid** |
| **Setup time** | 20+ min | 20+ min | **3 minutes** |

---

## 📦 Installation

**Prerequisites**: Python 3.10+ · A Sorftime account ([free signup](https://open-intl.sorftime.com)) · Any MCP-compatible AI agent

```bash
# Clone the repo
git clone https://github.com/DannylydST/sorftime-seller-agent.git
cd sorftime-seller-agent

# One-click install (creates venv, installs deps, configures MCP)
python3 scripts/install.py

# Verify everything works
python3 scripts/healthcheck.py
```

That's it. Your AI agent can now access 86 marketplace intelligence tools.

**Platform support**: macOS · Linux · Windows (all Python 3.10+ environments)

---

## 💬 Example Conversations

### Find products in an untapped niche
> **You**: "Find blue ocean products in kitchen storage on Amazon US. I'm a beginner seller with $5K budget."
>
> **Agent**: *[Scans Hidden Profit Index, filters by low competition, beginner-friendly categories]*
> "Here are 5 opportunities with low brand concentration, <500 reviews on top listings, and healthy margins. #1: Under-sink organizers — 15K monthly searches, only 3 competitors with >100 reviews."

### Analyze a competitor
> **You**: "Analyze ASIN B08N5WRWNW — give me their traffic keywords and pricing strategy."
>
> **Agent**: *[Pulls ProductDetail, TrafficTerms, CompetitorKeywords]*
> "Gaiam Yoga Block — 40K monthly sales, 4.7 stars, $18.99. Top 3 traffic keywords: 'yoga block' (52K), 'yoga blocks 2 pack' (28K), 'cork yoga block' (15K). FBA fee: $12.82. Threat assessment: medium."

### Calculate profitability
> **You**: "I'm sourcing yoga mats at $8.50/piece. I want to sell at $29.99, weight 1.2lb. Should I?"
>
> **Agent**: *[Runs Calculator with FBA fee estimate]*
> "Gross margin: 38%. Break-even: 9 units/day. Return rate sensitivity: profit stays positive up to 12% returns. Verdict: viable — proceed."

### Research keywords
> **You**: "What keywords should I target for a new yoga mat listing?"
>
> **Agent**: *[KeywordDetail, KeywordExtends, KeywordSearchResults]*
> "Top opportunities: 'extra thick yoga mat' (147K searches, low competition), 'non slip yoga mat' (98K), 'yoga mat with strap' (52K). Avoid 'yoga mat' (1.4M searches, saturated — dominated by Amazon Basics and Gaiam)."

### Cross-platform arbitrage
> **You**: "Are there products selling higher on Walmart than Amazon?"
>
> **Agent**: *[Cross-platform gap analysis using Sorftime dual-platform data]*
> "Found 3 products with significant price gaps. 'Premium Yoga Block Set' — $34.99 on Walmart vs $24.99 on Amazon (40% premium). Only 3 sellers on Walmart vs 12 on Amazon."

---

## 🌍 Supported Platforms

| Platform | Data Available | Coverage |
|----------|---------------|----------|
| **Amazon** | Products · Keywords · Categories · Reviews · Traffic · Trends · Profit | 14 sites |
| **Walmart** | Products · Keywords · Categories · Traffic · Trends · Variations | US |
| **TikTok Shop** | Products · Categories · Authors · Videos · Trends | US |
| **Shopee** | Products · Keywords · Categories · Shops · Trends | Multi-region |
| **TEMU** | Products · Categories · Shops · Trends | Multi-region |
| **1688** | Products · Variations · Similar items | CN |

---

## 🙋 FAQ

**Q: Is this official Sorftime?**
Yes. Built by [@DannylydST](https://github.com/DannylydST) at Sorftime Data Technology. The skill connects to Sorftime's official MCP API ([open-intl.sorftime.com](https://open-intl.sorftime.com)).

**Q: Do I need to pay?**
New accounts get **free trial credits**. Paid plans available via PayPal when you need more.

**Q: What AI tools work with this?**
Any MCP-compatible agent — **Claude Code, Codex (OpenAI), Cursor, OpenClaw, Hermes, Pi**, and more. If your AI speaks MCP, it can use Sorftime. The `install.py` script auto-detects your environment.

**Q: How do I get my MCP Key?**
Sign up at [open-intl.sorftime.com](https://open-intl.sorftime.com) → MCP page → copy Key.

**Q: Can I use this without an AI agent?**
Yes — you can call the CLI tools directly: `python3 scripts/picker.py --keyword "yoga mat"`. But the full power comes from AI-driven analysis with the 20 methodology cards.

**Q: What's included in the 20 methodology cards?**
Proprietary analysis frameworks like **Hidden Profit Index, Blue Ocean Finder, Competitor Deep-Dive, Keyword Strategy** — full-ranking models that show you everything (no hard thresholds that hide borderline products). See `references/methodology-cards/`.

---

## 📄 License

MIT © [DannylydST](https://github.com/DannylydST) · Sorftime Data Technology

---

*Built for sellers. By sellers.*
