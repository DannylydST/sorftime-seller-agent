# Amazon Platform Guide

> Endpoint: `https://mcp.sorftime.com/amazon` · 43 tools（40 原生 + 3 专利，2026-10-27 实测）· Quora 三件套已迁 social 端点（根端点仍含）
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
| `product_trend` | `asin`,`type` | 历史趋势。`type`：`SalesVolume`（月销量，默认）/`SalesAmount`（月销额）/`Price`/`ListPrice`/`Rank`（主类目月排名）/`BsrRank`（子类目日排名）/`ReviewCount`/`Star`/**`DailySalesVolume`（日销量，2026-10-27 新增）**/`AsinSalesVolume`（ASIN 级月销，不含子体）。返回 `2024年08月=347` 文本格式——bridge/客户端已自动解析为 dict |
| `product_report` | `asin` | 单品分析报告 |
| `product_ranking_trend_by_keyword` | `asin`,`keyword` | 关键词下曝光排名趋势 |
| `product_search_from_name` | `name` | 按名搜索 |
| `product_search_from_history` | —（`search_time` 定位历史时点） | 历史快照搜索 |
| `similar_product_feature` | `product_name` | 子类目产品特征（注意参数是产品名非 ASIN） |
| `competitor_product_keywords` | `asin` | 竞品关键词曝光位 |
| `product_customers_say` | `asin` | "Customers Say" 买家声音摘要（站点参数 `site`） |

### 关键词（11）
`keyword_detail`(`keyword`,`amz_site`) 单词详情 · `keyword_extends`(`keyword`) 拓展词 · `keyword_search_results`(`keyword`,`position_type`：0=全部 1=自然位(默认) 2=仅广告) 关键词下产品 · `keyword_trend`(`keyword`,`type`) · `keyword_list` / `keyword_list_from_history`(`date`) 热词榜（`rank_min/max`、`search_volume_min/max` 过滤） · 收藏夹 5 件套（`favorite_keyword` / `get_favorite_keyword` / `get_favorite_keyword_dict` / `change_favorite_keyword` / `del_favorite_keyword`，站点参数 `keyword_support_site`）

### 类目（9）
`category_report`(`node_id`) 类目 Top100 销量报告 · `category_trend`(`node_id`,`trend_index`) · `category_name_search`(`category_name`) · `category_search_from_top_node`(`top_node`) · `category_search_from_product_name`(`product_name`) · `search_categories_broadly` 多维宽搜 · `category_tree` · `category_products`(`node_id`) ⭐新 类目下产品 · `category_keywords`(`node_id`)（实测常无数据）

### 低价商城 ⭐新（2026-10-10 实测有真数据）
`category_low_price_search` — 低价商城类目搜索，全参数可选。返回每个类目的低价带产品数/低价带月销/全类目月销/均价/评分/评论数/新品占比/自营占比/第三方占比/平均重量(0.01lb)/体积(0.01in³)/上架天数等。**低价商城(Haul)选品与竞店分析的核心工具**，配合 `average_weight/volume` 过滤可精确锁定轻小件。

### 卖家搜索 ⭐新（工具已上线，数据铺量中——2026-10-10 三种合法参数实测均返回 "No data available"，如实告知用户）
`seller_search` — 40+ 筛选维度（中国卖家/产品数/品牌数/Top10 占坑数/月销/FBM 数/A+ 数/无品牌占比/均价/评论/变体/在线日期/feedback），`node_id` 圈定类目。`seller_search_from_name`(`query_type` 1=按卖家名 2=按品牌)。

### 专利（3）⭐新（2026-10-27 上线；外观侵权排查/竞品专利组合分析）
| 工具 | 必填 | 说明 |
|------|------|------|
| `patent_search_from_keyword` | `keyword` | 关键词/公司名/人名/公告号/申请号查专利（60 积分，单页最多 30 条）。筛选：`patent_type`（1 发明申请/2 发明授权/3 实用新型/4 外观设计，数组）、`legal_status`（1 失效/2 有效/3 审查中/4 PCT 失效/5 PCT 审查中/6 状态不明，数组）、`country`（WO/EP/CN/EM/JP/KR/US…数组）、`applicant`、`publication_no`、`application_no`、`class_type`（1 LOC/2 IPC）+`class_no`、`page_index`。返回：Photo/Title/PublicationNo/Applicant/ApplicationDate/PublicationDate |
| `patent_search_from_image` | `image` | 图搜外观专利（450 积分，最多 100 条）。`image` 支持 URL/Base64（产品占比>80%、干净背景、jpg/png<4M）；**`query_mode` 实际必传**（1=智能联想推荐 / 2=以图搜图；不传返回 `null`，2026-10-27 实测）；可选 `country`/`loc_class_no`（如 `["07-01"]`）/`legal_status`/`product_keyword`/`applicant` |
| `patent_request` | `publication_no` | 专利详情（150 积分；同一公告号同账号**首次查询计费、后续免费**）。返回：Title/PublicationNo/PatentType(4=外观)/Country/Inventor/Applicant/LOC·IPC·CPC·GBC 分类/LegalStatus/ApplicationDate/PublicationDate/EstimatedExpiryDate/Photos[] |

> 专利图链域名=zhihuiya.com（智慧芽，实测）；`publication_no` 从两个搜索工具的结果里取（如 `CN308683395S`）。「首次查询计费、后续免费」出自 MCP 工具描述原文。Quora 三件套不在本端点（见 social）。

### 隐赚指数（Sorftime 独家方法论）
`potential_product` — 全参数可选：**不传 `search_name` = 全品类跨排名**，传 = 关键词域内。返回 `potential_index` 综合评分（相对值：低门槛×低广告×高利润加权）。⚠️ 高分不豁免类目风险——食品/保健/电子合规/季节品/授权品牌必须对照四层风险咨询制亮牌（永不隐藏，见 `references/scripts-guide.md`）。完整方法论 → `references/methodology-cards/tactical/invisible-profit.md`

### 通用
`get_time`（服务器时间）· `common_usage_query`（**配额查询**，全端点通用，无参数，返回 `credit_left`——用户问余额/剩余次数就调它）

## Gotchas

- **图搜专利不传 `query_mode` 返回 `Data: null`（不是无结果）**——2026-10-27 实测，必须显式传 1 或 2。
- `category_report_from_history` 已从端点下线（工具清单中不存在）；`category_keywords` 实测常 "No relevant data"——服务端覆盖问题，非调用错误。历史类目数据走 `category_report` 的 `query_date` 参数。
- MCP SDK 锁 1.x、响应 `{doc,data}` 包裹、中文叙事前缀等通用坑 → `references/gotchas.md`
- 大盘方法论（市场全景/竞品深挖/关键词布局等 20 张卡）多数以 Amazon 为主场 → `references/methodology-cards/`
