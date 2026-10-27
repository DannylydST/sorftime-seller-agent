# Overseas Social Media Guide（Reddit · Quora 社媒舆情）

> Endpoint: `https://mcp.sorftime.com/social` · 7 tools（Reddit 三件套 + Quora 三件套 + 通用配额工具）
> 实测有真数据（2026-10-10：`reddit_post_search {"search_name":"yoga mat"}` ✅；social 端点 Quora 三件套由服务端当日下发）

**边界说明**：Reddit 三件套与 Quora 三件套都在本端点；Quora 三件套另在根端点（兼容）提供。**2026-10-27 实测 amazon 端点已不再挂载 Quora 三件套**（此前说法作废）。

## Parameter Traps（调错第一原因，先看这张表）

| 概念 | 实际分布（2026-10-10 活 schema） |
|------|------|
| 搜索词 | `reddit_post_search` 用 `search_name`（支持中英文；可搜品牌名、品类词如 "Ice Maker"、问题描述如 "What to do if the ice maker leaks"）；`quora_question_search` 用 `search_name`（支持中英文） |
| 串联键 | Reddit：`reddit_id`——**必须带 `t3_` 前缀**，从 `reddit_post_search` 结果里取；Quora：`reddit_id`（字段名同 Reddit，值为 Quora 问题 ID，从 `quora_question_search` 结果里取） |
| 帖子类型 | `reddit_post_search` 的 `post_type`，逗号分隔多值：`1`=Question/Help · `2`=Purchase Advice · `3`=Complaint · `4`=Experience Sharing · `5`=Discussion · `6`=Innovation · `7`=Other |
| 情感倾向 | `reddit_post_search` 的 `main_sentiment`（整数）：`1`=Positive · `2`=Neutral · `3`=Negative |
| 分页 | `page`（从 1 起，每页 20 条）——仅 `reddit_post_search`、`reddit_comment_request`、`quora_question_search`、`quora_answer_request` 有 |

## Tool Reference

### Reddit 三件套
| 工具 | 必填 | 说明 |
|------|------|------|
| `reddit_post_search` | `search_name` | 按产品词/品牌词/问题描述搜帖。可选 `post_type`（多值逗号分隔）/`main_sentiment`/`page`。⚠️ Reddit 链路唯一的检索入口，`reddit_id` 只能从这里拿 |
| `reddit_post_request` | `reddit_id` | 取帖子正文与热度数据（返回字段以实测为准——**待实测**） |
| `reddit_comment_request` | `reddit_id` | 取帖子评论（`page` 分页，每页 20 条；返回字段**待实测**） |

### Quora 三件套（本端点 + 根端点）
| 工具 | 必填 | 说明 |
|------|------|------|
| `quora_question_search` | `search_name` | 按关键词/品牌搜 Quora 问题，可选 `post_type`/`main_sentiment`/`page`；拿到问题 ID 供下游两件使用 |
| `quora_question_request` | `reddit_id` | 取问题全文（返回字段以实测为准） |
| `quora_answer_request` | `reddit_id` | 取问题下的回答（`page` 分页；返回字段以实测为准） |

### 通用
`common_usage_query`（全端点通用配额查询，无参数返回 `credit_left`）

## 舆情选品工作流（真实可跑链路）

```
reddit_post_search（按产品词/品牌词搜帖，post_type=3 投诉 / main_sentiment=3 负向 直接锁痛点帖）
  → reddit_post_request（拿正文+热度，确认讨论规模）
  → reddit_comment_request（挖评论区的真实痛点与不满表述）
  → 汇总痛点 → 对照 review-mining 方法论卡做痛点挖掘与机会判定
```

按产品词搜（如 "yoga mat"）看品类讨论热度与槽点；按品牌词搜（如竞对品牌）看品牌舆情与未满足需求。`post_type=3`（Complaint）+ `main_sentiment=3`（Negative）组合是最高信噪比的痛点过滤。Quora 链路同构：`quora_question_search` → 问题全文 → 回答挖掘（问答平台的痛点表述比 Reddit 更长更具体）。方法论细节 → `references/methodology-cards/comprehensive/review-mining.md`。

## Gotchas

- `reddit_id` 必须带 `t3_` 前缀，拿搜索结果里的 ID 原样传递，别截断前缀。
- Reddit 三件套是严格串联：`reddit_post_request` / `reddit_comment_request` 没有搜索能力，没有 `reddit_id` 就只能先跑 `reddit_post_search`；Quora 同构（先 `quora_question_search`）。
- 服务端描述里提及 `social_media_search` 端点名——实际工具名是 `reddit_post_search`，以活 schema 为准。
- MCP SDK 锁 1.x、响应 `{doc,data}` 包裹、中文叙事前缀等通用坑 → `references/gotchas.md`
- 痛点挖掘方法论 → `references/methodology-cards/`（review-mining 为舆情链路主卡）
