#!/usr/bin/env python3
"""
卖家画像识别 — 从输入中提取阶段、平台、站点
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from router import detect_platform, detect_site, detect_stage


def parse(text: str) -> dict:
    platform = detect_platform(text)
    site = detect_site(text, platform)
    stage = detect_stage(text)
    return {
        "seller_stage": stage,
        "platform": platform,
        "site": site,
        "original_text": text,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    args = parser.parse_args()
    print(json.dumps(parse(args.text), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
