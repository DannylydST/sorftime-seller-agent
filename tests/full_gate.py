#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full release gate for the seller-agent skill (any branch).

Four layers, one command:
  L1 static integrity   — tool-name references vs matrix; file-path references exist; retired tools not called
  L2 version matrix     — py_compile every script under Python 3.10/3.11/3.12 (skips missing interpreters)
  L3 tool regression    — run every READ-ONLY fixture through the bridge (write-type tools excluded by name)
  L4 clean-room e2e     — pack blacklist zip -> extract to temp -> install.py --skip-test (no key) -> healthcheck reaches "Key not configured"

Exit 0 = all gates green. Any FAIL = exit 1 with a report.

Usage:
  SORFTIME_MCP_KEY=... python tests/full_gate.py            # full (L3 uses the key)
  python tests/full_gate.py --skip-live                     # L1+L2+L4 only (no key, no requests)
"""
import argparse, json, os, py_compile, re, shutil, subprocess, sys, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
FIXTURES = ROOT / "tests" / "fixtures"
MATRIX = ROOT / "references" / "tool-matrix.md"

RETIRED = {"tiktok_category_name_search"}
WRITE_PATTERNS = ("favorite", "subscription", "del_", "change_", "delete", "batch_task", "task_update")

def matrix_tools():
    return set(re.findall(r"\|\s*`([a-z0-9_]+)`\s*\|", MATRIX.read_text(encoding="utf-8")))

# ---------- L1 static ----------
def gate_static():
    fails = []
    tools = matrix_tools()
    # 1. called tool names must exist (call sites: _call(".."), --one-shot "..", tool_name="..", "name": ".." in routers)
    call_pat = re.compile(r"""(?:_call\(|--one-shot\s+|tool_name\s*=\s*|tool_name"?\s*:\s*)["']([a-z0-9_]{4,50})["']""")
    for py in list((ROOT / "scripts").rglob("*.py")) + list((ROOT / "tests").glob("*.py")):
        text = py.read_text(encoding="utf-8", errors="replace")
        for m in call_pat.finditer(text):
            name = m.group(1)
            if name in RETIRED:
                fails.append(f"L1 retired tool called: {name} in {py.relative_to(ROOT)}")
            elif name not in tools and not name.startswith(("shopee_keyword_search",)):
                # tolerate non-tool python identifiers heuristics: only flag known-prefix names
                if name.split("_")[0] in ("category", "product", "keyword", "tiktok", "walmart", "shopee", "temu", "ali1688", "reddit", "get", "sorftime", "similar"):
                    fails.append(f"L1 unknown tool called: {name} in {py.relative_to(ROOT)}")
    # 2. file references in docs must exist
    for md in [ROOT / "SKILL.md", ROOT / "README.md"] + list((ROOT / "references").glob("*.md")):
        text = md.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"`((?:scripts|references|config|tests|assets)/[\w./-]+\.\w+)`", text):
            rel = m.group(1)
            if not (ROOT / rel).exists():
                fails.append(f"L1 doc references missing file: {rel} in {md.relative_to(ROOT)}")
    # 3. fixtures must all reference live tools
    for fx in FIXTURES.glob("*.yaml"):
        first = fx.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"name:\s*([a-z0-9_]+)", first)
        if m and m.group(1) in RETIRED:
            fails.append(f"L1 fixture targets retired tool: {fx.name}")
    return fails

# ---------- L2 version matrix ----------
def gate_versions():
    fails, tried = [], []
    for ver in ("3.10", "3.11", "3.12"):
        proc = subprocess.run(["uv", "run", "--python", ver, "--no-project", "python", "-c",
            "import py_compile,glob,sys\n"
            "bad=[]\n"
            "[bad.append((f,str(e)[:80])) for f in glob.glob('scripts/*.py')+glob.glob('scripts/utils/*.py')+glob.glob('tests/*.py') if (lambda p: (lambda: [py_compile.compile(p, doraise=True), False][1])() and False)(f)] if False else None\n"
            "import contextlib\n"
            "for f in glob.glob('scripts/*.py')+glob.glob('scripts/utils/*.py')+glob.glob('tests/*.py'):\n"
            "    try: py_compile.compile(f, doraise=True)\n"
            "    except Exception as e: bad.append((f,str(e)[:80]))\n"
            "print('PYFAIL:'+json.dumps(bad) if bad else 'OK')\n"
            "import json"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=180)
        tried.append(ver)
        out = (proc.stdout or "") + (proc.stderr or "")
        if "OK" not in out:
            fails.append(f"L2 py{ver}: {out.strip()[:200]}")
    return fails, tried

# ---------- L3 live tool regression (read-only) ----------
def gate_live(key):
    fails, passed, skipped = [], 0, []
    import yaml
    venv = ROOT / "scripts" / ".venv"
    py = str(venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")) if venv.exists() else sys.executable
    bridge = str(ROOT / "scripts" / "sorftime_bridge.py")
    for fx in sorted(FIXTURES.glob("*.yaml")):
        data = yaml.safe_load(fx.read_text(encoding="utf-8"))
        if not data: continue
        tool = data.get("name", "")
        if not tool or any(p in tool for p in WRITE_PATTERNS):
            skipped.append(tool or fx.name); continue
        cases = data.get("cases") or [data.get("arguments") or data.get("params") or {}]
        for args in cases:
            proc = subprocess.run([py, bridge, "--one-shot", tool, json.dumps(args, ensure_ascii=False)],
                                  capture_output=True, text=True, timeout=60,
                                  env={**os.environ, "SORFTIME_MCP_KEY": key})
            ok = proc.returncode == 0 and not (proc.stdout or "").strip().startswith("An error occurred")
            if ok: passed += 1
            else: fails.append(f"L3 {tool} {json.dumps(args)[:60]}: rc={proc.returncode} {(proc.stdout or proc.stderr)[:120]}")
    return fails, passed, skipped

# ---------- L4 clean-room e2e ----------
def gate_e2e(pack_script=None):
    fails = []
    tmp = Path(tempfile.mkdtemp(prefix="sagent-e2e-"))
    try:
        # pack from working tree via blacklist
        zp = tmp / "pkg.zip"
        BLACK_EXT = (".gif", ".mp4")
        BLACK = {"assets/company-intivo.png", "assets/company-intro.png", "assets/data-coverage.png",
                 "assets/hero-extension.png", "CONTRIBUTING.md", "GITHUB-MAINTENANCE.md", "SUPPORT.md", ".gitignore"}
        BLACK_DIRS = {".git", ".github", "__pycache__", ".venv", ".sync-backups"}
        with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as zo:
            for root, dirs, files in os.walk(ROOT):
                dirs[:] = [d for d in dirs if d not in BLACK_DIRS]
                for f in files:
                    rel = Path(root, f).relative_to(ROOT).as_posix()
                    if rel.endswith(BLACK_EXT) or rel in BLACK: continue
                    zo.write(Path(root, f), rel)
        must = ["SKILL.md", "requirements.txt", ".env.example", "scripts/install.py", "scripts/healthcheck.py",
                "scripts/sorftime_bridge.py", "references/tool-matrix.md"]
        if (ROOT / "config" / "channel.json").exists():
            must.append("config/channel.json")  # channel edition only
        with zipfile.ZipFile(zp) as z:
            got = set(z.namelist())
            z.extractall(tmp / "x")
        for m in must:
            if m not in got: fails.append(f"L4 zip missing {m}")
        if fails: return fails
        env = {k: v for k, v in os.environ.items() if k != "SORFTIME_MCP_KEY"}
        syspy = ROOT / "scripts" / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        # system python must run install (venv python of source tree is fine to bootstrap deps)
        r = subprocess.run([str(syspy) if syspy.exists() else sys.executable, str(tmp / "x" / "scripts" / "install.py"),
                            "--unattended", "--key", "dummy-not-real-key", "--skip-test"],
                           capture_output=True, text=True, timeout=600, cwd=str(tmp / "x"), env=env)
        if r.returncode != 0:
            fails.append(f"L4 install failed rc={r.returncode}: {(r.stdout or r.stderr)[-300:]}")
            return fails
        r2 = subprocess.run([str(syspy) if syspy.exists() else sys.executable, str(tmp / "x" / "scripts" / "healthcheck.py")],
                            capture_output=True, text=True, timeout=300, cwd=str(tmp / "x"),
                            env={k: v for k, v in env.items() if k != "SORFTIME_MCP_KEY"})
        out = r2.stdout + r2.stderr
        # without a key in this clean env, healthcheck must fail at the KEY step (not crash earlier)
        if "Traceback" in out:
            fails.append(f"L4 healthcheck crashed: {out[-300:]}")
        elif "Key" not in out:
            fails.append(f"L4 healthcheck did not reach key check: {out[-200:]}")
        return fails
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-live", action="store_true")
    a = ap.parse_args()
    report = {}
    f1 = gate_static(); report["L1_static"] = f1
    f2, tried = gate_versions(); report["L2_versions"] = f2
    if not a.skip_live:
        key = os.environ.get("SORFTIME_MCP_KEY") or ""
        if not key:
            print("no SORFTIME_MCP_KEY; skipping L3"); report["L3_live"] = ["skipped-no-key"]
        else:
            f3, passed, skipped = gate_live(key)
            report["L3_live"] = f3 + [f"(info) passed={passed} skipped_write_type={len(skipped)}"]
    f4 = gate_e2e(); report["L4_e2e"] = f4
    print("=" * 60)
    hard = False
    for layer, fails in report.items():
        real = [f for f in fails if not f.startswith("(info)") and f != "skipped-no-key"]
        status = "PASS" if not real else "FAIL"
        if real: hard = True
        print(f"[{status}] {layer}")
        for f in fails: print("   ", f)
    print("=" * 60)
    print("GATE:", "GREEN" if not hard else "RED")
    sys.exit(0 if not hard else 1)

if __name__ == "__main__":
    main()
