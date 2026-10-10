# Gotchas — 跨平台通用坑（平台专属坑在各平台页）

## MCP SDK 版本锁（bridge 启动失败第一嫌疑）

本技能锁 **MCP 1.x**（`requirements.txt`: `mcp>=1.0.0,<2.0.0`）。MCP 2.x 有破坏性变更（`Server`→`MCPServer`、`stdio_server` 签名变化）。症状："MCP 2.x is not yet supported" / `AttributeError: 'Server' object...`。修法：`python3 scripts/install.py --upgrade`。

## 响应格式约定

- **包裹**：标准返回 `{"doc": <字段说明>, "data": <数据>}`——`doc` 是字段文档不是数据，解析取 `data`
- **中文叙事前缀**：部分工具在 JSON 前带中文说明文字——`utils/mcp_client.py` 与 bridge 已自动剥离，手写解析时注意
- **扁平交错数组**：趋势族工具（Shopee/Walmart 趋势、变体销量）返回 `[date1, val1, date2, val2, ...]` 而非对象数组。解析：`dict(zip(data[::2], data[1::2]))`；日期元素是 `YYYYMMDD`/`YYYYMM` 整数非 ISO 字符串。客户端已自动处理
- **文本键值对**：`product_trend` 族返回 `"2024年08月=347,2024年09月=155"` 文本——bridge/客户端已自动解析为 dict；若遇到 `{"error": true, "hint": "Server returned non-JSON"}` 说明所用解析路径未含此处理，走 `mcp_client.call_tool_json`
- **收藏夹返回裸数组**：Shopee/Walmart 关键词收藏夹工具不套 `{doc,data}` 包裹，直接返回数组或操作提示文本

## 传输与调用路径

- **主路径**：`mcp_client.call_tool / call_tool_json`（封装 bridge `--one-shot` 直连，处理 env/venv/解析全部复杂度）。编程调用示例：
  ```python
  import sys; sys.path.insert(0, 'scripts')  # 必须先插路径，utils 在 scripts/ 下
  from utils.mcp_client import call_tool, call_tool_json
  ```
  不要 `import MCPClient` / `import mcp_client`（不存在的名字）；不要在技能根目录外跑 `python3 -c "from utils..."`
- **mcporter HTTP 传输**在大响应上偶发中断——复杂查询走 bridge `--one-shot` 直连路径
- 所有 subprocess 调用保持 argv 列表形态（`shell=False`），用户输入（ASIN/站点/关键词）过正则白名单校验后才使用（安全模型见 SECURITY.md）

## 工具清单维护

- 工具 schema 随包发布；服务端上新工具后跑 `python3 scripts/sync_manager.py` 同步（写 schema_store + tool-matrix）
- 未注册进 bridge 的工具经 `sorftime_raw_call` 透传调用：
  ```json
  {"tool_name": "<tool>", "arguments": {...}}
  ```
- 请求超出工具覆盖范围时，mcp_client 自动重映射废弃工具名或拦截落日志（`~/.sorftime-cache/unsupported-requests.log`）
- **Key 轮换中毒**：服务端轮换 Key 后 `tools/list` 返回伪工具（如 NotAuthorization）而非报错——healthcheck 已按此判据检测，遇到即引导用户重新复制 Key

## 端点行为

- **tools/list 按端点过滤，执行器跨端点放行部分通用工具**：`get_time` 不在 walmart/shopee/tiktok/temu/1688/social 端点的 tools/list 里，但直接调用仍会被服务端执行（2026-10-10 实测 1688 端点）。取工具清单以各端点 tools/list 为准，跨端点放行只是服务端容错，不要依赖。
- 平台端点的完整探活（9 端点握手+工具数+配额）跑 `python3 scripts/probe_endpoints.py`。

## 缓存与限额

- SQLite 缓存 `~/.sorftime-cache/`（Windows: `%LOCALAPPDATA%\sorftime-cache`），重复查询自动命中；**缓存是用户级共享**，多实例/多分支共用同一份
- 配额全端点共享；`common_usage_query`（全端点通用）查 `credit_left`；批量场景走脚本（内置节流+缓存），避免裸循环单点调用
