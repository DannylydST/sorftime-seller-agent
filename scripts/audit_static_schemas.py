#!/usr/bin/env python3
"""静态 schema 漂移审计：桥接静态表 vs 线上 tools/list 实时 schema。

退出码：0=无漂移（或仅警告级）；2=有参数级漂移（需人工/自动发版同步）。
用法：python scripts/audit_static_schemas.py [--endpoint URL]
每日保健任务消费：drift 即视同内部需求走发版流水线（同 tool-matrix 口径）。
2026-11-10 由 Kimi Code 报障催生（product_search 静态表滞留废弃参数 search_name 两月）。
"""
import ast
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from utils.env_config import load_env  # noqa: E402

load_env()

BRIDGE = os.path.join(os.path.dirname(__file__), "sorftime_bridge.py")


def static_schemas() -> dict:
    """从桥接源码 ast 提取静态工具表（不 import，无依赖）。"""
    tree = ast.parse(open(BRIDGE, encoding="utf-8").read())
    out = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        kv = {k.value: v for k, v in zip(node.keys, node.values)
              if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        if "name" in kv and any(k == "inputSchema" for k in kv):
            try:
                lit = ast.literal_eval(node)
                if isinstance(lit.get("inputSchema"), dict):
                    out[lit["name"]] = lit["inputSchema"]
            except Exception:
                pass
    return out


def live_schemas(endpoint: str) -> dict:
    key = os.environ.get("SORFTIME_MCP_KEY", "")
    def post(payload):
        req = urllib.request.Request(
            endpoint + ("?key=" + key if key else ""),
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json",
                     "Accept": "application/json, text/event-stream"}, method="POST")
        t = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
        for l in t.splitlines():
            if l.strip().startswith("data:"):
                return json.loads(l.split("data:", 1)[1].strip())
        return {}
    post({"jsonrpc": "2.0", "method": "notifications/initialized"})
    tools = post({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}) \
        .get("result", {}).get("tools", [])
    return {t["name"]: t.get("inputSchema", {}) for t in tools}


def main():
    endpoint = "https://mcp.sorftime.com/"
    if "--endpoint" in sys.argv:
        endpoint = sys.argv[sys.argv.index("--endpoint") + 1]

    st, lv = static_schemas(), live_schemas(endpoint)
    drift = []
    for name, live_schema in sorted(lv.items()):
        if name not in st:
            continue  # 新工具未入静态表由 tool-matrix 流程管
        sp = set(st[name].get("properties", {}))
        lp = set(live_schema.get("properties", {}))
        missing = lp - sp          # 线上有、静态无 → 静态过期
        stale = sp - lp            # 静态有、线上无 → 废弃参数滞留（危险：触发别名反向改写）
        if missing or stale:
            drift.append((name, sorted(stale), sorted(missing)))

    if drift:
        print("DRIFT 检出（静态表 vs 线上）：")
        for name, stale, missing in drift:
            if stale:
                print(f"  {name}: 滞留废弃参数 {stale}")
            if missing:
                print(f"  {name}: 缺新参数 {missing[:8]}{'…' if len(missing) > 8 else ''}")
        sys.exit(2)
    print(f"无漂移（静态表 {len(st)} 工具 vs 线上 {len(lv)} 工具，参数集一致）")


if __name__ == "__main__":
    main()
