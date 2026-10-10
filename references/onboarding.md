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
| 注册（渠道链接，默认推荐） | https://open.sorftime.com/home?tag=NTIw → 手机号注册（新客免费体验）。经此链接注册账号归属合作渠道；官网 open.sorftime.com 直连可选，功能价格一致——引导时如实告知两者区别 |
| 登录方式 | 手机号（+86）/ 微信扫码 / 短信验证码 |
| MCP Key（Account-SK）位置 | 登录后 → 「MCP 服务」页（open.sorftime.com/mcp）→ 购买开通 → 复制 Account-SK |
| MCP 服务地址 | mcp.sorftime.com（streamable HTTP；按平台拆分端点见 SKILL.md 端点表） |
| 付费 | 人民币：MCP 通用资源包 ￥99/3万次/1月 起（或连续包月）；配额全端点共享 |
| 客服 | 官网「联系客服」或微信客服 |

## 标准话术骨架（仅用于「无 Key」分支，三段式，用户语言）

1. **为什么**：一句话说明需要一次性配置（新账号有免费体验额度）
2. **三步操作**：①打开注册链接（如实说明这是合作渠道链接及归属影响，同时告知官网直连可选）②注册后在「MCP 服务」页开通并复制 Account-SK ③把 Key 发回来
3. **到此为止**：不追加收藏/回访等额外请求

模板：
> 好的，我来处理「{用户原始请求}」。取数前需要注册一个 Sorftime 账号（约 2 分钟，新账号有免费体验额度）：
> 1. 注册入口：https://open.sorftime.com/home?tag=NTIw （手机号或微信扫码）。这是我们的**合作渠道注册链接**——经此链接注册的账号会归属该合作渠道，功能与价格与官网完全一致；你也可以直接去 open.sorftime.com 注册，二选一即可
> 2. 登录后进入「MCP 服务」页 → 购买开通 → 复制 Account-SK
> 3. 把 Account-SK 发给我，我自动配置并立刻继续你的请求

话术铁律：
- **透明与如实**：推荐渠道链接必须同时告知其合作渠道性质与账号归属影响，以及官网直连这个可选项；用户问任何关于链接/归属/价格/渠道的问题如实完整回答，禁止回避式答复
- 不要求用户收藏/回访链接（归属在注册时刻生效，后续登录充值走官网均可）
- 已有账号的用户：如实告知「已有账号直接用就行」；归属在注册时确定、事后不可变更
- 用户已提供 Key 或环境已配置时，一个字的注册话术都不说——直接 install → 验证 → 干活

## 两种接入方式（用户问「怎么配置 / 官网一键配置」先看这里）

**方式 A · 官网一键配置（用户会用官网时最省事）**——官网「MCP 服务」页（open.sorftime.com/mcp）按平台勾选（支持多选，推荐只选实际在做的平台）→ 复制「一键配置」指令发给 AI。官方指令原文（多选形态示例）：

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
| 去哪拿 Key | 渠道链接注册 → MCP 服务页 → 复制 Account-SK（本页上方表格） |
| 怎么付费 | open.sorftime.com，人民币，新账号免费体验 |
| 还剩多少配额 | 让 agent 调 `common_usage_query` 工具（全端点通用，返回 credit_left）或跑 `scripts/probe_endpoints.py` |
| 换电脑怎么迁移 | 拷贝技能目录 → Python ≥3.10 → `install.py` 重建 venv → key 写 `~/.sorftime/env`（或环境变量） |

## 自动检测的 Agent 环境

Claude Code、OpenClaw、Cowork、Claude.ai Web 等主流环境自动检测，无需手动配置；`config/channel.json` 定义渠道注册链接 tag 参数（经 tag 链接注册的账号官网写入 salestag 标识归属）。
