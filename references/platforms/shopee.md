# Shopee Platform Guide

> Endpoint: `https://mcp.sorftime.com/shopee` · 18 tools（17 业务 + 通用配额）· 业务工具纯前缀（`shopee_*`），另有跨端点通用配额工具 `common_usage_query`
> Site param: `site` — 8 站点：**`VN ID SG TH MY TW PH BR`**（schema 默认值拼写为 `Unknown`）。⭐2026-10-10 实测：**不传 `site` 报 "Please specify the site"；传非法站点（如 `US`）报 "An error occurred"；传合法站点（如 `PH`）有真数据**——`site` 虽在多数工具标 optional，实际**必传合法枚举值**

## Parameter Traps（调错第一原因，先看这张表）

| 概念 | 实际分布（2026-10-10 活 schema） |
|------|------|
| 站点 | 全部 16 个业务工具共用 `site` 参数（另有通用配额工具 `common_usage_query` 不需站点），枚举统一：`Unknown`/`VN`/`ID`/`SG`/`TH`/`MY`/`TW`/`PH`/`BR`。**无 US/JP 等站** |
| 产品 ID | `product_id`（`shopee_product_request`/`shopee_product_trend`） |
| 店铺 ID | `shop_id`（`shopee_shop_request` 独一份） |
| 类目 ID | `node_id`（`shopee_category_request` 必填；`shopee_category_tree`/`shopee_category_trend` 可选） |
| 搜索词 | `shopee_keyword_search` 用 `keyword`（查**关键词索引**）；`shopee_product_search_from_name`/`shopee_category_search_from_name` 用 `name` |
| 日期 | `shopee_product_trend` 用 `query_start`/`query_end`（`yyyy-MM-dd`）；`shopee_category_request` 用 `query_date` |

## Tool Reference

### 关键词（3）
| 工具 | 必填 | 说明 |
|------|------|------|
| `shopee_keyword_search` | —（全可选，但 `site` 实际必传） | **查关键词索引不是产品搜索**：支持前缀/部分匹配（"phone" 命中 "phone lanyard"，不区分大小写）；多词短语如 "phone case" 若未被索引为关键词可能无数据。无搜索词时传 `rank_min`+`rank_max`（如 1-100）刷热词榜；另有 `search_volume_min/max`、`page` |
| `shopee_keyword_relation_results` | —（`keyword`/`page`/`site` 全 optional，但要查必传 `keyword`+合法 `site`） | ⚠️ **名字带 relation，返回的是产品**（title/product_id/sales_count/price/ratings/shop_name），不是关联词——自由词产品发现用这个 |
| 收藏夹 5 件套 | 见下 | 站点参数 `site` |

收藏夹：`shopee_favorite_keyword`(`keyword`，可选 `dict`) · `shopee_get_favorite_keyword`（可选 `dict`/`page`） · `shopee_get_favorite_keyword_dict`（可选 `page`） · `shopee_change_favorite_keyword`(`keyword`,`to_dict`，可选 `from_dict`) · `shopee_del_favorite_keyword`(`keyword`，可选 `dict`)。**收藏夹工具返回裸数组**（非 `{doc,data}` 包裹）：add 返回 "Favorite succeeded" 的 error 格式 JSON；`get_favorite_keyword_dict` 返回 `["清单名",...]`；`get_favorite_keyword` 返回 `["关键词",...]`

### 产品（5）
| 工具 | 必填 | 说明 |
|------|------|------|
| `shopee_product_search` | —（全可选，`site` 实际必传） | 多维筛选产品搜索：`node_id`、价格区间 `price_range_min/max`、月销区间 `month_sale_volume_range_min/max`、上架日期 `online_date_range_min/max`、评分/评论数/变体数区间、**`shop_location`**（1=本土店 2=跨境店——跨境可行性分析利器，对比两值下的结果量）、`shop_type`、`page`。**响应嵌套：`data.products[]`** 不是 `data[]` |
| `shopee_product_search_from_name` | `name` | 按产品名搜索；`site`/`page` |
| `shopee_product_request` | `product_id` | 产品详情；`site` |
| `shopee_product_content` ⭐新（2026-10-27） | `product_id` | 单品内容素材：全图链接/店铺优惠券/店铺位置；`site` |
| `shopee_product_trend` | `product_id` | 历史趋势；`query_start`/`query_end` 圈定范围（不传默认约 1 年）；`site` |

### 类目（4）
| 工具 | 必填 | 说明 |
|------|------|------|
| `shopee_category_tree` | —（`node_id`/`site` 可选） | 类目树；`site` |
| `shopee_category_search_from_name` | `name` | 按类目名搜索；`site` |
| `shopee_category_request` | `node_id` | 类目下产品；`query_date`/`page`/`site` |
| `shopee_category_trend` | —（`node_id`/`trend_index`/`site` 全 optional） | 类目趋势，`trend_index` 枚举 **72+ 个值**（默认 `MonthlySalesVolume`）：销量/销售额/均价/评分/卖家数/品牌数/旗舰店占比/Preferred 店占比，及 `Listed1Month*`/`Listed3Month*`/`Listed6Month*`/`Listed12Month*`/`Listed24Month*` 时间窗变体与 `Top3*`/`Top5*`/`Top10*` 集中度指标——查全量枚举看 schema |

### 店铺（1）
`shopee_shop_request`(`shop_id`，`site`) 店铺详情

## Gotchas

- **`site` 实测硬约束**：不传报 "Please specify the site"，传非枚举值（如 `US`）报 "An error occurred"——报这两个错先查 `site` 是否合法枚举（⭐2026-10-10 实测）。
- **趋势返回扁平交错数组**：`shopee_category_trend` 与 `shopee_product_trend` 返回 `[date1,val1,date2,val2,...]`，非对象数组。日期是整数：`YYYYMMDD`（日度）或 `YYYYMM`（月度），非 ISO 字符串。解析：`zip(data[::2], data[1::2])`。
- **`shopee_keyword_search` 是关键词索引**：前缀匹配、大小写不敏感；多词短语可能未入索引而无数据；产品自由词发现走 `shopee_keyword_relation_results`（返回产品）。
- **`shop_location` 口径**：1=本土店、2=跨境店，配合 `page` 对比两值结果量做跨境可行性判断。
- **收藏夹裸数组**：add 成功返回 error 格式 JSON（"Favorite succeeded"），查询返回字符串数组——勿按标准 `{doc,data}` 包裹解析。
- **`product_search` 响应嵌套**：取 `data.products[]`，不是顶层 `data[]`。
- **旧口径澄清**：旧文档记站点默认值为 `UnKonw`，**活 schema 拼写为 `Unknown`**；旧文档站点枚举 8 站写法与 schema 一致（`VN ID SG TH MY TW PH BR`）。
- MCP SDK 锁 1.x、响应 `{doc,data}` 包裹、中文叙事前缀等通用坑 → `references/gotchas.md`
- 蓝海发现/市场全景/定价卡等部分方法论卡覆盖 Shopee → `references/methodology-cards/`（跨平台价差卡 `tactical/cross-platform-gap.md` 以 Amazon↔Walmart 为主）
