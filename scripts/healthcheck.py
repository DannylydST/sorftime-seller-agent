#!/usr/bin/env python3
"""
Sorftime Seller Agent Health Check
One-click diagnostic for skill configuration health

Usage:
  python3 scripts/healthcheck.py          # Human-friendly output (default)
  python3 scripts/healthcheck.py --json   # JSON output (agent use)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = SKILL_DIR / ".venv"

sys.path.insert(0, str(SKILL_DIR / "scripts"))
from utils.env_config import get_key
from utils.platform_utils import get_venv_python

VENV_PYTHON = get_venv_python()


REQUIRED_DEPS = ["mcp", "httpx", "socksio", "yaml"]
CRITICAL_SCRIPTS = [
    "picker.py",
    "analyst.py",
    "calculator.py",
    "monitor.py",
    "walmart_picker.py",
    "walmart_analyst.py",
]

# Human-friendly icons
ICON_OK = "✅"
ICON_ERR = "❌"
ICON_WARN = "⚠️"
ICON_INFO = "ℹ️"


def check_python() -> dict:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = sys.version_info >= (3, 10)
    result = {
        "name": "Python Version",
        "status": "ok" if ok else "error",
        "detail": f"{version} (requires >= 3.10)",
        "fix": None if ok else _python_fix_hint(),
    }
    return result


def _python_fix_hint() -> str:
    if sys.platform == "darwin":
        return "macOS: Run `brew install python@3.12` or visit https://python.org/downloads"
    elif sys.platform == "win32":
        return "Windows: Visit https://python.org/downloads to install Python 3.12"
    else:
        return "Linux: Run `sudo apt install python3.12` or `sudo dnf install python3.12`"


def check_venv() -> dict:
    ok = VENV_DIR.exists() and VENV_PYTHON.exists()
    return {
        "name": "Virtual Env",
        "status": "ok" if ok else "error",
        "detail": "Created" if ok else "Not created",
        "fix": None if ok else "Run `python3 scripts/install.py` to auto-create the virtual environment",
    }


def check_deps() -> dict:
    missing = []
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    for dep in REQUIRED_DEPS:
        try:
            result = subprocess.run(
                [python, "-c", f"import {dep}"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                missing.append(dep)
        except Exception:
            missing.append(dep)
    ok = not missing
    return {
        "name": "Dependencies",
        "status": "ok" if ok else "error",
        "detail": "All ready" if ok else f"Missing: {', '.join(missing)}",
        "fix": None if ok else "Run `python3 scripts/install.py` to auto-install missing dependencies",
    }


def check_key() -> dict:
    key = get_key()
    if not key:
        return {
            "name": "API Key",
            "status": "error",
            "detail": "Not configured",
            "fix": "1. Create a free account at https://open-intl.sorftime.com (Google login supported, free trial credits included)\n   2. Go to the MCP page and copy your Key\n   3. Run `python3 scripts/install.py --key <your-key>`",
        }
    env_key = os.getenv("SORFTIME_MCP_KEY", "").strip()
    source = "Environment Variable" if env_key else "Local .env File"
    masked = key[:4] + "****" + key[-4:] if len(key) > 8 else "****"
    return {
        "name": "API Key",
        "status": "ok",
        "detail": f"Configured ({masked}), source: {source}",
        "fix": None,
    }


def check_mcp_connection() -> dict:
    key = get_key()
    if not key:
        return {
            "name": "Sorftime Connect",
            "status": "error",
            "detail": "Key not configured, skipping connection test",
            "fix": "Configure the API Key first, then re-run healthcheck",
        }

    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    env = os.environ.copy()
    env["SORFTIME_MCP_KEY"] = key
    test_code = """
import asyncio, sys, os
sys.path.insert(0, os.path.abspath('scripts'))
from sorftime_bridge import call_sorftime
async def main():
    try:
        r = await call_sorftime("get_time", {})
        print(r)
    except Exception as e:
        print(f"ERROR: {e}")
asyncio.run(main())
"""
    result = subprocess.run(
        [python, "-c", test_code],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(SKILL_DIR),
    )
    stdout = result.stdout.strip()
    if result.returncode != 0 or "ERROR" in stdout:
        err = stdout or result.stderr
        return {
            "name": "Sorftime Connect",
            "status": "error",
            "detail": f"Connection failed: {err[:100]}",
            "fix": "1. Check if the Key was copied completely (no missing characters)\n   2. Confirm your account has MCP service enabled (check MCP page after login)\n   3. Check network access to open-intl.sorftime.com\n   4. New accounts get free trial credits — if exhausted, top up via PayPal",
        }
    return {
        "name": "Sorftime Connect",
        "status": "ok",
        "detail": f"OK ({stdout[:50]})",
        "fix": None,
    }


def check_scripts() -> dict:
    import py_compile
    failed = []
    scripts_dir = SKILL_DIR / "scripts"
    for name in CRITICAL_SCRIPTS:
        path = scripts_dir / name
        if not path.exists():
            failed.append(name)
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as e:
            failed.append(f"{name} ({e})")
    ok = not failed
    return {
        "name": "Core Scripts",
        "status": "ok" if ok else "error",
        "detail": "All passed" if ok else f"Failed: {', '.join(failed)}",
        "fix": None if ok else "Files may be corrupted — try re-extracting the skill package",
    }


def check_schema_sync() -> dict:
    """Check if local Schema is in sync with server"""
    try:
        sys.path.insert(0, str(SKILL_DIR / "scripts"))
        from utils.schema_store import load_latest, SCHEMA_DIR

        cached_tools = load_latest()
        if not cached_tools:
            return {
                "name": "Schema Sync",
                "status": "warn",
                "detail": "Never synced — run `python3 tests/auto_sync.py` to sync",
                "fix": "python3 tests/auto_sync.py",
            }

        # Check if cache is more than 7 days old
        latest_file = SCHEMA_DIR / "latest.json"
        import time
        mtime = latest_file.stat().st_mtime
        age_days = (time.time() - mtime) / 86400

        if age_days > 7:
            return {
                "name": "Schema Sync",
                "status": "warn",
                "detail": f"Schema is {age_days:.0f} days old — may be out of sync with server",
                "fix": "python3 tests/auto_sync.py",
            }

        return {
            "name": "Schema Sync",
            "status": "ok",
            "detail": f"Synced {len(cached_tools)} tools ({age_days:.0f} days ago)",
            "fix": None,
        }
    except Exception as e:
        return {
            "name": "Schema Sync",
            "status": "warn",
            "detail": f"Check failed: {e}",
            "fix": "python3 tests/auto_sync.py",
        }


def _print_human(checks: list[dict], overall_ok: bool, has_warnings: bool):
    """Human-friendly output format"""
    print("=" * 50)
    print(" Sorftime Seller Agent Health Check")
    print("=" * 50)
    print()

    for c in checks:
        status = c["status"]
        if status == "ok":
            icon = ICON_OK
        elif status == "warn":
            icon = ICON_WARN
        else:
            icon = ICON_ERR
        print(f"  {icon} {c['name']:<18}  {c['detail']}")
        if c["fix"] and c["status"] == "error":
            for line in c["fix"].split("\n"):
                print(f"      {ICON_INFO} {line}")
            print()

    print()
    print("=" * 50)
    if overall_ok:
        if has_warnings:
            print(f"  {ICON_OK} Core checks passed. {ICON_WARN} Non-blocking: Schema may be stale, auto_sync when convenient.")
        else:
            print(f"  {ICON_OK} All checks passed! You're ready to get started.")
        print()
        print("  Try asking your AI:")
        print('    "Find blue ocean products in yoga mats"')
        print('    "Analyze ASIN B08N5WRWNW"')
        print('    "Calculate profit: price $29.99, cost $8.50"')
    else:
        error_count = sum(1 for c in checks if c["status"] == "error")
        warn_count = sum(1 for c in checks if c["status"] == "warn")
        parts = [f"{error_count} error(s)"]
        if warn_count:
            parts.append(f"{warn_count} warning(s)")
        print(f"  {ICON_ERR} Found {", ".join(parts)}. Follow the hints above to fix.")
        print()
        print(f"  Re-run after fixing: python3 scripts/healthcheck.py")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Sorftime Seller Agent Health Check")
    parser.add_argument("--json", action="store_true", help="Output JSON format (for agent use)")
    args = parser.parse_args()

    checks = [
        check_python(),
        check_venv(),
        check_deps(),
        check_key(),
        check_mcp_connection(),
        check_scripts(),
        check_schema_sync(),
    ]
    errors = [c for c in checks if c["status"] == "error"]
    warnings = [c for c in checks if c["status"] == "warn"]
    overall_ok = len(errors) == 0
    has_warnings = len(warnings) > 0

    if args.json:
        # JSON mode: backward-compatible output format
        json_checks = {c["name"].replace(" ", "_").lower(): {
            "status": c["status"],
            **({"detail": c["detail"]} if c["detail"] else {}),
            **({"fix": c["fix"]} if c["fix"] else {}),
        } for c in checks}
        result = {"status": "ok" if overall_ok else "error", "checks": json_checks}
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_human(checks, overall_ok, has_warnings)

    sys.exit(0 if overall_ok else 1)


if __name__ == "__main__":
    main()
