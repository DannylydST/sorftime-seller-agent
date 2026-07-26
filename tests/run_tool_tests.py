#!/usr/bin/env python3
"""
Sorftime MCP 工具自动化测试运行器
读取 fixtures/*.yaml，调用 bridge --one-shot 执行测试，生成结果报告
"""

import argparse
import json
import os
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

import yaml

# 动态定位技能根目录和工具路径
_SKILL_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SKILL_ROOT / "scripts"))
from utils.platform_utils import get_venv_python, get_cache_dir

BRIDGE_PATH = _SKILL_ROOT / "scripts" / "sorftime_bridge.py"
VENV_PYTHON = get_venv_python()
FIXTURES_DIR = Path(__file__).parent / "fixtures"
RESULTS_BASE_DIR = get_cache_dir() / "test-results"
TIMEOUT_SECONDS = 30


def load_yaml_fixtures() -> list[dict]:
    """加载 fixtures 目录下所有 YAML 文件"""
    fixtures = []
    for yaml_file in sorted(FIXTURES_DIR.glob("*.yaml")):
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data:
                    data["_source"] = yaml_file.name
                    fixtures.append(data)
        except Exception as e:
            print(f"⚠️  加载 {yaml_file.name} 失败: {e}")
    return fixtures


def run_test(tool_name: str, arguments: dict) -> dict:
    """运行单个测试用例"""
    args_json = json.dumps(arguments, ensure_ascii=False)
    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    cmd = [python, str(BRIDGE_PATH), "--one-shot", tool_name, args_json]

    start = datetime.now()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            env=os.environ.copy(),
        )
        elapsed = (datetime.now() - start).total_seconds()

        success = result.returncode == 0 and not result.stdout.strip().startswith("An error occurred")
        return {
            "success": success,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "elapsed_seconds": round(elapsed, 2),
            "cmd": " ".join(cmd),
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"TIMEOUT after {TIMEOUT_SECONDS}s",
            "elapsed_seconds": TIMEOUT_SECONDS,
            "cmd": " ".join(cmd),
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "elapsed_seconds": 0,
            "cmd": " ".join(cmd),
        }


def main():
    parser = argparse.ArgumentParser(description="Sorftime MCP 工具测试运行器")
    parser.add_argument("--filter", help="只运行匹配工具名的测试")
    args = parser.parse_args()

    fixtures = load_yaml_fixtures()
    if not fixtures:
        print("❌ 未找到 fixtures/*.yaml 测试用例")
        sys.exit(1)

    RESULTS_BASE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results = {"timestamp": timestamp, "tests": []}

    total = len(fixtures)
    passed = 0

    print(f"🧪 开始运行 {total} 个测试用例...\n")

    for i, fixture in enumerate(fixtures, 1):
        tool = fixture.get("tool", "unknown")
        if args.filter and args.filter not in tool:
            continue

        name = fixture.get("name", tool)
        arguments = fixture.get("arguments", {})

        print(f"[{i}/{total}] {name} (tool={tool})")
        result = run_test(tool, arguments)
        results["tests"].append({
            "name": name,
            "tool": tool,
            **result,
        })

        if result["success"]:
            passed += 1
            print(f"    ✅ 通过 ({result['elapsed_seconds']}s)")
        else:
            print(f"    ❌ 失败")
            if result["stderr"]:
                print(f"       stderr: {result['stderr'][:200]}")

    results["summary"] = {
        "total": len(results["tests"]),
        "passed": passed,
        "failed": len(results["tests"]) - passed,
    }

    result_file = RESULTS_BASE_DIR / f"test-results-{timestamp}.json"
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"结果: {passed}/{len(results['tests'])} 通过")
    print(f"报告: {result_file}")

    sys.exit(0 if passed == len(results["tests"]) else 1)


if __name__ == "__main__":
    main()
