#!/usr/bin/env python3
"""
Sorftime MCP 自动同步入口

触发场景：
  1. 每次技能加载时自动检测（如 healthcheck 中调用）
  2. 用户主动说 "同步 Sorftime 工具"
  3. CI / Cron 定时任务
  4. MCP 调用报错 "Unknown tool" 时自动触发

用法：
  python3 tests/auto_sync.py           # 检测变更，有变更时自动应用
  python3 tests/auto_sync.py --force   # 强制同步（无论是否有变更）
  python3 tests/auto_sync.py --dry-run # 仅检测和报告，不写入
"""

import argparse
import subprocess
import sys
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent
SYNC_MANAGER = _SKILL_ROOT / "scripts" / "sync_manager.py"


def main():
    parser = argparse.ArgumentParser(description="Sorftime MCP 自动同步")
    parser.add_argument("--force", action="store_true", help="强制同步，忽略缓存")
    parser.add_argument("--dry-run", action="store_true", help="仅检测和报告，不写入")
    args = parser.parse_args()

    if args.dry_run:
        # 仅 diff 模式
        cmd = [sys.executable, str(SYNC_MANAGER), "diff"]
        subprocess.run(cmd, check=False)
        return

    # 完整同步流程
    cmd = [sys.executable, str(SYNC_MANAGER), "full"]
    if args.force:
        # 先清除本地缓存，强制重新拉取
        cache_file = _SKILL_ROOT / ".sorftime-cache" / "schema-store" / "latest.json"
        if cache_file.exists():
            cache_file.unlink()
            print("🗑️  已清除本地缓存，将强制重新拉取")

    result = subprocess.run(cmd, check=False)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
