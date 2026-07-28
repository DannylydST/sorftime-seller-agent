#!/usr/bin/env python3
"""
TikTok Category Discovery + Auto-Persistence
Usage:
  python3 scripts/discover_tiktok.py <keyword>          # search & persist
  python3 scripts/discover_tiktok.py --list             # list known categories
  python3 scripts/discover_tiktok.py --report <name>    # search, persist, then get report
"""
import json, os, sys, subprocess
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parent.parent
REF_FILE = SKILL_DIR / "references" / "tiktok-categories.json"
BRIDGE = str(SKILL_DIR / "scripts" / "sorftime_bridge.py")
VENV_PYTHON = str(SKILL_DIR / ".venv" / "bin" / "python3")

if not Path(VENV_PYTHON).exists():
    VENV_PYTHON = sys.executable

KEY = os.getenv("SORFTIME_MCP_KEY", "")


def _call(tool, args):
    """Call bridge CLI and return parsed JSON"""
    cmd = [VENV_PYTHON, BRIDGE, "--one-shot", tool, json.dumps(args)]
    env = os.environ.copy()
    if KEY:
        env["SORFTIME_MCP_KEY"] = KEY
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(SKILL_DIR))
    stdout = r.stdout.strip()
    stderr = r.stderr.strip()
    if not stdout:
        return {"error": True, "message": stderr or "empty response"}
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"error": True, "message": stdout[:200]}


def load_ref():
    if REF_FILE.exists():
        with open(REF_FILE) as f:
            return json.load(f)
    return {"updated": "", "site": "US", "total": 0, "categories": []}


def save_ref(ref):
    ref["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    ref["total"] = len(ref["categories"])
    with open(REF_FILE, "w") as f:
        json.dump(ref, f, indent=2, ensure_ascii=False)


def discover(keyword):
    """Search for categories matching keyword, persist new ones, return all matches"""
    result = _call("tiktok_category_search_from_name", {"name": keyword, "site": "US"})
    data = result.get("data", result)
    if not isinstance(data, list) or not data:
        # Try alternate tool
        result = _call("tiktok_category_name_search", {"search_name": keyword, "site": "US"})
        data = result.get("data", result)

    if not isinstance(data, list) or not data:
        print(f"No categories found for '{keyword}'")
        return []

    ref = load_ref()
    existing_ids = {c["node_id"] for c in ref["categories"]}
    new_ids = set()

    matches = []
    for item in data:
        nid = str(item.get("node_id", ""))
        name = item.get("category_name", "")
        if nid and name:
            matches.append({"node_id": nid, "name": name})
            if nid not in existing_ids:
                ref["categories"].append({"node_id": nid, "name": name})
                existing_ids.add(nid)
                new_ids.add(nid)

    if new_ids:
        ref["categories"].sort(key=lambda c: int(c["node_id"]) if c["node_id"].isdigit() else 999999)
        save_ref(ref)
        print(f"Discovered {len(matches)} categories ({len(new_ids)} new) for '{keyword}'")
    else:
        print(f"Found {len(matches)} categories for '{keyword}' (all already known)")

    for m in matches:
        tag = " [NEW]" if m["node_id"] in new_ids else ""
        print(f"  {m['node_id']}: {m['name']}{tag}")

    return matches


def list_known():
    ref = load_ref()
    print(f"Known TikTok categories: {ref['total']} (updated {ref['updated']})")
    print()
    for c in ref["categories"]:
        print(f"  {c['node_id']}: {c['name']}")


def get_report(name_or_id):
    """Get category report — accepts name keyword or node_id directly"""
    ref = load_ref()

    node_id = None
    # Check if it's a direct node_id match
    for c in ref["categories"]:
        if c["node_id"] == name_or_id:
            node_id = name_or_id
            break

    # Otherwise search by name
    if not node_id:
        # Check known categories first
        for c in ref["categories"]:
            if name_or_id.lower() in c["name"].lower():
                node_id = c["node_id"]
                break

    # If not found, discover first
    if not node_id:
        matches = discover(name_or_id)
        if matches:
            node_id = matches[0]["node_id"]

    if not node_id:
        print(f"No category found for '{name_or_id}'")
        sys.exit(1)

    result = _call("tiktok_category_report", {"node_id": node_id, "site": "US"})
    data = result.get("data", result)
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "--list":
        list_known()
    elif cmd == "--report":
        if len(sys.argv) < 3:
            print("Usage: discover_tiktok.py --report <category_name_or_node_id>")
            sys.exit(1)
        get_report(sys.argv[2])
    else:
        discover(cmd)
