# Sorftime 闭环自动选品工作流 v3.3

```mermaid
flowchart LR
    START([🚀 /goal 命令]) --> P0

    subgraph P0["P0: 输入门"]
        direction TB
        I1["💰 预算"] --> I2["🏪 平台"]
        I2 --> I3["📊 阶段"]
        I3 --> I4["🏭 模式"]
        I4 --> I5["🎯 目标"]
    end

    P0 --> ROUTE{"路由推荐<br/>(卖家可覆盖)"}

    ROUTE -->|"Path 1: 单品狙击<br/>新手 · <$10K · 套利"| P1
    ROUTE -->|"Path 2: 赛道优先<br/>品牌 · 工厂 · 专业"| P2
    ROUTE -->|"Both: 全面扫描"| P2

    subgraph P1["Path 1: HPI 单品发现"]
        direction TB
        A1["potential_product<br/>全量 HPI 排名<br/>🛑 不做硬阈值"] --> A2["🛡️ 4级风险过滤<br/>排名后安全排除"] --> A3["📋 ≥10 产品初选<br/>标注 Edge Dark Horse"]
    end

    subgraph P2["Path 2: 市场全景分析"]
        direction TB
        B1["category_report × N<br/>11 维数据提取"] --> B2["📐 复合评分<br/>权重按阶段动态"] --> B3["🏆 TOP 3 优胜子类目"] --> B4["🔍 在优胜类目内<br/>potential_product 选品"] --> B5["📋 ≥10 产品<br/>来自 ≥2 子类目"]
    end

    P1 --> PIPE
    P2 --> PIPE

    subgraph PIPE["Phase B→E: 共用深度流水线"]
        direction LR
        C1["📦 PB: 深度验证<br/>detail·trend·traffic·reviews<br/>⚠️ exposure_position 字段<br/>🆚 差异化分析"] --> C2["🏭 PC: 供应链<br/>1688 中文搜索<br/>完全到岸成本<br/>首单数量建议"]
        C2 --> C3["💰 PD: 财务<br/>到岸 P&L<br/>真实净利润<br/>🛑 不做判决"]
        C3 --> C4["🛡️ PE: 风险<br/>4级·品牌·季节<br/>IP·合规·平台特有"]
    end

    PIPE --> D2

    subgraph D2["🆕 PD2: 7 个独立子 Agent 卖家评审团 (主 Agent 禁止投票)"]
        direction TB
        D2_INTRO["📦 每个产品: 完整数据包<br/>P&L + 趋势 + 流量 + 供应链 + 风险"] --> D2_SPAWN["⚡ Agent 工具 spawn 7 个子 Agent 并行运行"]
        D2_SPAWN --> D2_SEATS
        subgraph D2_SEATS["每个子 Agent 独立评审: 5 维评分(0-10) → 投票 GO/CAUTION/NO-GO → 写推理"]
            direction LR
            S1["🤖 Agent1<br/>Seat1 同行匹配<br/>同阶段·同预算·同模式<br/>权重 ×2"]
            S2["🤖 Agent2<br/>Seat2 同行备选<br/>同阶段·预算×0.8<br/>相反风险偏好"]
            S3["🤖 Agent3<br/>Seat3 导师视角<br/>高一级阶段卖家<br/>权重 ×1.5"]
            S4["🤖 Agent4<br/>Seat4 保守声音<br/>风险厌恶<br/>预算保护优先"]
            S5["🤖 Agent5<br/>Seat5 进取声音<br/>增长导向<br/>收益最大化"]
            S6["🤖 Agent6<br/>Seat6 平台专家<br/>Amazon/Walmart 深度<br/>权重 ×1.5 · 🚫否决权"]
            S7["🤖 Agent7<br/>Seat7 财务审计<br/>纯 P&L 核算<br/>🚫否决权"]
        end
        D2_SEATS --> D2_OUT["🗳️ 主 Agent 仅收集投票, 不参与判决<br/>🟢 GO: ≥4/7 GO 且 Seat6 ≠ NO-GO<br/>🔴 NO-GO: ≥4/7 NO-GO 或 Seat7 以 P&L 证据否决<br/>🟡 CAUTION: 其他 · 置信度 HIGH/MEDIUM/LOW<br/>📋 少数意见完整保留, 不隐藏"]
    end

    D2 --> PF

    subgraph PF["PF: 交付物"]
        direction TB
        F1["📊 Go/No-Go 决策表<br/>[VERIFIED]/[ESTIMATED]/[ASSUMED]/[UNAVAILABLE]"] --> F2["⭐ TOP3 深度解读"]
        F2 --> F3["🛡️ 风险登记表"]
        F3 --> F4["💰 预算利用率 + 首单计划"]
        F4 --> F5["📎 原始数据附录"]
    end

    PF --> PG

    subgraph PG["PG: 售后闭环"]
        direction TB
        G1["/loop 30d 监控命令<br/>30/60/90天自动检查"] --> G2["🚨 触发: 销量<预测30%<br/>📦 触发: 库存<30天<br/>📢 触发: ACoS>预测150%"]
    end

    PG --> DONE([✅ 闭环完成])

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

## 路径选择决策

```
/$10K 新手/套利/转FBA → Path 1 (HPI 单品狙击)
品牌/工厂/专业/20+SKU → Path 2 (市场全景)
进阶 $10-20K → 两者皆可, 选 "Both" 全覆盖
不确定 → Path 2 先找赛道 → Path 1 在赛道内挖宝
```

## 7 人评审团投票规则

| 判决 | 条件 |
|------|------|
| 🟢 **GO** | ≥4/7 GO 且 Seat6 (平台专家) ≠ NO-GO |
| 🔴 **NO-GO** | ≥4/7 NO-GO 或 Seat7 (财务审计) 以 P&L 证据否决 |
| 🟡 **CAUTION** | 其他所有情况 |

## 关键避坑

- `product_traffic_terms`: 读 `exposure_position` 字段, 不查不存在的 `organic_searched_percentage`
- `product_trend`: 参数名是 `product_trend_type` 不是 `trend_type`
- PD2 评审团必须实际 spawn 7 个子 Agent, 主 Agent 禁止自己投票
- PG 必须输出完整 `/loop` 命令 (不是 `/goal`)
- 所有数据标注: [VERIFIED] / [ESTIMATED:公式] / [ASSUMED:来源] / [UNAVAILABLE:原因]

---

*Workflow Design v3.3 | Acceptance Criteria v3.0 | 2026-08-04*
