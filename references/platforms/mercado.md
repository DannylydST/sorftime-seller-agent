# Mercado Libre Platform Guide

> Endpoint: `https://mcp.sorftime.com/mercado` · **1 tool（common_usage_query）**（2026-10-10 实测：当前账号下该端点未暴露任何工具）

## 当前状态

- 端点已上线并可连通，但工具按账号数据包逐步开通——当前账号未见任何工具，不代表端点不存在。
- **不要对 mercado 端点发起任何工具调用**：会返回方法不存在类错误，且可能被服务端记录为异常请求。
- 用户问到 Mercado Libre 数据能力时，如实告知「端点已就绪、工具尚未对当前账号开通」，不要虚构工具或参数。

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
