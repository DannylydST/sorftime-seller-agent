# Sorftime MCP 工具能力矩阵

> 自动同步生成。本文件由 `scripts/sync_manager.py` 自动生成，请勿手动编辑。
> 同步时间: 2026-07-26 23:42:40
> 工具总数: 86

## 图例

| 标记 | 含义 |
|------|------|
| ✅ | 核心工具（已在 bridge 中注册 Schema）|
| ⚠️ | 支持工具（可通过 `sorftime_raw_call` 透传调用）|

## 亚马逊产品 (12)

| 工具名 | 状态 | 说明 |
|--------|------|------|
| `competitor_product_keywords` | ✅ 已注册 | Get the exposure positions of a product's competitors under  |
| `product_customers_say` | ⚠️ raw | Query the Amazon "Customers Say" content summarized from the |
| `product_detail` | ✅ 已注册 | Query the detailed data of a product on the Amazon platform. |
| `product_ranking_trend_by_keyword` | ⚠️ raw | Exposure ranking trend of a product under a given keyword on |
| `product_report` | ⚠️ raw | Analysis report for a single product on the Amazon platform. |
| `product_reviews` | ✅ 已注册 | Query user reviews of a product on the Amazon platform in th |
| `product_search` | ✅ 已注册 | Search the real-time product data on the Amazon platform, so |
| `product_search_from_history` | ⚠️ raw | Search historical product data on the Amazon platform to vie |
| `product_traffic_terms` | ✅ 已注册 | Reverse-lookup keywords for a product on the Amazon platform |
| `product_trend` | ✅ 已注册 | Query the historical trend of a product on the Amazon platfo |
| `product_variations` | ✅ 已注册 | Query the variation (child ASIN) details of a product on the |
| `similar_product_feature` | ✅ 已注册 | Query the product features of an Amazon sub-category. |

## 关键词 (11)

| 工具名 | 状态 | 说明 |
|--------|------|------|
| `change_favorite_keyword` | ⚠️ raw | Move a favorited keyword in my Amazon platform keyword libra |
| `del_favorite_keyword` | ⚠️ raw | Delete a specified favorited keyword from my Amazon platform |
| `favorite_keyword` | ⚠️ raw | Add a keyword favorite into my Amazon platform keyword libra |
| `get_favorite_keyword` | ⚠️ raw | Query the keywords in my Amazon platform keyword library. |
| `get_favorite_keyword_dict` | ⚠️ raw | Query the favorite folder list of my Amazon platform keyword |
| `keyword_detail` | ✅ 已注册 | Query the detail of a trending keyword on the Amazon platfor |
| `keyword_extends` | ✅ 已注册 | Query the extended keywords of a trending keyword on the Ama |
| `keyword_list` | ⚠️ raw | Query the real-time trending keyword list on the Amazon plat |
| `keyword_list_from_history` | ⚠️ raw | Query the historical-date trending keyword list on the Amazo |
| `keyword_search_results` | ✅ 已注册 | Query the organic-position product list of a trending keywor |
| `keyword_trend` | ✅ 已注册 | Query the historical trend of a trending keyword on the Amaz |

## 类目 (9)

| 工具名 | 状态 | 说明 |
|--------|------|------|
| `category_keywords` | ⚠️ raw | Query the core keywords of an Amazon sub-category market. |
| `category_name_search` | ✅ 已注册 | Query Amazon sub-category markets by name, returning the Nod |
| `category_report` | ✅ 已注册 | Query the real-time top-100-by-sales product data report for |
| `category_report_from_history` | ⚠️ raw | Query the historical-period top-100-by-sales product data re |
| `category_search_from_product_name` | ⚠️ raw | Search Amazon sub-category markets related to a given produc |
| `category_search_from_top_node` | ✅ 已注册 | Search Amazon sub-category markets under a given top-level c |
| `category_tree` | ⚠️ raw | Query the product category structure on the Amazon platform. |
| `category_trend` | ✅ 已注册 | Query Amazon sub-category market trend data, based on the su |
| `search_categories_broadly` | ⚠️ raw | Broadly search sub-category markets that match multi-dimensi |

## TikTok Shop (9)

| 工具名 | 状态 | 说明 |
|--------|------|------|
| `tiktok_author` | ⚠️ raw | Query TikTok platform author details by author ID, US site o |
| `tiktok_category_name_search` | ⚠️ raw | Search related TikTok categories by name, returns category n |
| `tiktok_category_report` | ✅ 已注册 | Query the category data report for a given category on the T |
| `tiktok_category_search_from_name` | ⚠️ raw | Search related categories on the TikTok platform by name. |
| `tiktok_product_detail` | ✅ 已注册 | Query product details on the TikTok platform. |
| `tiktok_product_trend` | ⚠️ raw | Query TikTok platform product trend, returning multiple dime |
| `tiktok_product_video` | ⚠️ raw | Query promo videos of a TikTok product. |
| `tiktok_product_video_author` | ⚠️ raw | Query promo authors of a product on the TikTok platform. |
| `tiktok_similar_product` | ⚠️ raw | Query similar products of a product on the TikTok platform;  |

## 其他 (45)

| 工具名 | 状态 | 说明 |
|--------|------|------|
| `ali1688_product_request` | ⚠️ raw | Query the product details on the 1688 platform. |
| `ali1688_product_search` | ⚠️ raw | Search product information on the 1688 platform across multi |
| `ali1688_product_search_from_image` | ⚠️ raw | Search products on the 1688 platform by image. |
| `ali1688_product_variations` | ⚠️ raw | Find the variation (SKU) data of a product on the 1688 platf |
| `ali1688_similar_product` | ✅ 已注册 | Find sourcing/wholesale suppliers for a product on the 1688  |
| `get_time` | ✅ 已注册 | Get the current server time. |
| `potential_product` | ✅ 已注册 | (隐赚指数选品) Search for potential products on the Amazon platfor |
| `shopee_category_request` | ⚠️ raw | Query Best Seller products under a Shopee category. Optional |
| `shopee_category_search_from_name` | ⚠️ raw | Search related category markets on Shopee by name. Used to o |
| `shopee_category_trend` | ⚠️ raw | Used to query the historical trend of a Shopee category mark |
| `shopee_change_favorite_keyword` | ⚠️ raw | Move a favorited keyword on the Shopee platform to a specifi |
| `shopee_del_favorite_keyword` | ⚠️ raw | Delete a specified keyword from my Shopee keyword favorites. |
| `shopee_favorite_keyword` | ⚠️ raw | Add a keyword to my Shopee keyword favorites. If the specifi |
| `shopee_get_favorite_keyword` | ⚠️ raw | Query the favorited keywords in my Shopee keyword favorites. |
| `shopee_get_favorite_keyword_dict` | ⚠️ raw | Query the list of dicts (folders) in my Shopee keyword favor |
| `shopee_keyword_relation_results` | ⚠️ raw | Search Shopee related products by keyword, returning up to 2 |
| `shopee_keyword_search` | ⚠️ raw | The list of trending keywords on Shopee, sorted by monthly s |
| `shopee_product_request` | ⚠️ raw | Query detailed information of a Shopee product. |
| `shopee_product_search` | ⚠️ raw | Search product data on the Shopee platform with multi-dimens |
| `shopee_product_search_from_name` | ⚠️ raw | Search related products on Shopee by name, returning up to 2 |
| `shopee_product_trend` | ⚠️ raw | Supports historical trends across five dimensions: star rati |
| `shopee_shop_request` | ⚠️ raw | Query Shopee seller (shop) details. Returns basic informatio |
| `temu_category_request` | ⚠️ raw | Query Best Seller products under a Temu category market, whi |
| `temu_category_search` | ⚠️ raw | Search category data on the Temu e-commerce platform with mu |
| `temu_category_search_from_name` | ⚠️ raw | Search Temu platform category markets by name. |
| `temu_product_request` | ⚠️ raw | Query Temu product details. |
| `temu_product_search` | ⚠️ raw | Search product data on the Temu e-commerce platform with mul |
| `temu_product_search_from_name` | ⚠️ raw | Search Temu products by name, returning 20 products per call |
| `temu_product_trend` | ⚠️ raw | Query product historical trend data, returning monthly trend |
| `temu_shop_request` | ⚠️ raw | Query Temu seller (shop) details. |
| `walmart_category_report_by_node_id` | ⚠️ raw | Query the real-time Top 100 best-selling product data report |
| `walmart_change_favorite_keyword` | ⚠️ raw | Move a favorited keyword in my Walmart platform keyword libr |
| `walmart_del_favorite_keyword` | ⚠️ raw | Delete a specific favorited keyword from my Walmart platform |
| `walmart_favorite_keyword` | ⚠️ raw | Add a keyword favorite in my Walmart platform keyword librar |
| `walmart_get_favorite_keyword` | ⚠️ raw | Query the keywords in my Walmart platform keyword library. |
| `walmart_get_favorite_keyword_dict` | ⚠️ raw | Query the collection list of my Walmart platform keyword lib |
| `walmart_keyword_detail` | ⚠️ raw | Query the details of a hot-search keyword on the Walmart e-c |
| `walmart_keyword_extends` | ⚠️ raw | Query the extension keywords of a hot-search keyword on the  |
| `walmart_keyword_list` | ⚠️ raw | Query the real-time hot-search keyword list on the Walmart e |
| `walmart_keyword_search_from_name` | ⚠️ raw | Query a hot-search keyword on the Walmart e-commerce platfor |
| `walmart_keyword_search_results` | ⚠️ raw | Query the natural-position product list in the last 15 days' |
| `walmart_product_detail_by_product_id` | ⚠️ raw | Query the details of a product on the Walmart e-commerce pla |
| `walmart_product_traffic_terms` | ⚠️ raw | Reverse-lookup keywords for a product on the Walmart e-comme |
| `walmart_product_trend_by_product_id` | ⚠️ raw | Query the historical trend data of a product on the Walmart  |
| `walmart_product_variation_sales_by_product_id` | ⚠️ raw | Query the variation (child item) sales breakdown of a produc |

## 通用调用方式

当需要调用 ⚠️ raw 工具时，使用 `sorftime_raw_call`：

```json
{
  "tool_name": "product_trend",
  "arguments": {
    "amz_site": "US",
    "asin": "B0DPQ772T9"
  }
}
```
