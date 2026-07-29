#!/usr/bin/env python3
"""
TikTok Category Discovery + Auto-Persistence
Usage:
  python3 scripts/discover_tiktok.py <keyword>          # search & persist
  python3 scripts/discover_tiktok.py --list             # list known categories
  python3 scripts/discover_tiktok.py --report <name>    # search, persist, then get report
  python3 scripts/discover_tiktok.py --sweep            # batch scan with parallel probes
  python3 scripts/discover_tiktok.py --sweep --parallel 16
"""
import json, os, sys, subprocess, itertools
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

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


# ── sweep probe keywords ────────────────────────────────────────────
# ponytail: inline list; split into a probes.txt when >200 entries.
PROBES = [
    "makeup","skincare","moisturizer","lipstick","hair","shampoo","fragrance","perfume","nail","lash",
    "supplement","vitamin","protein","collagen","probiotic",
    "snack","candy","coffee","tea","drink","sauce",
    "kitchen","storage","cleaning","bedding","towel","lamp","decor","candle","pillow","blanket",
    "phone case","headphone","charger","cable","speaker","smartwatch","camera","computer",
    "dress","shirt","pants","jeans","hoodie","leggings","sweater","jacket","underwear","sock",
    "sneaker","boots","sandal","heel","backpack","handbag","wallet",
    "necklace","ring","earring","bracelet","watch","sunglasses","hat",
    "fitness","yoga","camping","fishing","bike","gym","sport",
    "toy","game","puzzle","doll","lego","plush",
    "dog","cat","pet",
    "baby","diaper","kids",
    "car","motorcycle","tool","drill","garden","plant","seed",
    "craft","sewing","yarn","book","pen","notebook","office","art",
]


def _search_one(term):
    """Run both search tools for one probe term, return unique (node_id, name) pairs."""
    results = {}
    for tool, param in [("tiktok_category_search_from_name", "name"),
                        ("tiktok_category_name_search", "search_name")]:
        try:
            res = _call(tool, {param: term, "site": "US"})
            for item in res.get("data", []) if isinstance(res, dict) else []:
                nid = str(item.get("node_id", ""))
                name = (item.get("category_name") or "").strip()
                if nid and name:
                    results[nid] = name
        except Exception:
            pass
    return results


def sweep(parallel=8):
    """Batch scan all probe keywords in parallel, persist unique categories."""
    all_found = {}
    failed = 0

    with ThreadPoolExecutor(max_workers=min(parallel, 16)) as ex:
        futures = {ex.submit(_search_one, t): t for t in PROBES}
        for i, fut in enumerate(as_completed(futures)):
            term = futures[fut]
            try:
                found = fut.result()
                for nid, name in found.items():
                    if nid not in all_found:
                        all_found[nid] = name
            except Exception:
                failed += 1
            if (i + 1) % 20 == 0:
                print(f"  ...{i+1}/{len(PROBES)} probes, {len(all_found)} unique so far", flush=True)

    # Persist
    ref = load_ref()
    existing_ids = {c["node_id"] for c in ref["categories"]}
    new_count = 0
    for nid, name in all_found.items():
        if nid not in existing_ids:
            ref["categories"].append({"node_id": nid, "name": name})
            existing_ids.add(nid)
            new_count += 1

    ref["categories"].sort(key=lambda c: int(c["node_id"]) if c["node_id"].isdigit() else 999999)
    save_ref(ref)

    print(f"Sweep done: {len(PROBES)} probes → {len(all_found)} unique categories "
          f"({new_count} new, {failed} probe failures)")
    print(f"Total known: {ref['total']} categories (saved to {REF_FILE})")


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
    elif cmd == "--sweep":
        parallel = 8
        for i, a in enumerate(sys.argv[2:]):
            if a == "--parallel" and i + 1 < len(sys.argv) - 1:
                parallel = min(int(sys.argv[i + 3]), 16)
            elif a.startswith("--parallel="):
                parallel = min(int(a.split("=")[1]), 16)
        print(f"Sweeping with {parallel} workers across {len(PROBES)} probe keywords...")
        sweep(parallel=parallel)
    elif cmd == "--report":
        if len(sys.argv) < 3:
            print("Usage: discover_tiktok.py --report <category_name_or_node_id>")
            sys.exit(1)
        get_report(sys.argv[2])
    else:
        discover(cmd)
