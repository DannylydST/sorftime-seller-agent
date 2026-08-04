# Sorftime Closed-Loop Product Selection Workflow v3.3

```mermaid
flowchart LR
    START([🚀 /goal Command]) --> P0

    subgraph P0["P0: Seller Input Gate"]
        direction TB
        I1["💰 Budget"] --> I2["🏪 Platform"]
        I2 --> I3["📊 Stage"]
        I3 --> I4["🏭 Model"]
        I4 --> I5["🎯 Goal"]
    end

    P0 --> ROUTE{"Auto-Route<br/>(Seller Overrides)"}

    ROUTE -->|"Path 1: Product Sniper<br/>Beginner · <$10K · Arb"| P1
    ROUTE -->|"Path 2: Market Mapper<br/>Brand · Factory · Pro"| P2
    ROUTE -->|"Both: Maximum Coverage"| P2

    subgraph P1["Path 1: HPI Product-First"]
        direction TB
        A1["potential_product<br/>Full HPI Ranking<br/>🛑 No Hard Thresholds"] --> A2["🛡️ 4-Tier Safety Filter<br/>After Ranking"] --> A3["📋 ≥10 Products<br/>Flag Edge Dark Horses"]
    end

    subgraph P2["Path 2: Market-First"]
        direction TB
        B1["category_report × N<br/>11-Dimension Data"] --> B2["📐 Composite Scoring<br/>Weights by Stage"] --> B3["🏆 Top 3 Subcategories"] --> B4["🔍 potential_product<br/>Within Winners"] --> B5["📋 ≥10 Products<br/>From ≥2 Subcategories"]
    end

    P1 --> PIPE
    P2 --> PIPE

    subgraph PIPE["Phase B→E: Common Deep-Dive Pipeline"]
        direction LR
        C1["📦 PB: Verification<br/>detail·trend·traffic·reviews<br/>⚠️ exposure_position field<br/>🆚 Differentiation"] --> C2["🏭 PC: Supply Chain<br/>1688 CN Keywords<br/>Full Landed Cost<br/>First-Order Qty"]
        C2 --> C3["💰 PD: Financials<br/>Landed P&L<br/>True Net Margin<br/>🛑 NO Verdict Here"]
        C3 --> C4["🛡️ PE: Risk<br/>4-Tier·Brand·Seasonal<br/>IP·Compliance·Platform"]
    end

    PIPE --> D2

    subgraph D2["🆕 PD2: 7 Independent Sub-Agent Seller Review Panel (Main Agent FORBIDDEN from Voting)"]
        direction TB
        D2_INTRO["📦 Per Product: Full Data Package<br/>P&L + Trends + Traffic + Sourcing + Risk"] --> D2_SPAWN["⚡ Agent Tool Spawns 7 Sub-Agents in Parallel"]
        D2_SPAWN --> D2_SEATS
        subgraph D2_SEATS["Each Sub-Agent: 5-Dimension Score(0-10) → Vote GO/CAUTION/NO-GO → Reasoning"]
            direction LR
            S1["🤖 Agent1<br/>Seat1 Peer Match<br/>Same Stage·Budget·Model<br/>Weight ×2"]
            S2["🤖 Agent2<br/>Seat2 Peer Alt<br/>Same Stage·Budget×0.8<br/>Opposite Risk"]
            S3["🤖 Agent3<br/>Seat3 Mentor<br/>One Stage Above<br/>Weight ×1.5"]
            S4["🤖 Agent4<br/>Seat4 Conservative<br/>Risk-Averse<br/>Capital Protection"]
            S5["🤖 Agent5<br/>Seat5 Opportunity<br/>Growth-Oriented<br/>Upside Maximizer"]
            S6["🤖 Agent6<br/>Seat6 Platform Specialist<br/>Amazon/Walmart Expert<br/>Weight ×1.5 · 🚫Veto"]
            S7["🤖 Agent7<br/>Seat7 Financial Auditor<br/>P&L-Only Analysis<br/>🚫Veto Power"]
        end
        D2_SEATS --> D2_OUT["🗳️ Main Agent Collects Votes Only<br/>🟢 GO: ≥4/7 GO AND Seat6 ≠ NO-GO<br/>🔴 NO-GO: ≥4/7 NO-GO OR Seat7 Veto with P&L Evidence<br/>🟡 CAUTION: Otherwise · Confidence HIGH/MEDIUM/LOW<br/>📋 Dissent Preserved, Never Hidden"]
    end

    D2 --> PF

    subgraph PF["PF: Final Deliverable"]
        direction TB
        F1["📊 Go/No-Go Decision Table<br/>[VERIFIED]/[ESTIMATED]/[ASSUMED]/[UNAVAILABLE]"] --> F2["⭐ TOP 3 Deep-Dive"]
        F2 --> F3["🛡️ Risk Registry"]
        F3 --> F4["💰 Budget + First-Order Plan"]
        F4 --> F5["📎 Raw Data Appendix"]
    end

    PF --> PG

    subgraph PG["PG: Post-Launch Loop"]
        direction TB
        G1["/loop 30d Monitoring<br/>30/60/90-Day Auto-Checks"] --> G2["🚨 Sales <30% Proj at D60<br/>📦 Stock <30d → Reorder<br/>📢 ACoS >150% Est at D45"]
    end

    PG --> DONE([✅ Closed Loop Complete])

    %% Styles
    style START fill:#4CAF50,color:#fff
    style DONE fill:#4CAF50,color:#fff
    style ROUTE fill:#FFD54F,color:#333
    style P0 fill:#E3F2FD
    style P1 fill:#E8F5E9
    style P2 fill:#BBDEFB
    style PIPE fill:#FFF3E0
    style D2 fill:#FCE4EC
    style PF fill:#E0F7FA
    style PG fill:#F1F8E9
```

---

## Path Selection Logic

```
Budget <$10K / Beginner / Arbitrage / Dropship→FBA → Path 1 (HPI Product Sniper)
Brand / Factory / Pro / 20+ SKU Portfolio       → Path 2 (Market Mapper)
Growing $10-20K                                  → Either, "Both" for full coverage
Unsure                                           → Path 2 first → Path 1 within winners
```

## 7-Member Panel Voting Rules

| Verdict | Condition |
|---------|-----------|
| 🟢 **GO** | ≥4/7 GO AND Seat6 (Platform Specialist) ≠ NO-GO |
| 🔴 **NO-GO** | ≥4/7 NO-GO OR Seat7 (Financial Auditor) veto with P&L evidence |
| 🟡 **CAUTION** | All other cases |

## Critical Gotchas

- `product_traffic_terms`: Read `exposure_position` ("Organic"/"Ad"/"Ad,Organic"), NEVER query non-existent `organic_searched_percentage`
- `product_trend`: Parameter is `product_trend_type`, NOT `trend_type`
- PD2 Panel: Must actually spawn 7 sub-agents. Main agent FORBIDDEN from voting.
- PG: Must output complete `/loop` command (NOT `/goal`)
- All data labeled: [VERIFIED] / [ESTIMATED:formula] / [ASSUMED:source] / [UNAVAILABLE:reason]

---

*Workflow Design v3.3 | Acceptance Criteria v3.0 | Validated: 20 rounds, 82.7% avg adoption | 2026-08-04*
