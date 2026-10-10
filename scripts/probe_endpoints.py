#!/usr/bin/env python3
"""Sorftime MCP 端点探活 + 工具清单 + 配额查询。

用法:
  python3 scripts/probe_endpoints.py            # 人读输出（全部 9 个端点 + 配额）
  python3 scripts/probe_endpoints.py --json     # JSON 输出（agent 用）
  python3 scripts/probe_endpoints.py --matrix   # 再生 references/tool-matrix.md（按端点分组）

行为:
  - 对 ROOT + 8 个平台端点各做一次完整 MCP 握手 (initialize → tools/list)
  - 根端点另调 get_time / amazon 端点另调 usage_query (credit_left)
  - Key 失效时服务端会返回伪工具 (NotAuthorization 系)——按名检出并明确提示
  - --matrix 时把全部端点的工具表 (名称/必填/参数) 写入 references/tool-matrix.md
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# 控制台输出编码健壮化（Windows GBK 终端/重定向流不中断）
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

_SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SKILL_ROOT / "scripts"))
from utils.env_config import load_env, get_key, get_mcp_url  # noqa: E402

load_env()

ENDPOINTS = {
    "root(全平台兼容)": "https://mcp.sorftime.com",
    "amazon": "https://mcp.sorftime.com/amazon",
    "walmart": "https://mcp.sorftime.com/walmart",
    "shopee": "https://mcp.sorftime.com/shopee",
    "tiktok": "https://mcp.sorftime.com/tiktok",
    "temu": "https://mcp.sorftime.com/temu",
    "1688": "https://mcp.sorftime.com/1688",
    "mercado": "https://mcp.sorftime.com/mercado",
    "social": "https://mcp.sorftime.com/social",
}

_KEY_NAME = "SORFTIME_MCP_KEY"


def _http():
    import urllib.request
    # 标准代理解析：遵循 http_proxy/https_proxy/no_proxy 环境变量，未设置则直连——
    # 与 bridge(httpx) 行为一致，适配需要代理出网的网络环境
    return urllib.request.build_opener()


def probe_endpoint(url, key):
    """完整握手 + tools/list。返回 (ok, tools, error)。"""
    import urllib.request, urllib.error
    opener = _http()

    def rpc(payload, sid=None, timeout=40):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "User-Agent": "sorftime-probe/4.0",
        }
        if sid:
            headers["Mcp-Session-Id"] = sid
        req = urllib.request.Request(url + "?key=" + key, data=json.dumps(payload).encode(),
                                     headers=headers, method="POST")
        resp = opener.open(req, timeout=timeout)
        sid_out = sid or resp.headers.get("mcp-session-id")
        raw = resp.read().decode("utf-8", errors="replace")
        datas = [ln[5:].strip() for ln in raw.splitlines() if ln.startswith("data:")]
        text = "\n".join(datas) or raw
        if not text.strip():
            return None, sid_out
        obj = None
        for cand in [t for t in text.split("\n") if t.strip().startswith("{")]:
            try:
                o = json.loads(cand)
                if "result" in o or "error" in o:
                    obj = o
            except Exception:
                pass
        if obj is None:
            obj = json.loads(text)
        return obj, sid_out

    try:
        init, sid = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                         "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                                    "clientInfo": {"name": "sorftime-probe", "version": "4.0"}}})
        if not init or "result" not in init:
            return False, [], f"initialize failed: {init}"
        rpc({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, sid)
        tl, _ = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}, sid)
        if not tl or "result" not in tl:
            return False, [], f"tools/list failed: {tl}"
        tools = tl["result"].get("tools", [])
        return True, tools, None
    except Exception as e:  # noqa: BLE001
        return False, [], f"{type(e).__name__}: {e}"


def call_tool(url, key, name, args):
    import urllib.request
    opener = _http()
    session = {"sid": None}

    def rpc(payload):
        headers = {"Content-Type": "application/json",
                   "Accept": "application/json, text/event-stream"}
        if session["sid"]:
            headers["Mcp-Session-Id"] = session["sid"]  # tools/call 需要会话态（无 sid 配额查询静默失败实测）
        resp = opener.open(urllib.request.Request(
            url + "?key=" + key, data=json.dumps(payload).encode(),
            headers=headers, method="POST"), timeout=60)
        if not session["sid"]:
            session["sid"] = resp.headers.get("mcp-session-id")
        raw = resp.read().decode("utf-8", errors="replace")
        datas = [ln[5:].strip() for ln in raw.splitlines() if ln.startswith("data:")]
        text = "\n".join(datas) or raw
        if not text.strip():
            return None
        for cand in [t for t in text.split("\n") if t.strip().startswith("{")]:
            try:
                o = json.loads(cand)
                if "result" in o or "error" in o:
                    return o
            except Exception:
                pass
        try:
            return json.loads(text)
        except Exception:
            return None  # 非 JSON 文本（服务端错误页等）——由调用方按 None 处理

    try:
        rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                        "clientInfo": {"name": "sorftime-probe", "version": "4.0"}}})
        rpc({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        res = rpc({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                   "params": {"name": name, "arguments": args}})
        if not res or "result" not in res:
            return None
        contents = res["result"].get("content", [])
        if not contents:
            return None
        text = contents[0].get("text", "")
        try:
            return json.loads(text)
        except Exception:
            return text
    except Exception:
        return None  # 配额查询失败不影响探活主流程


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--matrix", action="store_true", help="再生 references/tool-matrix.md")
    args = ap.parse_args()

    key = get_key()
    if not key:
        print(json.dumps({"error": f"{_KEY_NAME} not set"}) if args.json
              else f"❌ 未配置 {_KEY_NAME}（install.py --key 或写 ~/.sorftime/env）")
        return 1

    results = {}
    for name, url in ENDPOINTS.items():
        ok, tools, err = probe_endpoint(url, key)
        names = [t.get("name", "?") for t in tools]
        pseudo = [t for t in names if "notauthorization" in t.lower()]
        entry = {"ok": ok, "count": len(names), "tools": names}
        if ok:
            entry["_full"] = tools  # 仅供 --matrix 再生用，不进 JSON 输出
        if err:
            entry["error"] = err
        if pseudo:
            entry["pseudo_auth"] = pseudo
        results[name] = entry
        if not args.json:
            flag = " ⚠️KEY疑似失效(伪工具)" if pseudo else ""
            print(f"{'✅' if ok else '❌'} {name:<18} {url:<42} tools={len(names)}{flag}"
                  + (f" err={err}" if err else ""))

    # 配额工具动态探测：服务端当日曾把 usage_query 改名 common_usage_query 并铺满全端点，
    # 两个名字都认，以端点工具清单实际有的为准
    amz_names = results.get("amazon", {}).get("tools", [])
    quota_tool = next((t for t in ("common_usage_query", "usage_query") if t in amz_names), None)
    quota = call_tool(ENDPOINTS["amazon"], key, quota_tool, {}) if quota_tool else None
    credit = None
    if isinstance(quota, dict):
        credit = quota.get("data", {}).get("credit_left")
    # 端点解析可能被白名单镇流拦下——诊断工具结构化降级，不裸 traceback
    try:
        active_url = get_mcp_url()
    except RuntimeError as e:
        active_url = f"[blocked] {str(e)[:80]}"
    if not args.json:
        print(f"💰 配额余量 credit_left = {credit if credit is not None else '查询失败'}"
              f"（端点={active_url}）")

    if args.json:
        slim = {k: {kk: vv for kk, vv in v.items() if kk != "_full"} for k, v in results.items()}
        print(json.dumps({"quota_credit_left": credit, "active_mcp_url": active_url,
                          "endpoints": slim}, ensure_ascii=False, indent=1))

    if args.matrix:
        write_matrix(results)
    return 0


def write_matrix(results):
    matrix = _SKILL_ROOT / "references" / "tool-matrix.md"
    lines = [
        "# Sorftime MCP Tool Matrix（按平台端点分组）",
        "",
        f"> 由 `scripts/probe_endpoints.py --matrix` 从服务端再生。Sync time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
    ]
    for name, entry in results.items():
        url = ENDPOINTS[name]
        lines += [f"## {name} — {url}", ""]
        if not entry.get("ok"):
            lines += [f"探测失败：{entry.get('error', 'unknown')}", ""]
            continue
        if entry.get("pseudo_auth"):
            lines += ["⚠️ 返回伪工具（Key 疑似被轮换失效）——到 open.sorftime.com/mcp 重新复制 Key", ""]
            continue
        lines += [f"工具数：{entry['count']}", "", "| 工具 | 必填参数 |", "|---|---|"]
        for t in entry.get("_full", []):
            req = ", ".join(t.get("inputSchema", {}).get("required", [])) or "—"
            lines.append(f"| `{t.get('name', '?')}` | {req} |")
        lines.append("")
    matrix.write_text("\n".join(lines), encoding="utf-8")
    print(f"📝 tool-matrix.md 已再生: {matrix}")


if __name__ == "__main__":
    sys.exit(main())
