# Mercado Libre Platform Guide

> Endpoint: `https://mcp.sorftime.com/mercado` · 2 tools（1 业务 + 通用配额，2026-11-19 实测）

## 当前状态

- 端点已上线并可连通；通用配额工具 `common_usage_query` 可直接调（返回 credit_left）。
- **首个业务工具 `mercado_product_search_from_keyword` 已在工具清单出现**（2026-11-19 活 schema 验证）；当前账号数据包未开——实测返回 "No data available"，如实告知用户「工具已上线、数据待账号数据包开通」，不要虚构返回内容。
- 业务工具调用前先探活：工具清单未出现的业务方法不要调（方法不存在错误，且可能被服务端记录为异常请求）。

## Tool Reference

### 商品（1）
`mercado_product_search_from_keyword`(`keyword` 必填,`page`,`site`) — Mercado Libre 关键词搜品，实时查询，20 条/页；**仅巴西站（site=401）**，不传 `site` 报「Please specify the site」（2026-11-19 实测）。

## 工具开通后怎么复查

```bash
# 复查全部端点的工具清单（含 mercado）
python scripts/probe_endpoints.py --json
```

`count` 从 0 变为正数即表示工具已开通。届时按以下清单补齐本文档：

1. 对照活 schema 逐一核对工具名、必填参数、枚举值（写入 `## Tool Reference` 工具表）
2. 整理 `## Parameter Traps`（站点参数名、ID 参数名、枚举拼写）
3. 实测 1-2 个核心工具确认有真数据，标注实测日期
4. 补充 `## Gotchas`（站点覆盖、空数据站点等）

## 通用参考

- MCP SDK 锁 1.x、响应 `{doc,data}` 包裹、中文叙事前缀等通用坑 → `references/gotchas.md`
- 数据探查/诊断脚本用法 → `references/scripts-guide.md`
