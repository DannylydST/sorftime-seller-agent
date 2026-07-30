# sorftime-agent-x-standalone 用户场景验证用例

> 目标：验证纯 MCP 技能在 20 个典型用户场景下的可靠性、触发准确性、无 CLI 交叉引用

## 选品与发现场景（5 个）

### S1: 蓝海选品
**用户输入**: "帮我在亚马逊美国站找厨房收纳的蓝海机会"
**预期**: 触发技能 → 路由到 `picker.py --mode blueocean --platform amazon --site US --keyword "kitchen storage"` → 返回隐赚指数排名
**验证点**: 正确路由、参数提取正确、无 sf-batch.py 引用

### S2: 新手选品
**用户输入**: "我是新手，资金有限，帮我在瑜伽垫类目找找机会"
**预期**: 触发 → `picker.py --mode newbie --platform amazon --site US --keyword "yoga mat"` → 自动启用四级风险过滤
**验证点**: 识别"新手"→ newbie profile、无硬阈值表述

### S3: 隐赚指数
**用户输入**: "全品类扫一遍隐赚指数排名"
**预期**: 触发 → `sorftime_bridge.py --one-shot potential_product '{"amz_site":"US"}'` → 全品类拉通排序
**验证点**: 不传 search_name 参数、解释隐赚指数是 Sorftime 独家综合推荐分（相对值），而非逐个维度拆解

### S4: 季节性选品
**用户输入**: "圣诞节相关的产品有什么好的切入机会"
**预期**: 触发 → `tactical/seasonal-position.md` 方法论卡片 → 季节性爆发指数分析
**验证点**: 正确路由到卡片、无 CLI 执行映射

### S5: 1688 货源
**用户输入**: "看看 B08N5WRWNW 这个产品在 1688 上的采购成本"
**预期**: 触发 → `ali1688_similar_product` MCP 工具

## 竞品分析场景（5 个）

### S6: 竞品拆解
**用户输入**: "帮我拆解 ASIN B0CVM8TXHP 这个竞品"
**预期**: 触发 → `analyst.py --mode competitor --platform amazon --site US --asin B0CVM8TXHP` + `competitor-deepdive.md` 卡片
**验证点**: 返回流量词、定价、评论痛点全维度、无 workflow-competitor-deep.sh 引用

### S7: 竞品关键词反查
**用户输入**: "B08N5WRWNW 这个产品在哪些关键词有曝光"
**预期**: 触发 → `product_traffic_terms` MCP 工具 → 输出关键词列表 + 展示份额

### S8: 市场全景
**用户输入**: "分析一下空气炸锅类目的市场全景"
**预期**: 触发 → `market-panorama.md` 卡片 → 11 维度综合评分 → 无 workfow-market-panorama.sh

### S9: 评论洞察
**用户输入**: "看看 B0CVM8TXHP 的差评都集中在哪些问题"
**预期**: 触发 → `product_reviews` + `review-mining.md` 卡片 → 痛点严重度指数排名

### S10: 流量结构
**用户输入**: "帮我分析这个 ASIN 的流量来源结构"
**预期**: 触发 → `traffic-structure.md` 卡片 → 自然流量健康度指数

## 运营优化场景（5 个）

### S11: 利润计算
**用户输入**: "算一下，售价 $29.99，成本 $8.5，FBA 发货 1.2 磅，利润多少"
**预期**: 触发 → `calculator.py --platform amazon --price 29.99 --cost 8.5 --weight 1.2` → 毛利率/盈亏平衡日销量

### S12: Listing 诊断
**用户输入**: "帮我诊断 B0CVM8TXHP 的 Listing 有哪些可以优化的"
**预期**: 触发 → `listing-audit.md` 卡片 → 关键词覆盖缺口指数

### S13: 定价策略
**用户输入**: "这个类目 3743561 的价格带怎么分布的"
**预期**: 触发 → `pricing-position.md` 卡片 → 价格带机会指数

### S14: 品牌缺口
**用户输入**: "瑜伽垫类目有没有品牌垄断的缺口可以切入"
**预期**: 触发 → `brand-gap-entry.md` 卡片 → 品牌垄断脆弱度指数

### S15: 轻小件利润
**用户输入**: "找轻小件高利润产品，FBA 费用越低越好"
**预期**: 触发 → `lightweight-profit.md` 卡片 → 利润效率指数（全量排序，非 minPrice≥$20）

## 多平台与管理场景（5 个）

### S16: Walmart 选品
**用户输入**: "帮我在 Walmart 上找瑜伽垫的选品机会"
**预期**: 触发 → `walmart_picker.py --mode blueocean --keyword "yoga mat"` → 评论阈值 <200

### S17: TikTok 达人
**用户输入**: "看看 TikTok 上做瑜伽垫带货的达人有哪些"
**预期**: 触发 → `tiktok_author` MCP 工具

### S18: 内容审核
**用户输入**: "帮我审核这篇文章能不能发官方号"
**预期**: 触发 → 内容审核流程：竞品替换测试 → 烂大街测试 → 五维评分

### S19: 首次配置
**用户输入**: "帮我配置 Sorftime MCP"
**预期**: 触发 onboarding → `healthcheck.py` → 引导获取 Key → `install.py --unattended`

### S20: 无 CLI 引用验证
**用户输入**: "分析完了，帮我批量跑一下这些 ASIN"
**预期**: → 使用 MCP 工具分批调用 + Python 循环实现，**不出现** sf-batch.py / workflow-*.sh / sorftime-cli 任何字样。不提"切换到 CLI"
