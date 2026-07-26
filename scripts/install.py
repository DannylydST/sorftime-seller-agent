#!/usr/bin/env python3
"""
Sorftime MCP Bridge — One-Click Installer
Auto-configures CC / OpenClaw environments
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
VENV_DIR = SKILL_DIR / ".venv"
BRIDGE_SCRIPT = SKILL_DIR / "scripts" / "sorftime_bridge.py"
HOME = Path.home()

sys.path.insert(0, str(SKILL_DIR / "scripts"))
from utils.env_config import save_key
from utils.platform_utils import (
    get_venv_python,
    get_venv_pip,
    get_agent_config_dir,
    detect_agent_env,
    detect_shell_rc,
)


def run(cmd: list, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def check_python():
    print("[1/7] Checking Python version...")
    result = run([sys.executable, "--version"])
    version_str = result.stdout.strip() or result.stderr.strip()
    print(f"    {version_str}")
    major, minor = sys.version_info.major, sys.version_info.minor
    if major < 3 or (major == 3 and minor < 10):
        print("    ❌ Python >= 3.10 required")
        print()
        print("    Installation guide:")
        if sys.platform == "darwin":
            print("    macOS: brew install python@3.12")
        elif sys.platform == "win32":
            print("    Windows: Visit https://python.org/downloads to install Python 3.12")
        else:
            print("    Linux: sudo apt install python3.12 or sudo dnf install python3.12")
        sys.exit(1)
    print("    ✅ Python version meets requirements")


def install_deps():
    print("[2/7] Installing dependencies...")
    if not VENV_DIR.exists():
        print("    Creating virtual environment...")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])

    pip = get_venv_pip()
    result = run([str(pip), "install", "-q", "mcp", "httpx", "socksio", "pyyaml"])
    if result.returncode != 0:
        print(f"    ❌ Installation failed: {result.stderr}")
        sys.exit(1)
    print("    ✅ mcp, httpx installed to virtual environment")


def detect_env() -> str:
    print("[3/7] Detecting runtime environment...")
    env = detect_agent_env()
    print(f"    Detected environment: {env}")
    return env


def prompt_key(cli_key: str = "") -> str:
    print("[4/7] Checking API Key...")
    if cli_key:
        masked = cli_key[:4] + "****" + cli_key[-4:] if len(cli_key) > 8 else "****"
        print(f"    SORFTIME_MCP_KEY provided via --key={masked}")
        return cli_key

    key = os.getenv("SORFTIME_MCP_KEY", "")
    if key:
        masked = key[:4] + "****" + key[-4:] if len(key) > 8 else "****"
        print(f"    Detected SORFTIME_MCP_KEY env var={masked}")
        return key

    print("    ⚠️  SORFTIME_MCP_KEY environment variable not found")
    print("    Sign up at https://open-intl.sorftime.com (Google login available, free trial credits included)")
    print("    Then go to the MCP page to copy your Key.")
    key = input("    Enter your Sorftime MCP Key: ").strip()
    if not key:
        print("    ❌ Key cannot be empty")
        sys.exit(1)

    # Suggest writing to shell rc
    rc_file = detect_shell_rc()
    if rc_file:
        print(f"\n    Tip: Add the following to your {rc_file}:")
    else:
        print("\n    Tip: Add the following environment variable to your system config:")
    print(f'    export SORFTIME_MCP_KEY="{key}"')
    return key


def test_connection(key: str) -> dict:
    print("[5/7] Testing Sorftime connection...")
    python = get_venv_python()
    env = os.environ.copy()
    env["SORFTIME_MCP_KEY"] = key
    test_code = f"""
import asyncio, sys, os
sys.path.insert(0, {repr(str(SKILL_DIR / "scripts"))})
from sorftime_bridge import call_sorftime
async def main():
    try:
        r = await call_sorftime("get_time", {})
        print(r)
    except Exception as e:
        print(f"ERROR: {e}")
asyncio.run(main())
"""
    result = subprocess.run([str(python), "-c", test_code], capture_output=True, text=True, env=env, cwd=str(SKILL_DIR / "scripts"))
    if "ERROR" in result.stdout or result.returncode != 0:
        err = f"{result.stdout}{result.stderr}"
        print(f"    ❌ Connection test failed: {err}")
        return {"status": "error", "message": err.strip()}
    print(f"    ✅ Connection successful, response: {result.stdout.strip()}")
    return {"status": "ok", "response": result.stdout.strip()}


def gen_cc_config(key: str):
    print("\n[6/7] Claude Code config snippet (mcporter.json):")
    config = {
        "mcpServers": {
            "sorftime-seller-agent": {
                "command": str(get_venv_python()),
                "args": [str(BRIDGE_SCRIPT)],
                "env": {"SORFTIME_MCP_KEY": key},
            }
        }
    }
    print(json.dumps(config, indent=2, ensure_ascii=False))
    agent_cfg = get_agent_config_dir()
    if agent_cfg:
        mcporter_path = agent_cfg / "skills-installed" / "config" / "mcporter.json"
        mcp_path = agent_cfg / "mcp" / "mcp-config.json"
        print(f"\n    Merge into one of the following config files:")
        print(f"    - {mcporter_path}  (mcporter main config, recommended)")
        print(f"    - {mcp_path}  (Claude Code MCP config)")
    else:
        print("\n    No agent config directory detected. Manually add the above config to your MCP settings.")


def gen_openclaw_config(key: str):
    print("\n[7/7] OpenClaw config snippet (openclaw.json):")
    scripts_dir = SKILL_DIR / "scripts"
    config = {
        "skills": {"extraDirs": [str(SKILL_DIR)]},
        "agents": {
            "list": [
                {
                    "id": "default",
                    "exec": {
                        "safeBins": [
                            str(BRIDGE_SCRIPT),
                            str(scripts_dir / "router.py"),
                            str(scripts_dir / "picker.py"),
                            str(scripts_dir / "analyst.py"),
                            str(scripts_dir / "monitor.py"),
                            str(scripts_dir / "calculator.py"),
                            str(scripts_dir / "platform_router.py"),
                            str(scripts_dir / "persona.py"),
                            str(scripts_dir / "stage_formatter.py"),
                            str(scripts_dir / "explorer" / "content-capture.js"),
                        ],
                        "safeBinTrustedDirs": [
                            str(SKILL_DIR / "scripts"),
                            str(SKILL_DIR / "tests"),
                        ],
                        "safeBinProfiles": {},
                    },
                }
            ]
        },
    }
    print(json.dumps(config, indent=2, ensure_ascii=False))
    openclaw_cfg = get_agent_config_dir()
    if openclaw_cfg and (openclaw_cfg / "openclaw.json").exists():
        print(f"\n    Merge into: {openclaw_cfg / 'openclaw.json'}")
    else:
        print("\n    Merge into your OpenClaw config file (usually ~/.openclaw/openclaw.json)")


def main():
    parser = argparse.ArgumentParser(description="Sorftime Seller Agent Installer")
    parser.add_argument("--key", type=str, default="", help="Provide Sorftime MCP Key directly, skip interactive input")
    parser.add_argument("--unattended", action="store_true", help="Unattended mode, output JSON results only")
    parser.add_argument("--skip-test", action="store_true", help="Skip connection test")
    args = parser.parse_args()

    if not args.unattended:
        print("=" * 60)
        print(" Sorftime MCP Bridge Installer")
        print("=" * 60)

    check_python()
    install_deps()
    env = detect_env()
    key = prompt_key(args.key)

    # Auto-save to skill local .env
    save_key(key)
    if not args.unattended:
        print(f"    ✅ Key saved to skill .env ({SKILL_DIR / '.env'})")

    test_result = {"status": "skipped"}
    if not args.skip_test:
        test_result = test_connection(key)
        if test_result["status"] == "error":
            if args.unattended:
                print(json.dumps({"status": "error", "key_saved": True, "test_passed": False, "message": test_result["message"]}, ensure_ascii=False))
            sys.exit(1)
    else:
        if not args.unattended:
            print("    ⏭️  Connection test skipped")

    if not args.unattended:
        if env in ("claude-code", "both"):
            gen_cc_config(key)
        if env in ("openclaw", "both"):
            gen_openclaw_config(key)

        print("\n" + "=" * 60)
        print(" Sorftime Seller Agent Installation Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Add SORFTIME_MCP_KEY to your shell profile and source it")
        print("2. Update mcporter.json or openclaw.json with the config snippet above")
        print("3. Test in Claude Code / OpenClaw: mcporter call sorftime-seller-agent get_time --json '{}'")
    else:
        print(json.dumps({
            "status": "ok",
            "key_saved": True,
            "test_passed": test_result.get("status") == "ok",
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
