# TikTok Platform Guide

> Endpoint: `https://mcp.sorftime.com/tiktok` · 19 tools
> Site param: `site` — 9 sites: `Unknow US MY PH VN TH ID GB JP`（⚠️ **author 系 2 个工具只有 `Unknow US MY`**）；schema 里 `Unknow` 即原样拼写
> 2026-10-10 实测：`tiktok_category_search_from_name {"name":"kitchen","site":"US"}` 有真数据

## Parameter Traps（调错第一原因，先看这张表）

| 概念 | 实际分布（2026-10-10 活 schema） |
|------|------|
| 站点 | 全部 18 个工具都有 `site`，**全部可选但行为不一致——始终显式传 `site`**；9 站点族（US/MY/PH/VN/TH/ID/GB/JP）vs author 系 3 站点族（Unknow/US/MY），枚举拼写以 schema 为准 |
| 产品 ID | `product_id`（`tiktok_product_request` / `tiktok_product_trend`） |
| 类目 ID | `node_id`（⚠️ 不是 `category_id`）；`tiktok_category_tree` 的 `node_id` 可选——不传返回顶层，传了返回该节点的子类目 |
| 搜索词 | 所有 `*_search_from_name` 工具用 `name`；`name` 的含义随 `query_type` 变化（见下） |
| `query_type` | 各工具枚举不同：`product_search_from_name` 1=产品名/2=标题关键词/3=包含词；`shop_search_from_name` 1=卖家名/2=产品名/3=品牌；`author_search_from_name` 1=达人名/2=产品/3=品牌/4=卖家；`brand_search_from_name` 1=按产品/2=按名/3=按卖家；`video_search_from_name` 1=标题模糊/2=产品/3=卖家/4=品牌——**以目标工具 schema 为准，勿跨工具套用** |
| 数字枚举 | `tiktok_product_search.ship_location`：1=本土发货，2=海外发货；`shop_type`：1=Gold-star seller，2=Silver-star seller，3=官方店（截断，以 schema 描述为准）；`tiktok_product_trend.type`：1=周销趋势（10 credits），2=月销趋势（默认，5 credits） |
| 达人 ID | `tiktok_author_request.author_id` **实际接受作者 handle（如 `xmw_us`），非数字 ID**；可从 `tiktok_author_search_from_name` 结果获取 |

## Tool Reference

### 产品（4）
| 工具 | 必填 | 说明 |
|------|------|------|
| `tiktok_product_request` | `product_id` | 产品详情。返回结构以实测为准 |
| `tiktok_product_search` | —（全可选） | ⭐多维产品筛选，30+ 参数：`node_id`/`brand`/`seller_name`/`seller_id`/`price_min·max`/`month_sale_count_min·max`/`weekly_sale_count_min·max`/`exposure_time_min·max`（上架时间，字符串日期）/`star_min·max`/`review_count_min·max`/`variation_count_min·max`/`ship_location`/`shop_type`/`author_count_count_min·max`（关联达人数，参数名就是双 `_count`）/`video_count_count_min·max`（推广视频数）/`page`（每页 20 条）。选品主力工具 |
| `tiktok_product_search_from_name` | —（`name` 语义随 `query_type` 变） | 按名搜产品，`page` 每页 20 条 |
| `tiktok_product_trend` | `product_id` | 历史趋势，`type` 1=周（10 credits）/2=月（默认，5 credits） |

### 店铺（3）
| 工具 | 必填 | 说明 |
|------|------|------|
| `tiktok_shop_request` | `shop_id` | 店铺详情（店铺 ID 形如 `8646932002846773930`） |
| `tiktok_shop_search` | —（全可选） | 店铺多维筛选 20+ 参数：`node_id` 圈类目（不限制结果范围）/`seller_product_count`/`seller_cumulative_sale_count`/`seller_review_count`/`product_count`/`weekly_sale_count·amount_min·max`/`monthly_sale_count·amount_min·max`/`star_min·max`/`shop_type`/`fans_count_min·max`/`page`（每页 20 卖家）。竞店分析、店群发现 |
| `tiktok_shop_search_from_name` | —（`name` 语义随 `query_type` 变） | 按名搜店铺，`page` 每页 100 卖家 |

### 达人（2）⚠️ site 仅 `Unknow US MY`
| 工具 | 必填 | 说明 |
|------|------|------|
| `tiktok_author_request` | `author_id` | 达人详情；`author_id` 实测接受 handle（如 `xmw_us`），非数字 ID |
| `tiktok_author_search_from_name` | —（`name` 语义随 `query_type` 变） | 按名搜达人，`query_type` 4=按卖家；`page` 每页 100 达人。联盟带货达人发现入口 |

### 品牌（1）
`tiktok_brand_search_from_name`（—，`query_type` 1=按产品/2=按名/3=按卖家，`page` 每页 100 品牌）— 品牌按名发现，无品牌详情工具

### 视频（3）
| 工具 | 必填 | 说明 |
|------|------|------|
| `tiktok_video_request` | `video_id` | 单个视频详情（视频 ID 形如 `7661686423367453965`） |
| `tiktok_video_search_from_name` | —（`name` 语义随 `query_type` 变） | 按名搜视频，`query_type` 1=标题模糊匹配；`page` 每页 100 条。爆款带货视频挖掘 |
| `tiktok_video_tag_search` | `tag_name` | 话题标签搜索（如 `fashion`），`page` 每页 20 个标签。话题趋势入口 |

### 类目（5）
| 工具 | 必填 | 说明 |
|------|------|------|
| `tiktok_category_request` | `node_id` | 类目详情/榜单（`page` 每页 20 个产品）。**返回结构待实测**——旧 category_report 榜单不含 `product_id`，新结构是否含 `product_id` 拿到结果再确认；若不含，用 `tiktok_product_search_from_name` 反查 product_id |
| `tiktok_category_search` | —（全可选） | 类目多维筛选 30+ 参数：集中度（`top10_product_monthly_sale_count_share_ratio`/`top10_seller_*`）、体量（`monthly_sale_count·amount`/`cumulative_sale_count`）、质量（`avg_star`/`avg_review_count`/`avg_price`）、新品动态（`new_product_count`/`new_product_monthly_sale_*`/`new_product_*_share_ratio`）、`source_shop_count`（Top-300 在售店铺数）。类目竞争格局分析主力 |
| `tiktok_category_search_from_name` | `name` | 按名搜类目（如 `{"name":"kitchen","site":"US"}` 实测有真数据） |
| `tiktok_category_tree` | —（`node_id` 可选） | 类目树：不传返回顶层，传 `node_id` 返回其子类目。层级遍历唯一入口 |
| `tiktok_category_trend` | `node_id` | 类目历史趋势，`trend_index`：0=月销件数，1=月销件数环比，2=月销额（截断，以 schema 枚举为准） |

### 从旧资料迁移：旧名 → 新名对照

旧 7 工具已全部下线。仅**同参等价**的改名进客户端自动映射（`mcp_client` 调旧名自动改发新名）；行为不等价的旧工具不自动映射——干净报错好过错参失败：

| 旧名（已下线） | 现名 | 自动映射 |
|---------------|------|:---:|
| `tiktok_product_detail` | `tiktok_product_request` | ✅ |
| `tiktok_category_report` | `tiktok_category_request` | ✅ |
| `tiktok_author` | `tiktok_author_request` | ✅ |
| `tiktok_category_name_search` | `tiktok_category_search_from_name` | ✅ |
| `tiktok_similar_product` | 无直接对应——用 `tiktok_product_search` 多维筛选替代 | ❌ |
| `tiktok_similar_product_detail` | 无直接对应 | ❌ |
| `tiktok_product_video` / `tiktok_product_video_author` | 语义已变（新 `tiktok_video_request` 按 video_id 查视频详情，非「产品的视频」） | ❌ |

## Gotchas

- **类目发现 SOP（永远 tier-1 先行）**：① TIER 1（0 秒、0 API 调用）：读包内 `references/tiktok-rankings.json`——228 个叶子类目预计算榜单（月销/环比/均价 + 启发式父类目聚合），覆盖绝大多数活跃类目，「热销类目」「市场概览」问题直接答；② 榜单没有的：`_search_from_name` 按名搜 → `category_tree` 定层级 → `category_request`/`category_search` 出数据。反模式：勿逐字母暴力遍历、勿不带 `site` 调工具、勿指望顶层类目名精确匹配。
- **类目名搜索只发现叶子级类目**；要枚举顶层或上下钻取，用 `tiktok_category_tree`。
- **站点可用性不均**：8 个业务站点里 VN 类目查询常返回 "No data available"；GB/JP/ID/MY/PH/TH/US 确认有数据。空结果先换站点复核，再判为真无数据。
- **达人系站点面窄**：`tiktok_author_request`/`tiktok_author_search_from_name` 的 `site` 只有 `Unknow/US/MY`，其余站点传了也白传。
- `tiktok_category_request` 与 `tiktok_product_request` 的返回结构**未逐字段实测**，本文不写死字段名；拿到响应以实际字段为准。
- MCP SDK 锁 1.x、响应 `{doc,data}` 包裹、中文叙事前缀等通用坑 → `references/gotchas.md`
- 大盘方法论卡 → `references/methodology-cards/`
