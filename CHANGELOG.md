# Changelog
## [2026-10-12] — v5.1.0（官方直营定位：去渠道化 + 国内外双站注册）

- **官方直营定位确立**：移除渠道合作版全套引导（渠道注册链接 tag、归属说明话术、透明铁律、config/channel.json）——注册话术只服务用户动作（注册→取 Key→发回），两站区别只答「功能价格一致，选你方便的」
- **双站注册**：大陆站 open.sorftime.com（手机号/微信、人民币）与国际站 open-intl.sorftime.com（邮箱/Google、PayPal/Stripe）并列为官方入口——SKILL.md/onboarding.md（双版三步话术模板）/README.md/平台包 README 模板四处同步
- 方式 A（官网一键配置）补两站 MCP 页标注（open/open-intl 各有 /mcp，指令形态一致）
- 话术纪律更新：不加机制解释；已有 Key 时零注册话术
## [2026-10-10] — v5.0.3（包内文档与脚本过滤对齐）

- 平台包 SKILL.md Scripts 表按平台过滤（包内不含的引擎不再列出，杜绝死命令）；tiktok 包补 discover_tiktok 入口行
- 平台包 scripts-guide 顶部加包级注（跨平台引擎示例属总技能，本包执行会报文件不存在）
- 构建器 docstring 与过滤行为对齐
## [2026-10-10] — v5.0.2（平台包脚本净化 + 措辞收尾）

- 平台包不再随带其他平台的专属脚本（picker/analyst→Amazon、walmart_*→Walmart、discover_tiktok→TikTok），消除跨平台脚本误导；总技能（全平台包）保留全部脚本
- SKILL.md Onboarding/Environment 两处安装命令补 Windows `python` 提示
## [2026-10-10] — v5.0.1（通道 A 范围修正）

- 通道 A（原生 MCP）知识层范围澄清：数据查询走宿主原生 MCP 工具；批量脚本（picker/monitor 等）内部经技能 bridge 取数、仍需本地 Key（届时跑一次 install.py 即可）——SKILL.md/onboarding/平台包 README 三处同步
- onboarding 连通性验证示例改用全端点通用的 `common_usage_query`；平台包工具清单「其他平台」改为动态生成（含 mercado、不含本包）；生成节间空行修正；README 官方下载位表述如实（换链进行中）
## [2026-10-10] — v5.0.0（双通道接入 + 官网一键配置对齐 + 安装体验重做）

- **双通道数据接入（自动分流）**：通道 A=宿主原生 MCP 服务（官网 MCP 页「一键配置」配置的 `sorftime-<平台>` 系 streamableHttp 服务，服务名与平台包同名）——已配置时本技能自动作为知识层（平台文档/参数 traps/选品方法论/批量脚本），不再要求重复配 Key；通道 B=技能内置 bridge（默认，install.py 一键配置）。官方指令原文（单选/多选两种形态）入 `references/onboarding.md`
- **总技能定位确立**：本技能=全平台总技能+官方分发单元；8 个平台包为同源平台专版，同名对齐官网原生服务名，共存迭代
- **安装体验重做**：每个平台包新增用户 README（技能目录放置对照表+Windows `python` 提示+三步开始+官网一键配置入口）；仓库 README 新增 Install 段
- **平台包工具清单改为端点专属视图**：不再携带全端点矩阵（曾导致跨平台工具误调用），顶部声明本包可用范围与跨包获取方式
- **脚本平台适用性标注**：引擎脚本覆盖 Amazon/Walmart，其余平台 MCP 直调（SKILL.md Scripts 表与 scripts-guide 注明）
- onboarding 排障表补 Windows `python3`→`python` 条目
## [2026-10-10] — v4.0.6（文档勘误）

- social 平台指南分页参数说明补全（`quora_question_search` 支持 `page`）

## [2026-10-10] — v4.0.5（社交平台文档完善 + 发布包精简）

- social 平台指南补全 Quora 三件套工具表与双平台工作流（Reddit/Quora 链路同构，问答平台痛点表述更具体）
- 发布包不再包含仓库内部 QA 手册（含开发环境路径，与技能使用无关）

## [2026-10-10] — v4.0.4（网络兼容性 + 输出健壮性）

- **probe 网络访问标准化**：遵循 http_proxy/https_proxy/no_proxy 环境变量的标准代理解析（未设置则直连），与 bridge 行为一致——需要代理出网的网络环境（企业网/校园网）不再连接失败
- **控制台输出编码健壮化**：异常终端/重定向流下探活输出不中断
- social 端点新增 Quora 三件套（与 amazon 端点双侧同挂，Reddit+Quora 共 7 工具），相关文档与平台包计数同步

## [2026-10-10] — v4.0.3（文档口径统一）

- probe 输出在端点配置异常时结构化降级（完整输出全部端点结果，不中断）
- mercado 页状态与实测对齐（通用配额工具可调用，业务工具待账号开通）；walmart/shopee/tiktok 文档工具计数口径统一「N 业务 + 通用配额」；README 配额工具名更新
## [2026-10-10] — v4.0.2（配额工具服务端改名适配 + 诊断输出优化）

- **usage_query → common_usage_query（服务端当日改名并铺满 9 端点）**：probe/healthcheck 改为动态探测端点工具清单里可用的配额工具名（两个名字都认）；文档口径统一为「全端点通用配额工具」；各平台页/构建器工具数刷新为 10:45 实测（各端点 +1=通用配额工具，mercado 0→1）
- **probe `call_tool` 恢复 Mcp-Session-Id 传播**（配额查询依赖会话头），保留全部异常与非 JSON 响应防护
- **healthcheck 端点解析结构化降级**：敌意 SORFTIME_MCP_URL / platform.json 触发白名单阻断时输出结构化 error 检查项（含修复指引），不再裸 traceback——`--json` 消费方始终拿到完整 JSON
## [2026-10-10] — v4.0.1（端点安全加固）

- **端点解析安全镇流（单点收口）**：`get_mcp_url()` 对任何来源（环境变量 `SORFTIME_MCP_URL` / 包内 `config/platform.json` / 默认值）的解析结果强制 host 白名单（仅 `mcp.sorftime.com`），被篡改的 env/config 直接抛错阻断，凭证不再可能经新路径（healthcheck/probe/sync_manager）静默外发——与 bridge `_assert_official_url` 同一安全模型
- **probe 配额查询加固**：`call_tool` 全链异常与非 JSON 响应防护，配额查询失败不影响 9 端点探活主流程
- **构建器 fail-fast**：平台包 frontmatter 四处替换（name/description/trigger/version）失配即构建中止，杜绝包以错误身份静默产出
## [2026-10-10] — v4.0.0（MCP 按平台拆分适配 + 架构重构）

- **平台拆分适配**：Sorftime MCP 拆分为 8 平台端点（amazon/walmart/shopee/tiktok/temu/1688/mercado/social），根端点保留全平台兼容（113 工具=8 端点并集，2026-10-10 实测）。端点解析链：`SORFTIME_MCP_URL` 环境变量 > 包内 `config/platform.json` > 根端点（`utils/env_config.get_mcp_url()`，bridge/sync_manager 统一走它）
- **平台分发包**：新增构建器 `build/build_packages.py`——从本仓单一事实源产出 8 个自包含平台包（sorftime-amazon/walmart/shopee/tiktok/temu/ali1688/mercado/social，各含平台定制热层+平台知识页+全量脚本+端点预置），清单 `build/dist/manifest-<ver>.json`；同一把 Account-SK 全端点通用，key 仍存用户级 `~/.sorftime/env`
- **热层重构（渐进披露）**：SKILL.md 58KB→7KB——onboarding 话术/Walmart 工具表/TikTok 指南/内容质检/脚本指南全量下沉 `references/`（onboarding/gotchas/scripts-guide/content-quality + platforms/ 8 页）；方法论卡与闭环工作流原位保留
- **TikTok 工具族服务端改名适配**：旧 7 工具全部下线，新 18 工具上线（`*_request`/`*_search_from_name` 规范）；同参等价改名进 mcp_client 自动映射，行为不等价的不映射（干净报错优于错参失败）；`tiktok_product_search` 已存在（30+ 筛选），新增店铺/达人/品牌/视频/话题标签五大搜索族
- **新工具接入**（文档+实测标注）：`usage_query` 配额查询（无参，credit_left）/ `category_low_price_search` 低价商城类目分析 / `product_content` Listing+A+ 内容拆解 / `seller_search(_from_name)` 卖家搜索 / `quora_*` 三件套（挂 amazon 端点）——其中 seller/quora 实测暂无返回数据（数据覆盖铺设中，如实标注）
- **参数口径更新**：`product_search` 搜索参数 `search_name`→`keyword`；`keyword_detail` 站点参数统一为 `amz_site`（其余 keyword 族仍为 `keyword_support_site`）；`category_report_from_history` 已从端点下线
- **新脚本**：`scripts/probe_endpoints.py`（9 端点探活+工具清单+配额；`--matrix` 再生 tool-matrix.md 按端点分组）；healthcheck 升级为端点感知（任意端点握手+伪工具 key 失效检测+credit_left 内嵌）；tool-matrix.md 按端点再生（113 工具带必填参数）
- **Amazon 参数陷阱表按活 schema 重写**；mercado 端点已上线（0 工具，按账号数据包开通）与 social 端点（Reddit 三件套）入档
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
