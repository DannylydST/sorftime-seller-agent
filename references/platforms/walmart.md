# Walmart Platform Guide

> Endpoint: `https://mcp.sorftime.com/walmart` · 18 tools · 纯前缀工具（`walmart_*`），无跨平台工具
> 站点：**US 单一市场**——18 个工具无一有 `site` 参数， marketplace 硬编码美国，不需要也不接受站点参数

## Parameter Traps（调错第一原因，先看这张表）

| 概念 | 实际分布（2026-10-10 活 schema） |
|------|------|
| 搜索词 | 关键词下产品用 `keyword`（`walmart_keyword_search_results`/`walmart_keyword_detail`/`walmart_keyword_extends`）；按名搜索用 `name`（`walmart_product_search_from_name`/`walmart_keyword_search_from_name`/`walmart_category_search_from_name`） |
| 产品 ID | 一律 `product_id`（非 asin） |
| 类目 ID | `node_id`，**字符串类型、可能含下划线**（如 `1072864_8490340`）；类目树用 `category_tree`（`node_id` 可选，不传=顶层） |
| 排名区间 | `keyword_list` 的 `rank_min`/`rank_max` **双双必填**（schema 标注 required） |
| 趋势类型 | `walmart_product_trend_by_product_id` 的 `trend_type` **必须英文枚举**，见下 |
| 日期 | `begin_date`/`end_date`，格式 `yyyy-MM-dd` |

## Tool Reference

### 关键词（5）
| 工具 | 必填 | 说明 |
|------|------|------|
| `walmart_keyword_search_results` | `keyword` | 关键词下自然位产品，**近 15 天**口径，按月销量降序；`page` 可选 |
| `walmart_keyword_detail` | `keyword` | 单词详情：搜索量/竞争度/均价概览。⭐2026-10-10 实测 `{"keyword":"yoga mat"}` 有真数据 |
| `walmart_keyword_list` | `rank_min`,`rank_max` | 热词榜（按月搜索量排名），推荐区间 `1-100`，每页 100 条；`page` 可选 |
| `walmart_keyword_extends` | `keyword` | 拓展词挖掘；`page` 可选 |
| `walmart_keyword_search_from_name` | `name` | 按名搜词；`page` 可选 |

### 产品（6）
| 工具 | 必填 | 说明 |
|------|------|------|
| `walmart_product_search_from_name` | `name` | 按产品名搜索；`page` 可选 |
| `walmart_product_detail_by_product_id` | `product_id` | 产品详情（价格/销量/评分/品牌/属性），**含 `NodeTree` 字段可反查类目**：`["类目名","node_id","Date","Rank"]` |
| `walmart_product_traffic_terms` | `product_id` | 流量词反查（含 `ShowShare` 曝光份额 + `RecentlyPosition`/`OrganicPosition`/`AdPosition` 排名位）；`page` 可选 |
| `walmart_product_trend_by_product_id` | `product_id` | 历史趋势。**`trend_type` 虽为 optional 但不传服务端报错**（"please enter the trend type to query"）；枚举：`SalesVolume`/`SalesAmount`/`Price`/`Rank`/`Reviews`/`Star`/`Unknown`。**不能用中文**；`begin_date`/`end_date` 可选 |
| `walmart_product_variation_sales_by_product_id` | `product_id` | 子体销量拆解；`begin_date`/`end_date`/`page` 可选。**无变体产品返回 "no relevant data"** |

### 类目（3）
| 工具 | 必填 | 说明 |
|------|------|------|
| `walmart_category_tree` | —（`node_id` 可选） | 类目树；不传 `node_id` 取顶层 |
| `walmart_category_search_from_name` | `name` | 按类目名搜索 |
| `walmart_category_report_by_node_id` | `node_id` | 类目实时 Top100 销量报告。**非法 `node_id` 返回 "no relevant data"**——先从 `NodeTree` 或搜索结果里取合法 ID |

### 收藏夹（5 件套）
`walmart_favorite_keyword`(`keyword`，可选 `dict` 指定清单名) · `walmart_get_favorite_keyword`（可选 `dict`，传 `all` 查全部） · `walmart_get_favorite_keyword_dict`（列清单名） · `walmart_change_favorite_keyword`(`keyword`,`to_dict`，可选 `from_dict`) · `walmart_del_favorite_keyword`(`keyword`，可选 `dict`)。关键词清单为空时返回 "no relevant data"

## Gotchas

- **`trend_type` 英文枚举硬约束**：`SalesVolume`/`SalesAmount`/`Price`/`Rank`/`Reviews`/`Star`，传中文或不传都报错；枚举首现 `Unknown`（占位值，勿用作查询）。
- **`keyword_list` 的 `rank_min`/`rank_max` 必填**：缺一服务端报错，非调用格式问题。
- **`node_id` 含下划线**：如 `1072864_8490340`，类型 string，从 `NodeTree` 或搜索结果提取，手拼易错。
- **趋势/变体销量返回扁平交错数组**：`walmart_product_trend_by_product_id` 与 `walmart_product_variation_sales_by_product_id` 返回 `[date,val,date,val,...]`（趋势约 730 个日度点、变体销量约 62 个），非 `[{date,value}]` 对象——用 `zip(data[::2], data[1::2])` 配对解析。
- **近 15 天数据口径**：`keyword_search_results` 只覆盖近 15 天自然位产品，按月销量降序——解释数据时勿当全量历史。
- **变体销量对无变体产品无数据**：`walmart_product_variation_sales_by_product_id` 遇无变体产品返回 "no relevant data"，先查 product_detail 确认有变体。
- **旧口径澄清**：旧文档记 `change_favorite_keyword` 参数为 `toDict`/`fromDict`（驼峰），**活 schema 为 `to_dict`/`from_dict`**（下划线），以 schema 为准。
- MCP SDK 锁 1.x、响应 `{doc,data}` 包裹、中文叙事前缀等通用坑 → `references/gotchas.md`
- 跨平台价差方法论卡（Cross-Platform Price Gap Index，双平台对比 Walmart vs Amazon）→ `references/methodology-cards/tactical/cross-platform-gap.md`；蓝海/低评论赢家等卡 Walmart 为主场之一 → `references/methodology-cards/`
