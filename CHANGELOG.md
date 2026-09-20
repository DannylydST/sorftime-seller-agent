# Changelog
## [2026-09-20] — v3.7.0-channel.1（安全模型显性化）

- **出站域名白名单**：bridge 新增 `ALLOWED_OUTBOUND_HOSTS=("mcp.sorftime.com",)` 与 `_assert_official_url()`——凭证仅发往官方 MCP 端点，任何非白名单主机立即抛错（代码级强制）
- **命令执行全量显性化**：所有 subprocess 调用点显式 `shell=False`+argv 断言；ASIN/站点输入新增正则白名单校验器（`^[A-Z0-9]{10}$` / `^[A-Z]{2}$`）；execv 引导路径注释固化（包内派生，非用户可控）
- **新增 SECURITY.md**：逐点位的命令执行/凭证流向/文件写入安全说明（供审核与自动分析器直接取用）
- **工作流输出目录安全规范**：category/platform 必须 slug 化+realpath 前缀校验（closed-loop-selection.md）
- 依赖安装：仅显式安装步骤（install.py），运行期零 pip install
## [2026-09-18] — v3.6.2-channel（渠道合作版）

面向合作渠道分发的专用版本，功能与官方版一致，另含：
- **渠道注册入口**：默认推荐渠道专属注册链接（经其注册的账号归属合作渠道，功能与价格和官网完全一致，也可官网直连注册——引导时如实告知，由用户自选）
- **注册引导流程优化**：仅在未配置 Key 时引导注册；已有 Key 直接一键配置并验证，不做多余提示
- **安装与兼容性修复**：全新环境下安装器无法完成依赖安装的问题；Python 3.10–3.12 全版本兼容
- **工具集更新至 97 个**：新增 Reddit 社媒舆情三件套、五平台类目树与按名搜索等 12 个工具
- **安全加固**：移除维护类工具与内部模块，发布包仅含用户功能面；文档与配置全面脱敏

## [2026-09-07] — v3.6.2 (tool sync 86→97 + healthcheck auth-detection fix)

### Updated
- **Tool matrix synced to server (97 tools, +12/-1)**: new — `reddit_comment_request` / `reddit_post_request` / `reddit_post_search` (Reddit social listening, passthrough), `ali1688_category_tree`, `shopee_category_tree`, `temu_category_tree`, `tiktok_category_tree`, `tiktok_similar_product_detail`, `walmart_category_tree`, `walmart_category_search_from_name`, `walmart_product_search_from_name`, `product_search_from_name`; removed — `tiktok_category_name_search`.
- SKILL.md / README.md tool-count references updated (86 → 97); platform coverage now notes Reddit.

### Fixed
- **healthcheck.py false-positive "Connect OK"**: server-side auth failures (`isError: true` / "Authentication required" / `NotAuthorization` / `"error": true`) arrive as normal text with returncode 0 — a stale or rotated key reported a green check. These markers now fail the check.

All notable changes to Sorftime Seller Agent.

---

---

> Earlier release history is available in the public repository.
