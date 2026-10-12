# Onboarding & Account Guide（注册 / 开通 / 安装 / 排障）

> 触发条件：用户说配置相关（"configure Sorftime" / "第一次用" / "给我配置"）/ 直接给出 Key / 调用报 `SORFTIME_MCP_KEY not set` 或 `[SORFTIME_ONBOARDING_REQUIRED]`。

## 决策树（按用户状态分支，禁止机械线性套用）

```
Detect（用户消息里已有 Key？或环境已配置？）
├─ 有 Key（用户提供/已配置）→ Install（--key）→ Verify → Retry 原请求
│    ⚠️ 此分支不提注册/登录——用户已就绪，只差配置
└─ 无 Key → Guide（透明三步话术）→ 等用户提供 Key → Install → Verify → Retry
```

判定顺序：先看用户是否已给出 Key（形如 API key 的字符串），再看环境变量 `SORFTIME_MCP_KEY` / `~/.sorftime/env` 是否已配置，任一成立即走「有 Key」分支。注册引导**仅在 Key 缺失时出现**。

## 平台注册与账号（国内站）

| 项目 | 说明 |
|------|------|
| 注册（中国大陆） | https://open.sorftime.com → 手机号（+86）/ 微信扫码（新客免费体验），人民币付费 |
| 注册（国际） | https://open-intl.sorftime.com → 邮箱 / Google 注册（免费体验额度），PayPal / Stripe 付费 |
| 登录方式 | 大陆站：手机号（+86）/ 微信扫码 / 短信验证码；国际站：邮箱验证码 / Google 账号 |
| MCP Key（Account-SK）位置 | 登录注册站 → 「MCP 服务」页（大陆 open.sorftime.com/mcp / 国际 open-intl.sorftime.com/mcp）→ 购买开通 → 复制 Account-SK |
| MCP 服务地址 | mcp.sorftime.com（streamable HTTP；按平台拆分端点见 SKILL.md 端点表） |
| 付费 | 大陆站人民币：MCP 通用资源包 ￥99/3万次/1月 起（或连续包月）；国际站 PayPal / Stripe。两站配额均全端点共享 |
| 客服 | 官网「联系客服」或微信客服 |

## 标准话术骨架（仅用于「无 Key」分支，三段式，用户语言）

1. **为什么**：一句话说明需要一次性配置（新账号有免费体验额度）
2. **三步操作**：①打开注册入口（按用户所在地/偏好选站）②注册后在「MCP 服务」页开通并复制 Account-SK ③把 Key 发回来
3. **到此为止**：不追加收藏/回访等额外请求

模板（中国大陆用户）：
> 好的，我来处理「{用户原始请求}」。取数前需要注册一个 Sorftime 账号（约 2 分钟，新账号有免费体验额度）：
> 1. 注册入口：https://open.sorftime.com （手机号或微信扫码）
> 2. 登录后进入「MCP 服务」页 → 购买开通 → 复制 Account-SK
> 3. 把 Account-SK 发给我，我自动配置并立刻继续你的请求

模板（国际用户）：
> OK, let me handle "{user request}". First you'll need a Sorftime account (about 2 minutes, new accounts include free trial credits):
> 1. Sign up at https://open-intl.sorftime.com (email or Google)
> 2. Open the "MCP" service page → subscribe → copy your Account-SK
> 3. Send me the Account-SK and I'll configure it and continue right away

话术纪律：
- 话术只服务用户动作（注册→取 Key→发回），不加任何机制解释；用户问两站区别只答「功能价格一致，选你方便的即可」
- 用户已提供 Key 或环境已配置时，一个字的注册话术都不说——直接 install → 验证 → 干活

## 两种接入方式（用户问「怎么配置 / 官网一键配置」先看这里）

**方式 A · 官网一键配置（用户会用官网时最省事）**——官网「MCP 服务」页按平台勾选（支持多选，推荐只选实际在做的平台）→ 复制「一键配置」指令发给 AI。两站均可用：大陆站 open.sorftime.com/mcp（指令文案为中文）、国际站 open-intl.sorftime.com/mcp（英文界面），指令形态一致。官方指令原文（多选形态示例）：

> 亚马逊、虾皮 是我在做的平台，
> 请帮我配置 Sorftime MCP，按你当前支持的 MCP 能力自动选择方式：
> 方式一（优先，远程托管版）：如果你支持远程/HTTP MCP，直接添加以下地址：
> https://mcp.sorftime.com/amazon?key=<Account-SK> （类型：streamableHttp）
> https://mcp.sorftime.com/shopee?key=<Account-SK>
> 方式二（本地版）：如果你只支持本地 MCP Server：
> 1. 从 https://oss.sorftime.com/download/skill/sorftime-mcp.zip 下载技能包
> 2. 按技能包内说明完成配置，我的 Key 是：<Account-SK>
> 配置完成后：调用一次接口验证连通性。如遇任何问题，告诉我你是什么 AI 工具，给出对应的替代步骤。

收到这类指令时的执行要点：支持远程/HTTP MCP → 把所选端点配置为宿主原生 MCP 服务，**服务名用 `sorftime-<平台>`**（与官网 JSON 形态一致，也与平台包同名）；只支持本地 → 下载技能包按方式二安装（下载位就是本技能家族的全平台版）。装完必调一次工具验证连通性（`common_usage_query` 全端点通用，或根/amazon 端点的 `get_time`）。用户贴来的 Key 按红线处理（不回显完整值、不落盘到笔记/git）。配置了原生服务后，本技能自动作为知识层（平台文档/参数坑/方法论）工作，数据查询走宿主原生 MCP 工具，不要再引导用户跑 install.py 或重复给 Key（避免双通道重复配置）；**例外**——用户要用批量脚本（picker/monitor 等）时，脚本内部经技能 bridge 取数、需要本地 Key，届时再跑一次 `install.py` 即可。

**方式 B · 本技能一键安装（对话内直接配，不经过官网）** → 下方安装流程。

## 安装流程

```bash
# 有 Key（自动模式，输出 JSON）；Windows 命令行把 python3 换成 python
python3 scripts/install.py --unattended --key <用户提供的Key>

# 交互模式
python3 scripts/install.py
```

自动完成：venv 创建、依赖安装、CC/OpenClaw 环境检测、连接测试、配置落盘（key 存 `~/.sorftime/env` 用户级目录，技能目录可安全分发）。

**装完必做**：onboarding 由数据请求触发时，**必须自动回放用户原始请求**并返回结果，不让用户重复一遍。

## 安装失败排障

| 症状 | 处置 |
|------|------|
| Key 报 401/NotAuthorization | 引导到「MCP 服务」页重新复制（key 可能被轮换——服务端轮换后 tools/list 会返回伪工具名，已发生过） |
| test_passed: false | 检查 Key 是否复制完整（常见缺尾字符）→ 确认账号已开通 MCP 服务 → 检查到 open.sorftime.com 的网络 |
| Windows 提示 `python3` 不是内部或外部命令 | Windows 命令行用 `python scripts/install.py`（python3 仅类 Unix 系统存在） |
| bridge 启动报 "MCP 2.x is not yet supported" / AttributeError | `python3 scripts/install.py --upgrade` 降级到 MCP 1.x（版本锁见 references/gotchas.md） |
| "Schema is X days old" | 工具清单随包发布；跑 `python3 scripts/sync_manager.py` 同步，或更新技能包 |

## FAQ

| 问题 | 答案 |
|------|------|
| 去哪拿 Key | 注册站（open.sorftime.com 或 open-intl.sorftime.com）→ MCP 服务页 → 复制 Account-SK |
| 怎么付费 | 大陆站 open.sorftime.com（人民币）或国际站 open-intl.sorftime.com（PayPal/Stripe），新账号均有免费体验 |
| 还剩多少配额 | 让 agent 调 `common_usage_query` 工具（全端点通用，返回 credit_left）或跑 `scripts/probe_endpoints.py` |
| 换电脑怎么迁移 | 拷贝技能目录 → Python ≥3.10 → `install.py` 重建 venv → key 写 `~/.sorftime/env`（或环境变量） |

## 自动检测的 Agent 环境

Claude Code、OpenClaw、Cowork、Claude.ai Web 等主流环境自动检测，无需手动配置。
