# TEMU Platform Guide

> Endpoint: `https://mcp.sorftime.com/temu` · 10 tools · 仅 US/EU 两站
> Site param: `site` — 枚举 `Unknown US EU`，实际可用站点为 `US` / `EU` 两站（`Unknown` 是占位枚举值，别当站点用）

## Parameter Traps（调错第一原因，先看这张表）

| 概念 | 实际分布（2026-10-10 活 schema） |
|------|------|
| 搜索词 | `temu_product_search_from_name` 用 `name`；`temu_category_search_from_name` 用 `name`；类目下筛选用 `temu_category_search` 的 `node_id` 而非名称 |
| 站点 | 9 个工具统一用 `site`（US/EU），传 `Unknown` 语义未定义，别传 |
| 类目 ID | `node_id`（`temu_category_tree` 用 `node_id` 下钻） |
| 产品 ID | `product_id`（TEMU 产品字段是 **`product_name`**，不是 Amazon/Shopee 的 `title`，别对 TEMU 结果找 `title`） |
| 店铺 ID | `shop_id` |
| 日期 | `temu_product_trend` 用 `query_start` / `query_end` |

## Tool Reference

### 类目（4）
| 工具 | 必填 | 说明 |
|------|------|------|
| `temu_category_search` | —（全可选） | 类目级筛选搜索，**全 Sorftime 类目级筛选最丰富的工具**：20 组筛选维度（40 个 min/max 参数）——月销/销量份额/环比/销售额/价格/平均评论数/平均星级/卖家数/品牌数/Top10 产品销量份额/Top10 卖家销量份额/半托管店铺数/半托管店铺销量/半托管累计销量/明星卖家数/明星卖家月销量/新品数/新品销量/新品销量份额，外加 `node_id` 圈类目。蓝海类目发现与类目横向对比的主工具 |
| `temu_category_search_from_name` | `name` | 按类目名搜类目，拿 `node_id`。⚠️ **搜索词大小写敏感（2026-10-10 实测）**：`name="kitchen"` 返回 No data available，`name="Kitchen"`（首字母大写）✅命中 "Kitchen Fixtures"。建议品类词首字母大写，小写无结果时先改大小写再下结论 |
| `temu_category_tree` | — | 类目树，可选 `node_id` 下钻子类目 |
| `temu_category_request` | `node_id` | 类目下产品列表。返回 **`product_id` + `product_name`**（字段名是 product_name），可直接喂给下游 `temu_product_trend` / `temu_product_request` 做趋势与详情深挖 |

### 产品（4）
| 工具 | 必填 | 说明 |
|------|------|------|
| `temu_product_search` | —（全可选） | 多维产品筛选：`node_id`/`brand`/`seller_name`/累计销量/月销/销售额/环比/价格/`manage_type`/评论数/星级/上架时间(`sale_time_min·max`)/`page`，外加 `site` |
| `temu_product_search_from_name` | `name` | 按产品名搜索，可选 `site`/`page` |
| `temu_product_request` | `product_id` | 产品详情 |
| `temu_product_trend` | `product_id` | 历史趋势，`query_start`/`query_end` 定区间 |

### 店铺（1）
`temu_shop_request`(`shop_id`) 店铺详情

## Gotchas

- TEMU 仅 **US + EU 两站**，没有 Amazon 那种 14 站矩阵；跨平台对比时注意站点口径不可比。
- 产品名字段是 `product_name`（非 `title`）；`temu_category_request` 返回的 product_id + product_name 是通往趋势/详情查询的串联键。
- `temu_category_search` 类目级筛选最丰富（20 组维度），做 TEMU 蓝海/竞类分析优先用它而不是产品级搜索。
- 端点仅 10 工具（9 业务 + 通用配额 `common_usage_query`），无关键词工具、无评论工具、无卖家搜索工具——TEMU 侧的关键词/评论洞察需求走 Amazon 端点的类目与 review 方法类比推，或配合 social 端点舆情工具。
- MCP SDK 锁 1.x、响应 `{doc,data}` 包裹、中文叙事前缀等通用坑 → `references/gotchas.md`
- 方法论卡（蓝海发现/竞品深挖/review mining 等 20 张）→ `references/methodology-cards/`
