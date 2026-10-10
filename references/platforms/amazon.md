# Amazon Platform Guide

> Endpoint: `https://mcp.sorftime.com/amazon` · 43 tools · Quora 市场情报三件套也挂在本端点
> Site param: `amz_site` — 14 sites: `US GB DE FR IN CA JP ES IT MX AE AU BR SA`（无 SG）

## Parameter Traps（调错第一原因，先看这张表）

同一业务概念在不同工具里参数名不同，**以目标工具的 inputSchema 为准**（`mcp_client` 已自动纠正常见别名）：

| 概念 | 实际分布（2026-10-10 活 schema） |
|------|------|
| 搜索词 | `product_search` 用 **`keyword`**（旧名 `search_name` 已废弃，自动纠正）；`product_search_from_name` 用 `name`；类目搜索用 `category_name` / `product_name` |
| 站点 | 大多数产品/类目工具用 `amz_site`；`keyword_extends`/`keyword_search_results`/`keyword_list`/`keyword_trend`/收藏夹 5 件套用 `keyword_support_site`；**`keyword_detail` 已统一为 `amz_site`**；**`product_customers_say` 全 Amazon 独一份用 `site`** |
| 类目 ID | `node_id`（`category_search_from_top_node` 用 `top_node`） |
| 产品 ID | `asin`；`similar_product_feature` 例外用 `product_name` |
| 日期 | `yyyy-MM-dd`；`category_report` 历史区间上限 40 天 |

## Tool Reference

### 产品（14）
| 工具 | 必填 | 说明 |
|------|------|------|
| `product_search` | —（全可选） | 实时产品搜索：`keyword`/`price_range_min·max`/`asin`/`node_id`/`brand`/`page` |
| `product_detail` | `asin` | 产品详情（价格/销量/评分/品牌/变体概览） |
| `product_content` ⭐新 | `asin` | Listing 内容拆解：主图组/五点描述/属性表/**买家关注度评分**(`feature`)/A+ 图片——内容分析与 listing 审计的核心，实测有真数据 |
| `product_reviews` | `asin` | 评论（`review_type`: Both/Positive/Negative）。**上限约 100 条、无分页参数**；低量 ASIN 可能返回无评论 |
| `product_variations` | `asin` | 子体 ASIN 列表；部分子体 `attribute`/销量区间可能为空，用前核对 |
| `product_traffic_terms` | `asin` | 流量词反查（搜索量/建议竞价/曝光位）。⚠️ 字段用 `exposure_position`("Organic"/"Ad"/"Ad,Organic")+`latest_organic_position`，**没有** `organic_searched_percentage` 字段，查它恒得 null |
| `product_trend` | `asin`,`type` | 历史趋势。返回 `2024年08月=347` 文本格式——bridge/客户端已自动解析为 dict |
| `product_report` | `asin` | 单品分析报告 |
| `product_ranking_trend_by_keyword` | `asin`,`keyword` | 关键词下曝光排名趋势 |
| `product_search_from_name` | `name` | 按名搜索 |
| `product_search_from_history` | —（`search_time` 定位历史时点） | 历史快照搜索 |
| `similar_product_feature` | `product_name` | 子类目产品特征（注意参数是产品名非 ASIN） |
| `competitor_product_keywords` | `asin` | 竞品关键词曝光位 |
| `product_customers_say` | `asin` | "Customers Say" 买家声音摘要（站点参数 `site`） |

### 关键词（11）
`keyword_detail`(`keyword`,`amz_site`) 单词详情 · `keyword_extends`(`keyword`) 拓展词 · `keyword_search_results`(`keyword`) 关键词下自然位产品 · `keyword_trend`(`keyword`,`type`) · `keyword_list` / `keyword_list_from_history`(`date`) 热词榜（`rank_min/max`、`search_volume_min/max` 过滤） · 收藏夹 5 件套（`favorite_keyword` / `get_favorite_keyword` / `get_favorite_keyword_dict` / `change_favorite_keyword` / `del_favorite_keyword`，站点参数 `keyword_support_site`）

### 类目（9）
`category_report`(`node_id`) 类目 Top100 销量报告 · `category_trend`(`node_id`,`trend_index`) · `category_name_search`(`category_name`) · `category_search_from_top_node`(`top_node`) · `category_search_from_product_name`(`product_name`) · `search_categories_broadly` 多维宽搜 · `category_tree` · `category_products`(`node_id`) ⭐新 类目下产品 · `category_keywords`(`node_id`)（实测常无数据）

### 低价商城 ⭐新（2026-10-10 实测有真数据）
`category_low_price_search` — 低价商城类目搜索，全参数可选。返回每个类目的低价带产品数/低价带月销/全类目月销/均价/评分/评论数/新品占比/自营占比/第三方占比/平均重量(0.01lb)/体积(0.01in³)/上架天数等。**低价商城(Haul)选品与竞店分析的核心工具**，配合 `average_weight/volume` 过滤可精确锁定轻小件。

### 卖家搜索 ⭐新（工具已上线，数据铺量中——2026-10-10 三种合法参数实测均返回 "No data available"，如实告知用户）
`seller_search` — 40+ 筛选维度（中国卖家/产品数/品牌数/Top10 占坑数/月销/FBM 数/A+ 数/无品牌占比/均价/评论/变体/在线日期/feedback），`node_id` 圈定类目。`seller_search_from_name`(`query_type` 1=按卖家名 2=按品牌)。

### Quora 市场情报 ⭐新（工具已上线，数据铺量中——实测 "No data available"，同上口径）
`quora_question_search`(`search_name`，支持中英文) → `quora_question_request`(`reddit_id`) 问题全文 → `quora_answer_request`(`reddit_id`,`page`) 回答。挂在 amazon 端点（市场情报归类）。

### 隐赚指数（Sorftime 独家方法论）
`potential_product` — 全参数可选：**不传 `search_name` = 全品类跨排名**，传 = 关键词域内。返回 `potential_index` 综合评分（相对值：低门槛×低广告×高利润加权）。⚠️ 高分不豁免类目风险——食品/保健/电子合规/季节品/授权品牌必须对照四层风险咨询制亮牌（永不隐藏，见 `references/scripts-guide.md`）。完整方法论 → `references/methodology-cards/tactical/invisible-profit.md`

### 通用
`get_time`（服务器时间）· `common_usage_query`（**配额查询**，全端点通用，无参数，返回 `credit_left`——用户问余额/剩余次数就调它）

## Gotchas

- `category_report_from_history` 已从端点下线（工具清单中不存在）；`category_keywords` 实测常 "No relevant data"——服务端覆盖问题，非调用错误。历史类目数据走 `category_report` 的 `query_date` 参数。
- MCP SDK 锁 1.x、响应 `{doc,data}` 包裹、中文叙事前缀等通用坑 → `references/gotchas.md`
- 大盘方法论（市场全景/竞品深挖/关键词布局等 20 张卡）多数以 Amazon 为主场 → `references/methodology-cards/`
