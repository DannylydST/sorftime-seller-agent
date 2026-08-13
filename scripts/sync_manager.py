#!/usr/bin/env python3
"""
Sorftime MCP 全自动 Schema 同步管理器（方案 B）

职责：
  1. discover  — 从 Sorftime MCP 服务端拉取 tools/list
  2. diff      — 对比服务端 Schema vs 本地 Schema，识别新增/删除/变更
  3. generate  — 自动生成 bridge 代码、tool-matrix.md、测试 fixtures
  4. apply     — 将生成的内容写入技能目录（带备份）
  5. report    — 输出人类可读的变更报告

用法：
  python3 scripts/sync_manager.py discover          # 仅拉取并保存
  python3 scripts/sync_manager.py diff               # 对比并输出报告
  python3 scripts/sync_manager.py generate           # 生成所有产物（不写入）
  python3 scripts/sync_manager.py apply              # 应用更新（生成 + 写入 + 备份）
  python3 scripts/sync_manager.py full               # 完整流程：discover → diff → generate → apply
  python3 scripts/sync_manager.py rollback YYYYMMDD_HHMMSS  # 回滚到指定版本
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timedelta
from pathlib import Path

# 动态定位技能根目录
_SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SKILL_ROOT / "scripts"))

from utils.env_config import load_env
from utils.platform_utils import get_venv_python
import utils.schema_store as schema_store

load_env()

# ── 路径常量 ──
BRIDGE_PATH = _SKILL_ROOT / "scripts" / "sorftime_bridge.py"
MATRIX_PATH = _SKILL_ROOT / "references" / "tool-matrix.md"
FIXTURES_DIR = _SKILL_ROOT / "tests" / "fixtures"
BACKUP_DIR = _SKILL_ROOT / ".sync-backups"

SORFTIME_MCP_URL = os.getenv("SORFTIME_MCP_URL", "https://mcp.sorftime.com")
SORFTIME_MCP_KEY = os.getenv("SORFTIME_MCP_KEY", "")

# ── Tool Category Mapping (for tool-matrix.md grouping) ──
CATEGORY_MAP = {
    "product_": "Amazon Product",
    "keyword_": "Keyword",
    "category_": "Category",
    "tiktok_": "TikTok Shop",
    "ali1688_": "Other",
    "potential_": "Other",
    "get_time": "Other",
    "similar_product_": "Amazon Product",
    "competitor_": "Amazon Product",
    "search_categories_": "Category",
    "change_favorite_": "Keyword",
    "del_favorite_": "Keyword",
    "favorite_": "Keyword",
    "get_favorite_": "Keyword",
    "walmart_": "Walmart",
    "shopee_": "Shopee",
    "temu_": "TEMU",
}

# ── 平台专属真实 ID（fixture 默认值，避免假 ID 空跑）──
# 来源：2026-08-13 真实调用逐一验证（node_id 用 category_report 验证有 top100 数据）
_PLATFORM_NODE_IDS = {
    "walmart_": "5438",
    "tiktok_": "700650",
    "shopee_": "11001012",
    "temu_": "878",
    "default": "166350011",  # Amazon 及默认
}
_PLATFORM_PRODUCT_IDS = {
    "walmart_": "15689567602",
    "tiktok_": "1731637081990992476",
    "shopee_": "3536399570",
    "temu_": "606553130247338",
    "ali1688_": "671918122259",
    "default": "15689567602",
}
_PLATFORM_SHOP_IDS = {
    "shopee_": "13248331",          # Shopee shop_id 是数字 ID
    "temu_": "Zooye Family Cleaning",  # ⚠️ TEMU shop_id 实际接受店铺名（store_name）
}
# 站点默认值（按平台；Shopee 无 US 站，用 MY）
_PLATFORM_SITES = {
    "shopee_": "MY",
    "default": "US",
}
# TikTok author_id 实际接受作者 handle（用户名），非数字 ID
_AUTHOR_HANDLE = "xmw_us"
# 1688 反向图搜需要一个真实 web 图片 URL
_IMAGE_URL = "https://cbu01.alicdn.com/img/ibank/O1CN01TmjJpw1o1codZFhZH_!!951425165-0-cib.jpg"

# 服务端实际必填、但 schema 标注为可选的参数（缺了服务端会报错）
_SERVER_REQUIRED_OPTIONAL = {
    "walmart_product_trend_by_product_id": {"trend_type": "SalesVolume"},
    "shopee_keyword_relation_results": {"keyword": "yoga mat"},
    "shopee_category_trend": {"node_id": "11001012"},
}


def _platform_of(name: str) -> str:
    """按工具名前缀判断所属平台，返回平台 key（default 表示 Amazon 及通用）"""
    for p in ("walmart_", "tiktok_", "shopee_", "temu_", "ali1688_"):
        if name.startswith(p):
            return p
    return "default"


def _days_ago(n: int) -> str:
    """返回 n 天前的日期（yyyy-MM-dd），用于历史类工具的真实日期"""
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")

# 哪些工具是"核心"（需要在 bridge 中单独注册 schema，而非仅靠 raw_call）
# 规则：常用读工具单独注册；写操作、低频工具走 raw_call
CORE_TOOL_PATTERNS = [
    "get_time",
    "category_report",
    "product_search",
    "product_detail",
    "product_reviews",
    "product_variations",
    "product_traffic_terms",
    "keyword_detail",
    "keyword_search_results",
    "keyword_extends",
    "potential_product",
    "category_name_search",
    "category_search_from_top_node",
    "similar_product_feature",
    "competitor_product_keywords",
    "ali1688_similar_product",
    "tiktok_category_report",
    "tiktok_product_detail",
    "product_trend",
    "keyword_trend",
    "category_trend",
]


def _is_core_tool(name: str) -> bool:
    """Check whether a tool is a core tool (individually registered Schema)"""
    return name in CORE_TOOL_PATTERNS


# ═══════════════════════════════════════════════════════
#  1. DISCOVER — 从服务端拉取 tools/list
# ═══════════════════════════════════════════════════════

def discover() -> list[dict]:
    """向 Sorftime MCP 服务端请求 tools/list，返回工具列表"""
    if not SORFTIME_MCP_KEY:
        raise RuntimeError(
            "SORFTIME_MCP_KEY not set. Configure the environment variable or run install.py"
        )

    url = f"{SORFTIME_MCP_URL}?key={SORFTIME_MCP_KEY}"
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}

    import httpx

    async def _fetch():
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            resp = await client.post(
                url, json=payload, headers={"Content-Type": "application/json"}
            )
            resp.raise_for_status()
            raw_text = resp.text

            # SSE 解析
            data_json = None
            for line in raw_text.splitlines():
                line = line.strip()
                if line.startswith("data:"):
                    data_json = line[len("data:") :].strip()
                    break

            if not data_json:
                data_json = raw_text.strip()

            data = json.loads(data_json)
            return data["result"]["tools"]

    import asyncio

    tools = asyncio.run(_fetch())
    return tools


# ═══════════════════════════════════════════════════════
#  2. DIFF — 对比服务端 vs 本地
# ═══════════════════════════════════════════════════════

def diff(server_tools: list[dict]) -> dict:
    """
    对比服务端 Schema 与本地保存的 Schema
    返回变更报告
    """
    local_tools = schema_store.load_latest()

    server_map = {t["name"]: t for t in server_tools if "name" in t}
    local_map = {t["name"]: t for t in local_tools if "name" in t}

    server_names = set(server_map.keys())
    local_names = set(local_map.keys())

    added = sorted(server_names - local_names)
    removed = sorted(local_names - server_names)

    # Schema 变更检测（名称相同但 description 或 inputSchema 不同）
    changed = []
    for name in sorted(server_names & local_names):
        s_schema = server_map[name]
        l_schema = local_map[name]
        diffs = []

        if s_schema.get("description") != l_schema.get("description"):
            diffs.append("description")

        s_props = set(
            s_schema.get("inputSchema", {}).get("properties", {}).keys()
        )
        l_props = set(
            l_schema.get("inputSchema", {}).get("properties", {}).keys()
        )
        if s_props != l_props:
            added_props = s_props - l_props
            removed_props = l_props - s_props
            diff_str = ""
            if added_props:
                diff_str += f"+{','.join(added_props)}"
            if removed_props:
                diff_str += f"-{','.join(removed_props)}"
            diffs.append(f"inputSchema({diff_str})")

        if diffs:
            changed.append({"name": name, "changes": diffs})

    return {
        "server_count": len(server_names),
        "local_count": len(local_names),
        "added": added,
        "removed": removed,
        "changed": changed,
        "has_changes": bool(added or removed or changed),
    }


# ═══════════════════════════════════════════════════════
#  3. GENERATE — 自动生成产物
# ═══════════════════════════════════════════════════════

def _json_to_python_literals(text: str) -> str:
    """安全地将 JSON 中的 true/false/null 转换为 Python 的 True/False/None
    通过跳过 JSON 字符串内的内容来避免误替换"""
    result = []
    i = 0
    while i < len(text):
        if text[i] == '"':
            # 找到字符串结束（考虑转义）
            j = i + 1
            while j < len(text):
                if text[j] == "\\" and j + 1 < len(text):
                    j += 2
                elif text[j] == '"':
                    break
                else:
                    j += 1
            result.append(text[i:j + 1])
            i = j + 1
        else:
            # 尝试匹配 JSON 字面量
            for json_lit, py_lit in [("true", "True"), ("false", "False"), ("null", "None")]:
                if text[i:i + len(json_lit)] == json_lit:
                    # 检查前后是否是分隔符（确保不是单词的一部分）
                    before_ok = i == 0 or text[i - 1] in " \t\n\r:,[{]}"
                    after_ok = i + len(json_lit) >= len(text) or text[i + len(json_lit)] in " \t\n\r,}]}"
                    if before_ok and after_ok:
                        result.append(py_lit)
                        i += len(json_lit)
                        break
            else:
                result.append(text[i])
                i += 1
    return "".join(result)


def _indent(text: str, spaces: int = 4) -> str:
    """为每一行添加缩进"""
    prefix = " " * spaces
    return "\n".join(prefix + line for line in text.splitlines())


def generate_core_tools(tools: list[dict]) -> str:
    """
    从服务端 Schema 生成 sorftime_bridge.py 的 CORE_TOOLS Python 代码片段
    """
    lines = ["_FALLBACK_CORE_TOOLS = ["]

    for tool in sorted(tools, key=lambda t: t.get("name", "")):
        name = tool.get("name", "")
        desc = tool.get("description", "")
        schema = tool.get("inputSchema", {"type": "object", "properties": {}, "required": []})

        # 核心工具单独注册，其他标记为 raw 但保留基本信息
        is_core = _is_core_tool(name)

        # 转义三引号
        safe_desc = desc.replace('"""', '"""').replace("\\", "\\\\")

        schema_json = json.dumps(schema, ensure_ascii=False, indent=4)
        # 将 JSON 字面量转换为 Python 字面量（true→True, false→False, null→None）
        # 注意：只替换不在字符串内的值，通过引号状态跟踪实现
        schema_json = _json_to_python_literals(schema_json)

        # 缩进 Schema JSON
        schema_lines = schema_json.splitlines()
        formatted_schema = "\n".join(
            "        " + line if i > 0 else line for i, line in enumerate(schema_lines)
        )

        if is_core:
            entry = f'''    {{
        "name": "{name}",
        "description": """{safe_desc}""",
        "inputSchema": {formatted_schema},
    }},'''
        else:
            # 非核心工具：简化描述，提示通过 sorftime_raw_call 使用
            entry = f'''    {{
        "name": "{name}",
        "description": """{safe_desc} (可通过 sorftime_raw_call 透传调用)""",
        "inputSchema": {formatted_schema},
    }},'''

        lines.append(entry)

    # 追加本地代理工具（不在服务端 Schema 中，由 bridge 本地处理）
    lines.append('''    {
        "name": "sorftime_raw_call",
        "description": """透传调用任意 Sorftime MCP 工具（用于访问未在 bridge 中单独注册 Schema 的工具）""",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "要调用的 Sorftime 工具名称"},
                "arguments": {"type": "object", "description": "工具参数（JSON 对象）"}
            },
            "required": ["tool_name", "arguments"]
        },
    },''')

    lines.append("]")
    return "\n".join(lines)


def generate_matrix(tools: list[dict]) -> str:
    """生成 tool-matrix.md"""

    def _categorize(name: str) -> str:
        for prefix, cat in sorted(CATEGORY_MAP.items(), key=lambda x: -len(x[0])):
            if name.startswith(prefix) or name == prefix:
                return cat
        return "Other"

    # 按分类分组
    groups: dict[str, list[dict]] = {}
    for tool in tools:
        cat = _categorize(tool.get("name", ""))
        groups.setdefault(cat, []).append(tool)

    lines = [
        "# Sorftime MCP Tool Matrix",
        "",
        "> Auto-generated. This file is auto-generated by `scripts/sync_manager.py`. Do not edit manually.",
        f"> Sync time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"> Total tools: {len(tools)}",
        "",
        "## Legend",
        "",
        "| Marker | Meaning |",
        "|------|------|",
        "| ✅ | Core tool (Schema registered in bridge) |",
        "| ⚠️ | Supported tool (accessible via `sorftime_raw_call` passthrough) |",
        "",
    ]

    for cat in ["Amazon Product", "Keyword", "Category", "TikTok Shop", "Walmart", "Shopee", "TEMU", "Other"]:
        if cat not in groups:
            continue
        lines.append(f"## {cat} ({len(groups[cat])})")
        lines.append("")
        lines.append("| 工具名 | 状态 | 说明 |")
        lines.append("|--------|------|------|")

        for tool in sorted(groups[cat], key=lambda t: t.get("name", "")):
            name = tool.get("name", "")
            desc = tool.get("description", "")[:60]
            status = "✅ Registered" if _is_core_tool(name) else "⚠️ raw"
            lines.append(f"| `{name}` | {status} | {desc} |")

        lines.append("")

    lines.append("## Universal Call Method")
    lines.append("")
    lines.append("To call ⚠️ raw tools, use `sorftime_raw_call`:")
    lines.append("")
    lines.append('```json')
    lines.append('{')
    lines.append('  "tool_name": "product_trend",')
    lines.append('  "arguments": {')
    lines.append('    "amz_site": "US",')
    lines.append('    "asin": "B0DPQ772T9"')
    lines.append('  }')
    lines.append('}')
    lines.append('```')
    lines.append("")

    return "\n".join(lines)


def generate_fixture(tool: dict) -> dict:
    """从工具 Schema 生成测试 fixture（YAML 格式数据结构）"""
    name = tool.get("name", "")
    schema = tool.get("inputSchema", {})
    props = schema.get("properties", {})
    required = schema.get("required", [])

    # 构建示例参数（平台专属真实 ID，避免假 ID 空跑）
    args: dict[str, Any] = {}
    plat = _platform_of(name)
    for pname, pdef in props.items():
        if pname in required:
            ptype = pdef.get("type", "string")
            enum = pdef.get("enum", [])

            if enum:
                # 跳过 "Unknow" 默认值，选有意义的
                meaningful = [e for e in enum if e and str(e).lower() not in ("unknow", "unknown", "")]
                args[pname] = meaningful[0] if meaningful else enum[0]
            elif pname in ("amz_site", "amzSite", "site"):
                args[pname] = "US"
            elif pname == "keyword":
                args[pname] = "yoga mat"
            elif pname == "search_name":
                args[pname] = "kitchen storage"
            elif pname == "asin":
                args[pname] = "B07H9PZDQW"
            elif pname == "node_id":
                args[pname] = _PLATFORM_NODE_IDS.get(plat, _PLATFORM_NODE_IDS["default"])
            elif pname == "product_id":
                args[pname] = _PLATFORM_PRODUCT_IDS.get(plat, _PLATFORM_PRODUCT_IDS["default"])
            elif pname == "shop_id":
                args[pname] = _PLATFORM_SHOP_IDS.get(plat, "123456789")
            elif pname == "author_id":
                args[pname] = _AUTHOR_HANDLE
            elif pname == "image_url":
                args[pname] = _IMAGE_URL
            elif pname == "product_name":
                args[pname] = "yoga mat"
            elif pname == "name":
                args[pname] = "yoga mat"
            elif pname == "category_name":
                args[pname] = "kitchen"
            elif pname in ("top_node", "topNode"):
                args[pname] = "370783011"
            elif pname == "page":
                args[pname] = 1
            elif pname in ("start_date", "begin_date"):
                args[pname] = _days_ago(40)
            elif pname in ("end_date", "query_date", "search_time", "date"):
                args[pname] = _days_ago(3)
            elif ptype == "integer":
                args[pname] = 1
            elif ptype == "number":
                args[pname] = 10.0
            elif ptype == "boolean":
                args[pname] = True
            else:
                args[pname] = "test"

    # 服务端实际必填但 schema 标注可选的参数，补齐（否则服务端报错）
    for extra_k, extra_v in _SERVER_REQUIRED_OPTIONAL.get(name, {}).items():
        args.setdefault(extra_k, extra_v)

    # 站点类参数：schema 常标注为可选，但服务端实际必填（缺了返回 "Please specify the site"）
    for site_param in ("amz_site", "site", "keyword_support_site"):
        if site_param in props and site_param not in args:
            args[site_param] = _PLATFORM_SITES.get(plat, "US")

    return {
        "tool": name,
        "name": f"{name} — {tool.get('description', '')[:30]}",
        "arguments": args,
    }


# ═══════════════════════════════════════════════════════
#  4. APPLY — 应用更新（带备份）
# ═══════════════════════════════════════════════════════

def _backup_file(path: Path) -> Path:
    """备份文件到 .sync-backups"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"{path.name}.{timestamp}.bak"
    shutil.copy2(path, backup)
    return backup


def apply_bridge_update(core_tools_code: str) -> None:
    """将新生成的 _FALLBACK_CORE_TOOLS 代码写入 sorftime_bridge.py"""
    backup = _backup_file(BRIDGE_PATH)

    lines = BRIDGE_PATH.read_text(encoding="utf-8").splitlines()

    # 找到 _FALLBACK_CORE_TOOLS = [ 的起始行
    start_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^\s*_FALLBACK_CORE_TOOLS\s*=\s*\[", line):
            start_idx = i
            break

    if start_idx is None:
        raise RuntimeError(f"无法在 {BRIDGE_PATH} 中找到 _FALLBACK_CORE_TOOLS 定义")

    # 从起始行开始，计算括号深度，找到匹配的 ]
    depth = 0
    end_idx = None
    for i in range(start_idx, len(lines)):
        for ch in lines[i]:
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break
        if end_idx is not None:
            break

    if end_idx is None:
        raise RuntimeError(f"无法找到 _FALLBACK_CORE_TOOLS 定义的结束位置")

    # 替换：保留前后代码，中间插入新生成的代码
    new_lines = lines[:start_idx] + core_tools_code.splitlines() + lines[end_idx + 1:]
    BRIDGE_PATH.write_text("\n".join(new_lines), encoding="utf-8")

    print(f"  ✅ bridge 已更新 (备份: {backup.name})")


def apply_matrix_update(matrix_md: str) -> None:
    """写入 tool-matrix.md"""
    backup = _backup_file(MATRIX_PATH)
    MATRIX_PATH.write_text(matrix_md, encoding="utf-8")
    print(f"  ✅ tool-matrix.md 已更新 (备份: {backup.name})")


def apply_fixtures_update(tools: list[dict]) -> None:
    """生成/更新测试 fixtures"""
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    updated = 0
    created = 0
    for tool in tools:
        name = tool.get("name", "")
        fixture_path = FIXTURES_DIR / f"{name}.yaml"
        fixture = generate_fixture(tool)

        import yaml

        if fixture_path.exists():
            # 已有 fixture：保留用户可能自定义的内容，只更新结构和已知参数
            with open(fixture_path, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}

            # 智能合并：保留 name，更新 arguments 结构
            merged = {
                "tool": name,
                "name": existing.get("name", fixture["name"]),
                "arguments": fixture["arguments"],
            }
            # 保留额外字段（如 skip、notes）
            for k in existing:
                if k not in merged:
                    merged[k] = existing[k]

            fixture = merged
            updated += 1
        else:
            created += 1

        with open(fixture_path, "w", encoding="utf-8") as f:
            yaml.dump(fixture, f, allow_unicode=True, sort_keys=False)

    print(f"  ✅ fixtures: {created} 新建, {updated} 更新")


def apply_all(tools: list[dict], diff_report: dict) -> None:
    """执行完整的应用更新"""
    print("\n📝 应用更新...")

    core_tools_code = generate_core_tools(tools)
    apply_bridge_update(core_tools_code)

    matrix_md = generate_matrix(tools)
    apply_matrix_update(matrix_md)

    apply_fixtures_update(tools)

    # 保存服务端 Schema
    vpath = schema_store.save(tools)
    print(f"  ✅ Schema 已保存: {vpath.name}")

    # 生成变更摘要
    summary_path = BACKUP_DIR / f"sync-summary-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(diff_report, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 变更摘要: {summary_path.name}")


# ═══════════════════════════════════════════════════════
#  5. REPORT — 人类可读报告
# ═══════════════════════════════════════════════════════

def print_report(diff_report: dict) -> None:
    """打印变更报告"""
    print("\n" + "=" * 60)
    print(" Sorftime MCP Schema 变更报告")
    print("=" * 60)
    print(f"服务端工具数: {diff_report['server_count']}")
    print(f"本地缓存工具数: {diff_report['local_count']}")
    print()

    if diff_report["added"]:
        print(f"🟢 新增工具 ({len(diff_report['added'])}):")
        for name in diff_report["added"]:
            print(f"   + {name}")
        print()

    if diff_report["removed"]:
        print(f"🔴 删除工具 ({len(diff_report['removed'])}):")
        for name in diff_report["removed"]:
            print(f"   - {name}")
        print()

    if diff_report["changed"]:
        print(f"🟡 Schema 变更 ({len(diff_report['changed'])}):")
        for item in diff_report["changed"]:
            print(f"   ~ {item['name']}: {', '.join(item['changes'])}")
        print()

    if not diff_report["has_changes"]:
        print("✅ 无变更，服务端与本地 Schema 一致")
    else:
        print(f"📊 总计: +{len(diff_report['added'])}/-{len(diff_report['removed'])}/~{len(diff_report['changed'])}")

    print("=" * 60)


# ═══════════════════════════════════════════════════════
#  CLI 入口
# ═══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Sorftime MCP 全自动 Schema 同步管理器")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("discover", help="从服务端拉取 tools/list 并保存")
    sub.add_parser("diff", help="对比服务端 vs 本地 Schema")
    sub.add_parser("generate", help="生成产物但不写入（预览模式）")
    sub.add_parser("apply", help="应用更新（生成 + 写入 + 备份）")
    sub.add_parser("full", help="完整流程: discover → diff → generate → apply")

    rollback_parser = sub.add_parser("rollback", help="回滚到指定版本")
    rollback_parser.add_argument("timestamp", help="版本时间戳，如 20250423_120000")

    args = parser.parse_args()

    if args.command == "discover":
        print("🔍 从 Sorftime MCP 服务端拉取工具列表...")
        tools = discover()
        vpath = schema_store.save(tools)
        print(f"✅ 发现 {len(tools)} 个工具，已保存到 {vpath}")

    elif args.command == "diff":
        # 如果没有本地缓存，先拉取
        if not schema_store.load_latest():
            print("🔍 本地无缓存，先拉取服务端...")
            server_tools = discover()
            schema_store.save(server_tools)
        else:
            server_tools = discover()

        report = diff(server_tools)
        print_report(report)

    elif args.command == "generate":
        if not schema_store.load_latest():
            print("🔍 本地无缓存，先拉取服务端...")
            server_tools = discover()
            schema_store.save(server_tools)
        else:
            server_tools = schema_store.load_latest()

        print("📝 生成产物（预览模式，不写入文件）...")
        core_code = generate_core_tools(server_tools)
        print(f"\n--- CORE_TOOLS 代码 ({len(core_code)} 字符) ---")
        print(core_code[:500] + "...")

        matrix_md = generate_matrix(server_tools)
        print(f"\n--- tool-matrix.md ({len(matrix_md)} 字符) ---")
        print(matrix_md[:500] + "...")

        print(f"\n--- fixtures 预览 ---")
        for tool in server_tools[:3]:
            fixture = generate_fixture(tool)
            print(f"  {tool['name']}: {fixture['arguments']}")

    elif args.command == "apply":
        if not schema_store.load_latest():
            print("🔍 本地无缓存，先拉取服务端...")
            server_tools = discover()
            schema_store.save(server_tools)
        else:
            server_tools = schema_store.load_latest()

        report = diff(server_tools)
        print_report(report)

        if report["has_changes"]:
            apply_all(server_tools, report)
        else:
            print("\n✅ 无变更，无需应用")

    elif args.command == "full":
        print("🚀 启动完整同步流程...")
        print("\n━━━ 1/4 DISCOVER ━━━")
        server_tools = discover()
        print(f"✅ 发现 {len(server_tools)} 个工具")

        print("\n━━━ 2/4 DIFF ━━━")
        report = diff(server_tools)
        print_report(report)

        if not report["has_changes"]:
            print("\n✅ 无变更，流程结束")
            return

        print("\n━━━ 3/4 GENERATE ━━━")
        core_code = generate_core_tools(server_tools)
        matrix_md = generate_matrix(server_tools)
        print(f"✅ CORE_TOOLS: {len(core_code)} 字符")
        print(f"✅ tool-matrix.md: {len(matrix_md)} 字符")
        print(f"✅ fixtures: {len(server_tools)} 个")

        print("\n━━━ 4/4 APPLY ━━━")
        apply_all(server_tools, report)

        print("\n🎉 同步完成！")
        print(f"   备份目录: {BACKUP_DIR}")
        print(f"   Schema 存储: {schema_store.SCHEMA_DIR}")

    elif args.command == "rollback":
        schema_store.rollback_to(args.timestamp)
        print(f"✅ 已回滚到版本 {args.timestamp}")
        print(f"   最新 Schema: {schema_store.LATEST_FILE}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
