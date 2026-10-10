#!/usr/bin/env python3
"""构建器：从本仓（单一事实源）产出 8 个平台分发包。

用法:
  python3 build/build_packages.py            # 产出 dist/sorftime-<platform>/
  python3 build/build_packages.py --clean    # 先清空 dist 再产出

每个平台包 = 自包含技能目录：
  SKILL.md                    平台定制热层（端点表/路由表替换为该平台版本）
  references/platforms/<x>.md 平台知识页 + 共享 references（onboarding/gotchas/
                              scripts-guide/content-quality/tool-matrix/方法论卡/
                              workflows；tiktok 包另带 rankings/categories JSON）
  scripts/                    按平台适用面过滤的脚本（专属引擎只进对应平台包；端点路由由 config/platform.json 预置）
  config/platform.json        {"platform","mcp_url","display_name"} ← get_mcp_url() 读这里
  SECURITY.md/LICENSE/CHANGELOG.md/requirements.txt/.env.example/config/channel.json

排除项：.venv/.git/.sync-backups/tests/__pycache__/build/dist 本身/.env（key 永不进包）。
产出清单：dist/manifest-<version>.json（包名/大小/sha256/工具数）。
"""

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "build" / "dist"

PLATFORMS = {
    "amazon": {
        "pkg": "sorftime-amazon", "display": "Amazon", "doc": "amazon.md",
        "url": "https://mcp.sorftime.com/amazon", "tools": 43,
        "desc": "Sorftime Amazon 卖家助手 —— 亚马逊市场情报与选品智能体（平台专属端点 mcp.sorftime.com/amazon，43 工具）。产品搜索与 ASIN 深拆、关键词研究、类目报告、隐赚指数选品⭐、低价商城(Haul)类目分析、卖家搜索、Listing 内容与 A+ 拆解、Quora 舆情、配额查询。将任意 MCP 接入的 AI agent 变成 Amazon 市场情报专家。",
        "trigger": "亚马逊/amazon/ASIN/asin 拆解/选品/找产品/爆款/竞品/竞品分析/关键词/流量词/反查关键词/长尾词/类目/类目分析/市场分析/蓝海/隐赚指数/利润测算/FBA 费用/差评/买家痛点/评论分析/低价商城/Haul/卖家分析/查卖家/Quora/配额/余额/listing 审计/A+ 内容/product research/keyword research/competitor analysis/blue ocean",
        "related": "1688 找货联动见 `references/platforms/ali1688.md`（本包未含，需全平台版或 sorftime-ali1688 包）；跨平台价差卡（Amazon×Walmart）见方法论卡",
    },
    "walmart": {
        "pkg": "sorftime-walmart", "display": "Walmart", "doc": "walmart.md",
        "url": "https://mcp.sorftime.com/walmart", "tools": 19,
        "desc": "Sorftime Walmart 卖家助手 —— 沃尔玛市场情报与选品智能体（平台专属端点 mcp.sorftime.com/walmart，19 工具）。关键词研究、产品与变体分析、类目报告、流量词反查、收藏夹管理；美国站专属。将任意 MCP 接入的 AI agent 变成 Walmart 市场情报专家。",
        "trigger": "沃尔玛/walmart/沃尔玛选品/walmart 选品/walmart 关键词/walmart 竞品/walmart 类目/walmart 产品分析/1P 自营/WFS/跨平台价差",
        "related": "与 Amazon 对比见方法论卡 `tactical/cross-platform-gap.md`（跨平台价差，需两平台数据）",
    },
    "shopee": {
        "pkg": "sorftime-shopee", "display": "Shopee", "doc": "shopee.md",
        "url": "https://mcp.sorftime.com/shopee", "tools": 17,
        "desc": "Sorftime Shopee 卖家助手 —— 虾皮市场情报与选品智能体（平台专属端点 mcp.sorftime.com/shopee，17 工具）。8 站点（MY/PH/VN/TH/ID/SG/TW/BR）关键词研究、产品搜索、类目趋势、本土店×跨境店对比。将任意 MCP 接入的 AI agent 变成 Shopee 市场情报专家。",
        "trigger": "虾皮/shopee/shopee 选品/shopee 关键词/shopee 类目/东南亚电商/本土店/跨境店对比",
        "related": "跨平台方法论卡见 `references/methodology-cards/`",
    },
    "temu": {
        "pkg": "sorftime-temu", "display": "TEMU", "doc": "temu.md",
        "url": "https://mcp.sorftime.com/temu", "tools": 10,
        "desc": "Sorftime TEMU 卖家助手 —— TEMU 市场情报与选品智能体（平台专属端点 mcp.sorftime.com/temu，10 工具）。US/EU 两站，类目多维筛选（40 个 min/max 参数）、产品与店铺分析、趋势追踪。将任意 MCP 接入的 AI agent 变成 TEMU 市场情报专家。",
        "trigger": "temu/TEMU 选品/temu 类目/temu 产品/temu 店铺/temu 趋势",
        "related": "跨平台方法论卡见 `references/methodology-cards/`",
    },
    "tiktok": {
        "pkg": "sorftime-tiktok", "display": "TikTok Shop", "doc": "tiktok.md",
        "url": "https://mcp.sorftime.com/tiktok", "tools": 19,
        "desc": "Sorftime TikTok Shop 卖家助手 —— TikTok 电商市场情报与选品智能体（平台专属端点 mcp.sorftime.com/tiktok，19 工具）。8 站点，产品多维搜索（30+ 筛选）、店铺/达人/品牌/视频/话题标签五大搜索族、类目树与趋势、228 叶子类目预计算榜单。将任意 MCP 接入的 AI agent 变成 TikTok Shop 市场情报专家。",
        "trigger": "tiktok/TikTok Shop/抖音海外版/tiktok 选品/tiktok 达人/tiktok 店铺/tiktok 类目/tiktok 视频/话题标签/带货",
        "related": "达人×带货方法论见 `references/methodology-cards/`；本包含 `references/tiktok-rankings.json` 预计算榜单（tier-1 零调用读榜）",
    },
    "ali1688": {
        "pkg": "sorftime-ali1688", "display": "1688", "doc": "ali1688.md",
        "url": "https://mcp.sorftime.com/1688", "tools": 7,
        "desc": "Sorftime 1688 采购源助手 —— 工厂直采与供应链情报智能体（平台专属端点 mcp.sorftime.com/1688，7 工具）。关键词找货、多维筛选（实力商家/超级工厂/回购率/版权）、商品详情与 SKU 明细、反向图搜。亚马逊选品→1688 找货→利润测算一条龙。将任意 MCP 接入的 AI agent 变成 1688 采购情报专家。",
        "trigger": "1688/阿里巴巴批发/找货源/找工厂/供应商/实力商家/超级工厂/MOQ/起订量/采购/图搜找货/源头工厂",
        "related": "亚马逊端选品联动见 `references/platforms/amazon.md`（本包未含，需全平台版或 sorftime-amazon 包）；利润测算 `scripts/calculator.py`",
    },
    "mercado": {
        "pkg": "sorftime-mercado", "display": "Mercado Libre", "doc": "mercado.md",
        "url": "https://mcp.sorftime.com/mercado", "tools": 1,
        "desc": "Sorftime 美客多（Mercado Libre）助手 —— 拉美市场情报智能体（专属端点 mcp.sorftime.com/mercado）。端点已上线，当前含通用配额工具；业务工具按账号数据包逐步开通，用 scripts/probe_endpoints.py 可随时复查。",
        "trigger": "美客多/mercado libre/mercado/拉美电商/墨西哥电商/巴西电商",
        "related": "工具上线后用 `python3 scripts/probe_endpoints.py` 复查清单，再对照 `references/tool-matrix.md`",
    },
    "social": {
        "pkg": "sorftime-social", "display": "海外社媒（Reddit·Quora）", "doc": "social.md",
        "url": "https://mcp.sorftime.com/social", "tools": 7,
        "desc": "Sorftime 海外社媒舆情助手 —— Reddit + Quora 市场情报智能体（专属端点 mcp.sorftime.com/social，7 工具）。Reddit 产品词/品牌词搜帖、正文与热度、评论痛点挖掘；Quora 舆情三件套本端点与 amazon 端点双侧同挂。将任意 MCP 接入的 AI agent 变成海外社媒情报专家。",
        "trigger": "reddit/海外社媒/社媒舆情/老外怎么说/买家讨论/痛点挖掘/reddit 帖子/品牌舆情",
        "related": "痛点挖掘方法论 `references/methodology-cards/comprehensive/review-mining.md`；Quora 与 amazon 端点双侧同挂",
    },
}

VERSION_RE = re.compile(r"^version:\s*(.+)$", re.M)


def get_version() -> str:
    m = VERSION_RE.search((ROOT / "SKILL.md").read_text(encoding="utf-8"))
    return m.group(1).strip() if m else "0.0.0"


def read_root_skill() -> str:
    return (ROOT / "SKILL.md").read_text(encoding="utf-8")


def replace_section(text: str, header: str, new_body: str) -> str:
    """替换 `## <header>` 起到下一个 `## ` 前的整节。"""
    pat = re.compile(rf"(^## {re.escape(header)}\n)(.*?)(?=^## |\Z)", re.M | re.S)
    if not pat.search(text):
        raise RuntimeError(f"section not found: {header}")
    nl = chr(10)
    if not new_body.endswith(nl + nl):
        new_body = new_body.rstrip(nl) + nl + nl
    return pat.sub(lambda _: new_body, text, count=1)


def _sub_or_die(text: str, pattern: str, repl: str, what: str) -> str:
    """正则替换必须命中一次，失配即抛错——防止包以错误身份静默产出。"""
    new, n = re.subn(pattern, repl, text, count=1, flags=re.M)
    if n != 1:
        raise RuntimeError(f"frontmatter 替换失配（{what}）——源 SKILL.md 结构已变化，构建中止")
    return new


def gen_platform_skill(platform: dict, version: str, platform_key: str) -> str:
    text = read_root_skill()
    # frontmatter 定制（全部 fail-fast）
    text = _sub_or_die(text, r"^name: sorftime-seller-agent$", f"name: {platform['pkg']}", "name")
    text = _sub_or_die(text, r'^description: ".*"$', f'description: "{platform["desc"]}"', "description")
    text = _sub_or_die(text, r'^trigger: ".*"$', f'trigger: "{platform["trigger"]}"', "trigger")
    text = _sub_or_die(text, r"^version: .+$", f"version: {version}", "version")
    # 端点表 → 本平台版
    endpoint_body = (
        f"## 🌐 Platform Endpoint\n\n"
        f"| 项 | 值 |\n|---|---|\n"
        f"| 平台 | **{platform['display']}** |\n"
        f"| 端点 | `{platform['url']}` |\n"
        f"| 工具数 | {platform['tools']}（{get_version_sync_note(platform['tools'])}） |\n"
        f"| 知识页 | `references/platforms/{platform['doc']}` |\n\n"
        f"- 端点解析：环境变量 `SORFTIME_MCP_URL` > 本包 `config/platform.json`（已预置上面的端点）。"
        f"**同一把 Account-SK 全端点通用，配额共享**。\n"
        f"- 本包是总技能 `sorftime-seller-agent`（全平台版）的 {platform['display']} 专版，同源构建、同步迭代；"
        f"官网 MCP 页「一键配置」生成的原生服务名与本包同名（`sorftime-{platform_key}`），已配原生服务时本技能自动作为知识层（见「数据通道」节）。\n"
        f"- 其他平台（Amazon/Walmart/Shopee/TikTok/TEMU/1688/Mercado/社媒）有独立端点与独立技能包；"
        f"本包只管 {platform['display']}。配额查询：`common_usage_query`（全端点通用，无参数返回 credit_left）。\n"
    )
    text = replace_section(text, "🌐 Platform Endpoints（MCP 按平台拆分）", endpoint_body)
    # 路由表 → 本平台版
    router_body = (
        f"## Platform Knowledge Router\n\n"
        f"动手前先读平台知识页（工具表 / 参数 traps / 数据坑 / 站点枚举，全在那里）：\n\n"
        f"- **{platform['display']}** → `references/platforms/{platform['doc']}`\n"
        f"- {platform['related']}\n"
        f"- **通用坑**（MCP SDK 版本锁 / 响应包裹格式 / 中文前缀解析）→ `references/gotchas.md`\n"
    )
    text = replace_section(text, "Platform Knowledge Router", router_body)
    # Scripts 表按平台过滤（包内不含的引擎不列，防死命令）
    common_rows = (
        "| 利润测算 | 全平台（数据经 MCP 工具取） | `scripts/calculator.py` |\n"
        "| 监控 / 日常报告 | 全平台 | `scripts/monitor.py` |\n"
        "| 候选清单独立复核（Go/No-Go 前） | 全平台 | `scripts/verify_candidates.py` + `scripts/review_shortlist.py` |\n"
        "| 环境体检 / 端点探活 / 配额 | 全平台 | `scripts/healthcheck.py` / `scripts/probe_endpoints.py` |\n"
    )
    extra_rows = {
        "amazon": ("| 选品发现 / 蓝海（四层风险咨询制，永不隐藏产品） | Amazon | `scripts/picker.py --mode newbie\|blueocean` |\n"
                   "| 竞品 / 关键词 / 市场分析 | Amazon | `scripts/analyst.py` |\n"),
        "walmart": ("| 选品发现 / 蓝海 | Walmart | `scripts/walmart_picker.py --mode blueocean` |\n"
                    "| 竞品 / 关键词 / 市场分析 | Walmart | `scripts/walmart_analyst.py` |\n"),
        "tiktok": "| TikTok 类目发现（榜单兜底腿） | TikTok | `scripts/discover_tiktok.py` |\n",
    }
    rows = extra_rows.get(platform_key, "") + common_rows
    note = "" if platform_key in ("amazon", "walmart") else (
        "\n本包不含 Amazon/Walmart 选品引擎脚本（属总技能与对应平台包）；本平台单点查询直接走 MCP 工具（知识页有全工具表）。")
    scripts_body = (
        "## Scripts（引擎）\n\n"
        "| 场景 | 平台适用 | 入口 |\n|------|------|------|\n" + rows + note + "\n"
        "完整用法与分层输出原则 → `references/scripts-guide.md`（注意该指南的跨平台引擎示例属总技能）。"
    )
    text = replace_section(text, "Scripts（引擎）", scripts_body)
    return text


def get_version_sync_note(tools: int) -> str:
    return "2026-10-10 实测" if tools else "端点已上线，工具随账号数据包开通"


README_TEMPLATE = """# Sorftime {display} 卖家助手 · 快速上手

> 本包是总技能 **sorftime-seller-agent** 的 {display} 专版——数据与总技能同源、同步迭代，只接 {display} 端点。同一把 Account-SK 全平台通用、配额共享。

## 三步开始

**第 1 步 · 放进你 AI 助手的技能目录**——把整个 `{pkg}` 文件夹（不要拆散）复制到对应目录，然后重启 / 新开会话：

| 你在用 | 放到这里 |
|---|---|
| Claude Code | `~/.claude/skills/`（Windows：`C:\\Users\\你的用户名\\.claude\\skills\\`） |
| ZCode | `~/.zcode/skills/` |
| OpenClaw | active workspace 的 skills 目录 |
| 其他支持 Agent Skills 的工具 | 该工具的技能目录（其文档会写） |

**第 2 步 · 拿到你的 Key（Account-SK）**——注册/登录 https://open.sorftime.com （新账号有免费体验额度）→ 进入「MCP 服务」页 → 购买开通 → 复制 **Account-SK**。一次开通全平台可用，配额按实际调用次数计。

**第 3 步 · 让 AI 配好**——直接对你的 AI 说：

> 帮我配置 Sorftime，我的 Key 是 <粘贴 Account-SK>

AI 会自动完成安装、验证并跑通第一条数据。喜欢手动：`python scripts/install.py --key <你的Key>`（**Windows 命令行用 `python`，不是 `python3`**）。

## 也可以走官网一键配置

官网「MCP 服务」页可按平台勾选（支持多选）生成配置指令。若你的 AI 已按官网指令配置了原生 MCP 服务（服务名与本包同名：`sorftime-{key}`），本技能自动作为知识层（平台工具文档 / 参数坑 / 选品方法论）配合使用，数据查询走原生 MCP 工具，**无需再配 Key**；要用批量脚本（选品引擎/监控）时再跑一次 `install.py` 配本地 Key 即可。

## 常用

- 环境体检：`python scripts/healthcheck.py`（连接 / 端点 / 配额一次看清）
- 查剩余配额：直接问 AI「还剩多少配额」
- **想加做别的平台**：再放一个对应平台包（同一把 Key 直接用），或换总技能 `sorftime-seller-agent`（全平台合一，官网下载地址 oss.sorftime.com/download/skill/sorftime-mcp.zip）
- 出问题：`references/onboarding.md` 排障表；`references/platforms/{doc}` 本平台全部工具与参数坑

## 当前端点

`{url}` · {tools} 工具（以 `scripts/probe_endpoints.py` 实测为准，服务端持续上新）
"""


def write_platform_readme(dst: Path, platform_key: str) -> None:
    p = PLATFORMS[platform_key]
    (dst / "README.md").write_text(
        README_TEMPLATE.format(display=p["display"], pkg=p["pkg"], key=platform_key,
                               url=p["url"], tools=p["tools"], doc=p["doc"]),
        encoding="utf-8")


def write_platform_matrix(dst: Path, platform_key: str) -> None:
    """平台包内工具清单只保留本端点视图，杜绝跨平台工具误导调用。"""
    import re as _re
    full = (ROOT / "references" / "tool-matrix.md").read_text(encoding="utf-8")
    target = PLATFORMS[platform_key]["url"].rstrip("/")
    parts = _re.split(r"(?=^## )", full, flags=_re.M)
    kept = [p for p in parts[1:] if target in p.splitlines()[0]]
    body = "".join(kept) if kept else f"## {PLATFORMS[platform_key]['display']} — {target}\n\n以 `python scripts/probe_endpoints.py --matrix` 再生。\n"
    out = (
        "# 工具清单（本包视角）\n\n"
        f"> **本包只接 {PLATFORMS[platform_key]['display']} 端点（`{target}`）**，下表只含本端点工具。\n"
        f"> 其他平台各有独立端点与技能包（{"、".join(PLATFORMS[k]["pkg"] for k in PLATFORMS if k != platform_key)}），"
        "同一把 Account-SK 全端点通用——需要时安装对应平台包或总技能 `sorftime-seller-agent`，不要用本包直接调其他平台的工具。\n\n"
        + body
    )
    (dst / "references" / "tool-matrix.md").write_text(out, encoding="utf-8")


def copy_shared_refs(dst: Path, platform_key: str) -> None:
    refs = dst / "references"
    refs.mkdir(parents=True, exist_ok=True)
    (refs / "platforms").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "references" / "platforms" / PLATFORMS[platform_key]["doc"],
                 refs / "platforms" / PLATFORMS[platform_key]["doc"])
    for name in ["onboarding.md", "gotchas.md", "scripts-guide.md", "content-quality.md"]:
        src = ROOT / "references" / name
        if src.exists():
            shutil.copy2(src, refs / name)
    write_platform_matrix(dst, platform_key)  # 平台专属视图，不再整包复制全端点矩阵
    # scripts-guide 包级横幅：跨平台引擎示例属总技能，防包内死命令
    sg = refs / "scripts-guide.md"
    if sg.exists():
        body = sg.read_text(encoding="utf-8")
        banner = (f"> **本包注（{PLATFORMS[platform_key]['display']} 专版）**：本指南的引擎示例覆盖多平台，"
                  f"本包只随带适用于 {PLATFORMS[platform_key]['display']} 的脚本（以 SKILL.md Scripts 表为准）；"
                  "其他平台的引擎（picker/analyst/walmart_* 等）属总技能 `sorftime-seller-agent` 或对应平台包，"
                  "在本包内执行会报文件不存在。\n\n")
        sg.write_text(banner + body, encoding="utf-8")
    for sub in ["methodology-cards", "workflows"]:
        src = ROOT / "references" / sub
        if src.is_dir():
            shutil.copytree(src, refs / sub, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__"))
    if platform_key == "tiktok":
        for name in ["tiktok-rankings.json", "tiktok-categories.json"]:
            src = ROOT / "references" / name
            if src.exists():
                shutil.copy2(src, refs / name)


# 平台专属脚本的适用面：其余平台包不随带（避免错放误导）
PLATFORM_ONLY_SCRIPTS = {
    "walmart": {"walmart_picker.py", "walmart_analyst.py"},
    "amazon": {"picker.py", "analyst.py"},
    "tiktok": {"discover_tiktok.py"},
}


def copy_scripts(dst: Path, platform_key: str) -> None:
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache")
    shutil.copytree(ROOT / "scripts", dst / "scripts", ignore=ignore, dirs_exist_ok=True)
    for owner, files in PLATFORM_ONLY_SCRIPTS.items():
        if owner == platform_key:
            continue
        for fname in files:
            target = dst / "scripts" / fname
            if target.exists():
                target.unlink()


def build(platform_key: str, version: str) -> dict:
    p = PLATFORMS[platform_key]
    pkg_dir = DIST / p["pkg"]
    if pkg_dir.exists():
        shutil.rmtree(pkg_dir)
    pkg_dir.mkdir(parents=True)

    (pkg_dir / "SKILL.md").write_text(gen_platform_skill(p, version, platform_key), encoding="utf-8")
    write_platform_readme(pkg_dir, platform_key)
    copy_shared_refs(pkg_dir, platform_key)
    copy_scripts(pkg_dir, platform_key)

    cfg = pkg_dir / "config"
    cfg.mkdir(exist_ok=True)
    (cfg / "platform.json").write_text(
        json.dumps({"platform": platform_key, "mcp_url": p["url"],
                    "display_name": p["display"]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    shutil.copy2(ROOT / "config" / "channel.json", cfg / "channel.json")

    for name in ["SECURITY.md", "LICENSE", "CHANGELOG.md", "requirements.txt", ".env.example"]:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, pkg_dir / name)

    # 打包体积与指纹
    total = sum(f.stat().st_size for f in pkg_dir.rglob("*") if f.is_file())
    digest = hashlib.sha256()
    for f in sorted(x for x in pkg_dir.rglob("*") if x.is_file()):
        digest.update(str(f.relative_to(pkg_dir)).encode())
        digest.update(f.read_bytes())
    return {"pkg": p["pkg"], "platform": platform_key, "display": p["display"],
            "endpoint": p["url"], "tools": p["tools"], "version": version,
            "size_bytes": total, "sha256_dir": digest.hexdigest()[:16],
            "files": sum(1 for f in pkg_dir.rglob("*") if f.is_file())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()
    if args.clean and DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True, exist_ok=True)

    version = get_version()
    manifest = {"version": version, "source": "sorftime-seller-agent (repo root)",
                "built_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
                "packages": []}
    for key in PLATFORMS:
        info = build(key, version)
        manifest["packages"].append(info)
        print(f"✅ {info['pkg']:<20} v{version} · {info['tools']:>2} tools · "
              f"{info['files']:>3} files · {info['size_bytes']//1024} KB")

    # 源仓（全平台版）自身的指纹也入清单
    mpath = DIST / f"manifest-{version}.json"
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"📝 {mpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
