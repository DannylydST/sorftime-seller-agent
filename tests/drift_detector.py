#!/usr/bin/env python3
"""
Sorftime MCP 工具漂移检测器
对比 tool-matrix.md 与 sorftime_bridge.py 中的 CORE_TOOLS，输出差异报告
"""

import json
import re
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
MATRIX_PATH = _SKILL_ROOT / "references" / "tool-matrix.md"
BRIDGE_PATH = _SKILL_ROOT / "scripts" / "sorftime_bridge.py"
REPORT_PATH = Path(__file__).parent / "drift-report.json"


def parse_tool_matrix() -> tuple[set[str], set[str]]:
    """解析 tool-matrix.md，返回 (registered_tools, raw_tools)"""
    registered = set()
    raw = set()
    text = MATRIX_PATH.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("|") and "`" in line:
            # 提取工具名，如 `product_detail`
            match = re.search(r'`([^`]+)`', line)
            if match:
                tool = match.group(1)
                if "✅" in line:
                    registered.add(tool)
                elif "⚠️" in line or "raw" in line.lower():
                    raw.add(tool)
    return registered, raw


def parse_bridge_tools() -> set[str]:
    """解析 sorftime_bridge.py，提取所有注册的工具名"""
    text = BRIDGE_PATH.read_text(encoding="utf-8")
    # 方法1：优先从 schema_store 加载（如果已同步）
    try:
        sys.path.insert(0, str(_SKILL_ROOT / "scripts"))
        from utils.schema_store import load_latest
        tools = load_latest()
        if tools:
            names = {t["name"] for t in tools if "name" in t}
            # 追加本地代理工具（不在服务端 Schema 中）
            names.add("sorftime_raw_call")
            return names
    except Exception:
        pass

    # 方法2：直接搜索文件中所有的 "name": "xxx" 来提取工具名
    tools = set()
    for match in re.finditer(r'"name"\s*:\s*"([^"]+)"', text):
        name = match.group(1)
        # 过滤掉非工具名的键（如 jsonrpc、method 等）
        if name not in ("tools/list", "tools/call", "message", "text", "object"):
            tools.add(name)
    return tools


def main():
    if not MATRIX_PATH.exists():
        print(f"❌ 找不到 {MATRIX_PATH}")
        sys.exit(1)
    if not BRIDGE_PATH.exists():
        print(f"❌ 找不到 {BRIDGE_PATH}")
        sys.exit(1)

    matrix_registered, matrix_raw = parse_tool_matrix()
    bridge_tools = parse_bridge_tools()

    all_matrix = matrix_registered | matrix_raw

    missing_in_bridge = all_matrix - bridge_tools
    missing_in_matrix = bridge_tools - all_matrix

    report = {
        "matrix_total": len(all_matrix),
        "bridge_total": len(bridge_tools),
        "missing_in_bridge": sorted(missing_in_bridge),
        "missing_in_matrix": sorted(missing_in_matrix),
        "drift_detected": bool(missing_in_bridge or missing_in_matrix),
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("=" * 50)
    print("Sorftime MCP 工具漂移检测报告")
    print("=" * 50)
    print(f"tool-matrix.md 总计: {len(all_matrix)} 个工具")
    print(f"sorftime_bridge.py CORE_TOOLS: {len(bridge_tools)} 个工具")
    print()

    if missing_in_bridge:
        print(f"⚠️  tool-matrix.md 中有但 bridge 中缺失 ({len(missing_in_bridge)} 个):")
        for t in sorted(missing_in_bridge):
            print(f"   - {t}")
    else:
        print("✅ bridge 中未缺失 tool-matrix.md 的工具")

    print()

    if missing_in_matrix:
        print(f"⚠️  bridge 中有但 tool-matrix.md 中缺失 ({len(missing_in_matrix)} 个):")
        for t in sorted(missing_in_matrix):
            print(f"   - {t}")
    else:
        print("✅ tool-matrix.md 中未缺失 bridge 的工具")

    print()
    print(f"报告已保存: {REPORT_PATH}")
    print(f"漂移状态: {'❌ 发现漂移' if report['drift_detected'] else '✅ 无漂移'}")

    sys.exit(1 if report["drift_detected"] else 0)


if __name__ == "__main__":
    main()
