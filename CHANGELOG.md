# Changelog
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
