#!/usr/bin/env python3
"""
精铺卖家选品过滤器
筛选条件：
- 价格 $5-$25（低资金占用）
- 重量 < 1lb（低FBA费用）
- 月销量 > 1000（已验证需求）
- 评论数 50-5000（有市场但未被大品牌垄断）
- 排除 Amazon Basics / 超大品牌
- 优先：快消品、重复购买、小件轻货
- 排除：食品/保健品（硬阻断）、大件/重货
"""

import json
import sys
from pathlib import Path

# 大类风险映射
HARD_BLOCK_CATEGORIES = {
    "Grocery", "Health", "Baby", "Medic", "Drug", "Supplement",
    "Food", "Vitamin", "Protein", "Cosmetic"
}

# 真正的大品牌垄断 = 只有这些会构成品牌垄断威胁
# 注意：Vtopmart/Lifewit 等是典型精铺卖家的成功模式，不应排除
MEGA_BRANDS = {
    "Amazon Basics", "Amazon",
    "KitchenAid", "OXO", "Swiffer", "BLACK+DECKER",
    "Bounce", "Post-it", "Reynolds",
    "Hill's Science Diet", "Purina", "Blue Buffalo",
    "Milk-Bone", "Greenies", "Seresto", "Fresh Step", "Arm & Hammer",
    "Meow Mix", "Sheba", "Temptations", "Pedigree", "Cesar",
    "Advantage", "PetArmor", "Pro Plan", "Nutramax",
    "Core Power",  # 饮料大牌
    "Magic Bullet",  # 小家电大牌
}

# 重量阈值 (lb) - 放宽到3lb，收纳类稍重仍可接受
MAX_WEIGHT = 3.0
# 价格范围 - 放宽到$5-$35
MIN_PRICE = 5.0
MAX_PRICE = 35.0
# 月销量 - 放宽到500，覆盖更多潜力品
MIN_SALES = 500
# 评论数 - 放宽上限到20000
MIN_REVIEWS = 30
MAX_REVIEWS = 20000


def parse_products_from_file(filepath: Path) -> list[dict]:
    """从工具结果文件中提取产品JSON数据"""
    text = filepath.read_text(encoding="utf-8")
    # 找到JSON数组部分
    start = text.find("[")
    if start == -1:
        return []
    # 尝试找到匹配的 ]
    end = text.rfind("]")
    if end == -1:
        return []
    try:
        return json.loads(text[start:end+1])
    except json.JSONDecodeError:
        # 可能是多行JSON对象
        products = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("直接罗列"):
                continue
            try:
                data = json.loads(line)
                if isinstance(data, list):
                    products.extend(data)
                elif isinstance(data, dict):
                    products.append(data)
            except json.JSONDecodeError:
                pass
        return products


def is_hard_block(product: dict) -> bool:
    """检查是否属于硬阻断品类"""
    category = product.get("所属大类", "")
    for block in HARD_BLOCK_CATEGORIES:
        if block.lower() in category.lower():
            return True
    # 检查标题中的食品/保健关键词（仅针对宠物类目）
    title = product.get("标题", "").lower()
    # 严格宠物食品/保健关键词
    pet_food_keywords = [
        "dog food", "cat food", "protein drink", "protein shake",
        "vitamin supplement", "probiotic supplement", "dog treat", "cat treat",
        "jerky treat", "dental treat", "flea collar", "tick collar",
        "cat litter", "dog pad", "puppy pad", "dog diaper",
        "wet cat food", "wet dog food", "dry cat food", "dry dog food",
        "canned cat", "canned dog", "kibble", "biscuit", "dog cookie",
        "cat snack", "dog snack", "chew toy"  # chew toy不算食品但属于宠物用品
    ]
    # 仅对宠物/食品大类执行
    cat_lower = category.lower()
    if "pet" in cat_lower or "grocery" in cat_lower or "food" in cat_lower or "health" in cat_lower:
        for kw in pet_food_keywords:
            if kw in title:
                return True
    return False


def is_mega_brand(product: dict) -> bool:
    brand = product.get("品牌", "")
    return brand in MEGA_BRANDS or "Amazon" in brand


def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def score_product(p: dict) -> float:
    """
    给产品打分，分数越高越适合精铺
    评分维度：
    - 月销量（越高越好）
    - 价格适中度（$10-15 最佳）
    - 重量（越轻越好）
    - 评论数（适中，表示有市场但竞争不过度）
    - 上架时间（越新越好，表示市场还在增长）
    """
    sales = safe_int(p.get("月销量"), 0)
    price = safe_float(p.get("价格"), 0)
    weight = safe_float(p.get("重量"), 0)
    reviews = safe_int(p.get("评论数"), 0)

    score = 0.0

    # 月销量得分 (0-40)
    if sales >= 50000:
        score += 40
    elif sales >= 20000:
        score += 35
    elif sales >= 10000:
        score += 30
    elif sales >= 5000:
        score += 25
    elif sales >= 2000:
        score += 20
    else:
        score += 10

    # 价格适中度 (0-20) $10-15最佳
    if 10 <= price <= 15:
        score += 20
    elif 8 <= price <= 18:
        score += 15
    elif 5 <= price <= 20:
        score += 10
    else:
        score += 5

    # 重量得分 (0-20) 越轻越好
    if weight <= 0.2:
        score += 20
    elif weight <= 0.5:
        score += 15
    elif weight <= 0.8:
        score += 10
    else:
        score += 5

    # 评论数得分 (0-10) 适中最好
    if 100 <= reviews <= 1000:
        score += 10
    elif 50 <= reviews <= 2000:
        score += 8
    elif reviews <= 5000:
        score += 5
    else:
        score += 2

    # 快消品/重复购买加分
    title = p.get("标题", "").lower()
    repeat_keywords = ["cleaner", "wiper", "refill", "pad", "filter",
                       "bag", "wipe", "tissue", "glove", "sponge",
                       "brush", "cloth", "holder", "organizer"]
    for kw in repeat_keywords:
        if kw in title:
            score += 5
            break

    # 排除评分过低
    rating = safe_float(p.get("星级"), 4.0)
    if rating < 4.0:
        score -= 10
    if rating < 3.5:
        score -= 20

    return score


def filter_products(products: list[dict]) -> list[dict]:
    """过滤并排序产品"""
    filtered = []
    for p in products:
        price = safe_float(p.get("价格"), 0)
        weight = safe_float(p.get("重量"), 0)
        sales = safe_int(p.get("月销量"), 0)
        reviews = safe_int(p.get("评论数"), 0)
        rating = safe_float(p.get("星级"), 0)

        # 基本过滤
        if price <= 0 or price < MIN_PRICE or price > MAX_PRICE:
            continue
        if weight > MAX_WEIGHT:
            continue
        if sales < MIN_SALES:
            continue
        if reviews < MIN_REVIEWS or reviews > MAX_REVIEWS:
            continue
        if rating < 3.8:
            continue

        # 硬阻断
        if is_hard_block(p):
            continue

        # 大品牌垄断
        if is_mega_brand(p):
            continue

        # FBM/N/A 发货方式降低权重但不完全排除
        shipping = p.get("发货方式", "FBA")
        if shipping in ("FBM", "N/A"):
            # FBM需要更高门槛
            if sales < 2000 or reviews < 100:
                continue

        p["_score"] = score_product(p)
        filtered.append(p)

    # 按分数降序
    filtered.sort(key=lambda x: x["_score"], reverse=True)
    return filtered


def deduplicate(products: list[dict]) -> list[dict]:
    """按ASIN去重"""
    seen = set()
    result = []
    for p in products:
        asin = p.get("产品ASIN码", "")
        if asin and asin not in seen:
            seen.add(asin)
            result.append(p)
    return result


def main():
    # Default: ~/.sorftime-cache/tool-results/ — override with SORFTIME_CACHE_DIR
    cache_root = Path(os.environ.get("SORFTIME_CACHE_DIR", Path.home() / ".sorftime-cache"))
    tool_results_dir = cache_root / "tool-results"

    if not tool_results_dir.exists():
        print(f"Tool results directory not found: {tool_results_dir}", file=sys.stderr)
        print("Place your tool result files (*.txt) in this directory, or set SORFTIME_CACHE_DIR.", file=sys.stderr)
        sys.exit(1)

    files = [f.name for f in sorted(tool_results_dir.glob("*.txt"))]
    if not files:
        print(f"No .txt files found in {tool_results_dir}", file=sys.stderr)
        sys.exit(1)

    all_products = []
    for fname in files:
        fpath = tool_results_dir / fname
        prods = parse_products_from_file(fpath)
        print(f"Read {fname}: {len(prods)} products", file=sys.stderr)
        all_products.extend(prods)

    print(f"总计: {len(all_products)} 个产品", file=sys.stderr)

    # 去重
    all_products = deduplicate(all_products)
    print(f"去重后: {len(all_products)} 个产品", file=sys.stderr)

    # 过滤
    filtered = filter_products(all_products)
    print(f"过滤后: {len(filtered)} 个产品", file=sys.stderr)

    # 取前50
    top50 = filtered[:50]

    # 输出为JSON
    output = []
    for p in top50:
        output.append({
            "ASIN": p.get("产品ASIN码", ""),
            "标题": p.get("标题", ""),
            "品牌": p.get("品牌", ""),
            "价格": safe_float(p.get("价格"), 0),
            "月销量": safe_int(p.get("月销量"), 0),
            "月销额": safe_float(p.get("月销额"), 0),
            "评论数": safe_int(p.get("评论数"), 0),
            "星级": safe_float(p.get("星级"), 0),
            "重量": safe_float(p.get("重量"), 0),
            "FBA费用": safe_float(p.get("FBA费用"), 0),
            "发货方式": p.get("发货方式", ""),
            "所属大类": p.get("所属大类", ""),
            "所属细分类目": p.get("所属细分类目", "").replace("所属细分类目：", "").replace("\\r\\n", "").strip(),
            "上架时间": p.get("上架时间", ""),
            "评分": round(p.get("_score", 0), 1),
        })

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
