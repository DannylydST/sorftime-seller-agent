#!/usr/bin/env python3
"""
批量深度分析脚本 — 对15个高优先级ASIN执行：
1. 竞品拆解 (analyst.py --mode competitor)
2. 利润精算 (calculator.py)
3. 1688货源搜索 (ali1688_similar_product)

结果保存到 ~/.sorftime-cache/batch_analysis/ 目录
"""

import subprocess
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils.platform_utils import get_cache_dir

OUTPUT_DIR = get_cache_dir() / "batch_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 前15个高优先级产品
PRODUCTS = [
    {"asin": "B0GRSSW6R1", "name": "PawSono狗狗护爪膏", "price": 25.99, "weight": 0.15, "cost_rate": 0.35, "keyword": "dog paw balm coconut oil"},
    {"asin": "B0FWB8XT5F", "name": "电动胡椒研磨器", "price": 39.99, "weight": 0.40, "cost_rate": 0.35, "keyword": "electric salt pepper grinder rechargeable"},
    {"asin": "B0F8GRZJGR", "name": "EOENVIVS塑料收纳篮", "price": 25.99, "weight": 0.30, "cost_rate": 0.32, "keyword": "plastic storage bins with lids stackable"},
    {"asin": "B0FYNPF764", "name": "一次性马桶刷套装", "price": 29.99, "weight": 0.50, "cost_rate": 0.35, "keyword": "disposable toilet brush refills"},
    {"asin": "B0FZV4LDZJ", "name": "便携式淋浴清洁刷4件套", "price": 26.99, "weight": 0.40, "cost_rate": 0.35, "keyword": "shower cleaning brush set"},
    {"asin": "B0FFH6LKNR", "name": "窗户轨道清洁套装14件套", "price": 12.99, "weight": 0.30, "cost_rate": 0.35, "keyword": "window track cleaning tool"},
    {"asin": "B0F7XP4S6M", "name": "魔术清洁海绵", "price": 21.99, "weight": 0.20, "cost_rate": 0.30, "keyword": "magic eraser sponges bulk"},
    {"asin": "B0F2LZR538", "name": "TOIVO大蒜储存罐", "price": 19.99, "weight": 0.30, "cost_rate": 0.35, "keyword": "garlic keeper ceramic"},
    {"asin": "B0FPFRSNQP", "name": "MUTUACTOR强磁挂钩", "price": 29.99, "weight": 0.40, "cost_rate": 0.35, "keyword": "heavy duty magnetic hooks"},
    {"asin": "B0GDWXFDF6", "name": "VANMASS车载手机支架", "price": 24.95, "weight": 0.25, "cost_rate": 0.35, "keyword": "car phone holder dashboard mount"},
    {"asin": "B0FLJJF68S", "name": "浴室柜下拉式收纳架", "price": 18.88, "weight": 0.50, "cost_rate": 0.35, "keyword": "under sink organizer pull out"},
    {"asin": "B0FHCTSN1V", "name": "透明亚克力洗脸巾收纳盒", "price": 39.99, "weight": 0.40, "cost_rate": 0.35, "keyword": "acrylic face towel holder"},
    {"asin": "B0F9LJV17X", "name": "ECOLOVI桌面收纳套装", "price": 18.99, "weight": 0.40, "cost_rate": 0.35, "keyword": "desk organizer accessories set"},
    {"asin": "B0FFMTJGQH", "name": "CABTE桌边杯架手机支架", "price": 12.99, "weight": 0.20, "cost_rate": 0.35, "keyword": "desk cup holder with phone stand"},
    {"asin": "B0FBG6ZL5W", "name": "鸡肉撕碎器", "price": 6.08, "weight": 0.30, "cost_rate": 0.35, "keyword": "chicken shredder tool"},
]

SCRIPT_DIR = Path(__file__).resolve().parent


def run_command(cmd, timeout=60):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return f"ERROR: Command timed out after {timeout}s"
    except Exception as e:
        return f"ERROR: {e}"


def analyze_competitor(asin):
    """竞品拆解"""
    cmd = [
        sys.executable, str(SCRIPT_DIR / "analyst.py"),
        "--mode", "competitor",
        "--platform", "amazon",
        "--site", "US",
        "--asin", asin
    ]
    return run_command(cmd, timeout=45)


def calculate_profit(price, cost, weight):
    """利润精算"""
    cmd = [
        sys.executable, str(SCRIPT_DIR / "calculator.py"),
        "--platform", "amazon",
        "--price", str(price),
        "--cost", str(round(cost, 2)),
        "--weight", str(weight)
    ]
    return run_command(cmd, timeout=15)


def search_1688(keyword, product_name=""):
    """1688货源搜索（含降级提示）"""
    cmd = [
        sys.executable, str(SCRIPT_DIR / "sorftime_bridge.py"),
        "--one-shot", "ali1688_similar_product",
        f'{{"search_name":"{keyword}"}}'
    ]
    output = run_command(cmd, timeout=30)

    # 如果 MCP 工具报错，附上手动手动搜索建议
    if "Sorftime MCP 错误" in output or "error occurred invoking" in output.lower():
        fallback = f"""
\n---
\n> **1688 货源搜索（手动）**
> Sorftime MCP 的 `ali1688_similar_product` 接口当前服务端不可用，建议手动在 1688 搜索：
>
> - 搜索关键词：`{keyword}`
> - 目标产品：{product_name or keyword}
> - 操作建议：筛选 "实力商家" + "深度验厂"，拿样 3-5 家对比质量和价格
"""
        output = output.strip() + fallback

    return output


def main():
    print("=" * 70)
    print("批量深度分析 — 15个高优先级产品")
    print("=" * 70)
    print()

    results = []

    for i, p in enumerate(PRODUCTS, 1):
        asin = p["asin"]
        name = p["name"]
        price = p["price"]
        weight = p["weight"]
        cost = price * p["cost_rate"]

        print(f"[{i}/15] 分析: {name} ({asin})")
        print("-" * 50)

        # 1. 竞品拆解
        print("  1. 竞品拆解...", end=" ", flush=True)
        t0 = time.time()
        comp_output = analyze_competitor(asin)
        t1 = time.time()
        print(f"完成 ({t1-t0:.1f}s)")

        # 保存竞品分析
        comp_file = OUTPUT_DIR / f"{asin}_competitor.md"
        comp_file.write_text(comp_output)

        # 2. 利润精算
        print("  2. 利润精算...", end=" ", flush=True)
        profit_output = calculate_profit(price, cost, weight)
        print("完成")

        # 保存利润分析
        profit_file = OUTPUT_DIR / f"{asin}_profit.md"
        profit_file.write_text(profit_output)

        # 3. 1688货源搜索
        print("  3. 1688货源...", end=" ", flush=True)
        t0 = time.time()
        source_output = search_1688(p["keyword"], p["name"])
        t1 = time.time()
        print(f"完成 ({t1-t0:.1f}s)")

        # 保存货源分析
        source_file = OUTPUT_DIR / f"{asin}_1688.md"
        source_file.write_text(source_output)

        # 记录结果摘要
        results.append({
            "asin": asin,
            "name": name,
            "price": price,
            "cost": round(cost, 2),
            "profit_file": str(profit_file),
            "comp_file": str(comp_file),
            "source_file": str(source_file),
        })

        print()

    # 保存汇总索引
    index_file = OUTPUT_DIR / "index.json"
    index_file.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    print("=" * 70)
    print("全部完成！")
    print(f"结果保存在: {OUTPUT_DIR}")
    print(f"汇总索引: {index_file}")
    print()

    # 打印利润摘要
    print("## 利润摘要汇总")
    print()
    for r in results:
        profit_text = Path(r["profit_file"]).read_text()
        # 提取净利润
        for line in profit_text.split("\n"):
            if "单件净利润" in line:
                print(f"| {r['name'][:20]:<20} | ${r['price']:<6} | {line.strip()} |")
                break


if __name__ == "__main__":
    main()
