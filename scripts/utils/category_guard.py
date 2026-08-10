"""
China Small/Medium Seller Safe Sourcing — Category Risk Assessment & Advisory v3.0

ARCHITECTURE CHANGE (v3.0):
  The four-tier system is now an ADVISORY layer, not a blocking filter.
  Products are NEVER removed from results. Every product gets a risk level +
  a specific warning, surfaced AFTER output. The seller (or an independent
  review sub-agent) makes the final call — the tool informs, it does not censor.

Risk Levels (severity order):
  hard    — Hard risk (extremely high compliance barrier: food/supplements/medical/etc.)
  capital — Capital-Intensive risk (high inventory/returns/SKU complexity)
  ops     — Operations-Complex risk (certification/logistics/after-sales)
  trap    — Trap Signal (data anomaly/red ocean/suspected violation)
  safe    — Safe

Low Risk Advisory (non-blocking):
  Accessories, eyewear, pet supplies (non-food), basic kitchenware

False-positive mitigation (v3.0):
  - English keywords match on word boundaries (`\b...\b`) so "apple" the brand
    no longer fires on "apple slicer", "wear" no longer fires on "eyewear".
  - Context overrides downgrade known benign combinations:
      non-slip / anti-slip  -> NOT the apparel "slip" block
      SPF/UPF clothing      -> NOT "functional cosmetics"
      alcohol/disinfecting wipes & prep pads -> commodity cleaning, NOT beverage
      apple slicer/corer/peeler -> NOT the Apple brand
      watch band/strap/case -> NOT the jewelry "watch" block
      reusable/cotton face masks -> NOT regulated medical masks
"""

import re
from typing import Tuple, List, Dict, Any

# Severity order (higher = more severe)
RISK_ORDER = {"hard": 5, "capital": 4, "ops": 3, "trap": 2, "safe": 1}


def _to_float(val) -> float:
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _to_int(val) -> int:
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


# ============================================================================
# HARD RISK — extremely high compliance barrier
# ============================================================================
HARD_BLOCK_KEYWORDS = {
    # Food / Beverage
    "食品": "Food/Beverage: FDA compliance, customs quarantine, shelf-life management",
    "饮料": "Food/Beverage: FDA compliance, customs quarantine, shelf-life management",
    "零食": "Food/Beverage: FDA compliance, customs quarantine, shelf-life management",
    "酒水": "Alcohol: Requires liquor license, heavy platform restrictions, complex logistics",
    "茶叶": "Food: Pesticide residue testing, FDA labeling compliance required",
    "咖啡": "Food/Beverage: FDA compliance, shelf-life management, intense competition",
    # Dietary Supplements / Health Products
    "蛋白": "Dietary Supplement/Food: FDA compliance, strict ingredient labeling required",
    "protein": "Dietary Supplement/Food: FDA compliance, strict ingredient labeling required",
    "supplement": "Dietary Supplement: FDA certification, import approval, stringent labeling",
    "代餐": "Dietary Supplement/Food: FDA compliance, strict ingredient labeling required",
    "酵素": "Dietary Supplement/Health Product: Strict FDA and platform review",
    "益生菌": "Dietary Supplement/Health Product: Strict FDA and platform review",
    "维生素": "Health Product: Strict FDA and platform review, high complaint risk",
    "vitamin": "Health Product: Strict FDA and platform review, high complaint risk",
    "保健品": "Health Product: Strict FDA and platform review, high complaint risk",
    "胶原蛋白": "Health Product/Cosmetic: Strict FDA and platform review",
    "鱼油": "Health Product: Strict FDA and platform review",
    "护肝片": "Health Product: Strict FDA and platform review",
    # Medical Devices
    "医疗器械": "Medical Device: Requires 510(k) clearance or registration certificate, extremely high compliance barrier",
    "体温计": "Medical Device: Requires registration certificate, significant post-sale liability",
    "血压计": "Medical Device: Requires registration certificate, significant post-sale liability",
    "助听器": "Medical Device: FDA Class II, extremely high compliance barrier",
    "雾化器": "Medical Device: FDA regulated, complex certification process",
    # Medical Devices (English — closes the bilingual gap)
    "medical thermometer": "Medical Device: Requires registration certificate, significant post-sale liability",
    "digital thermometer": "Medical Device: Requires registration certificate, significant post-sale liability",
    "infrared thermometer": "Medical Device: Requires registration certificate, significant post-sale liability",
    "blood pressure monitor": "Medical Device: Requires registration certificate, significant post-sale liability",
    "hearing aid": "Medical Device: FDA Class II, extremely high compliance barrier",
    "nebulizer": "Medical Device: FDA regulated, complex certification process",
    "glucose monitor": "Medical Device: Requires registration certificate, significant post-sale liability",
    "insulin": "Medical Device/Drug: Prescription-regulated, extreme post-sale liability",
    # Functional Cosmetics
    "化妆品": "Cosmetics: Animal testing ban, ingredient labeling, extensive platform review",
    "护肤品": "Cosmetics: Animal testing ban, ingredient labeling, extensive platform review",
    "美白": "Functional Cosmetics: FDA strictly regulates efficacy claims",
    "祛斑": "Functional Cosmetics: FDA strictly regulates efficacy claims",
    "祛痘": "Functional Cosmetics: FDA strictly regulates efficacy claims",
    "药妆": "Cosmeceutical (cosmetic/drug borderline): Platform-sensitive, strict review",
    # Baby Food
    "奶粉": "Baby Food: Strictest regulation, high brand trust barrier",
    "婴儿食品": "Baby Food: Strictest regulation, high brand trust barrier",
    "辅食": "Baby Food: Strictest regulation, high brand trust barrier",
    "formula": "Baby Food: Strictest regulation, high brand trust barrier",
    # Pesticides / Chemicals
    "农药": "Pesticide/Chemical: Requires EPA registration, hazardous material shipping restrictions",
    "杀虫剂": "Pesticide/Chemical: Requires EPA registration, hazardous material shipping restrictions",
    "pesticide": "Pesticide/Chemical: Requires EPA registration, hazardous material shipping restrictions",
    # Alcohol (beverage context only)
    "wine": "Alcohol: Requires liquor license, age verification, shipping restrictions",
    "beer": "Alcohol: Requires liquor license, interstate shipping restrictions",
    "liquor": "Alcohol: Requires liquor license, platform ban or heavy restrictions",
    "spirits": "Alcohol: Requires liquor license, complex logistics",
    # Medical masks (specific, not fashion masks)
    "n95": "Medical Device/PPE: Strict regulation, platform delisting risk",
    "surgical mask": "Medical Device/PPE: Strict regulation, platform delisting risk",
}


# ============================================================================
# CAPITAL-INTENSIVE — high inventory/returns/SKU complexity
# ============================================================================
CAPITAL_BLOCK_KEYWORDS = {
    # ===== Apparel (main) =====
    "服装": "Apparel: 20-40% return rate, SKU explosion (sizes x colors), extreme inventory risk",
    "clothing": "Apparel: 20-40% return rate, SKU explosion, extreme inventory risk",
    "apparel": "Apparel: 20-40% return rate, SKU explosion, extreme inventory risk",
    "garment": "Apparel: 20-40% return rate, SKU explosion, extreme inventory risk",
    "attire": "Apparel: 20-40% return rate, SKU explosion, extreme inventory risk",
    "outfit": "Apparel: 20-40% return rate, SKU explosion, extreme inventory risk",
    # Tops
    "t-shirt": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "t shirt": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "shirt": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "blouse": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "sweater": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "hoodie": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "sweatshirt": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "jacket": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "coat": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "vest": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "polo": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "tank top": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "crop top": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "cardigan": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "pullover": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    # Bottoms
    "pants": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "trousers": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "jeans": "Apparel: 25-45% return rate, complex sizing (waist x length), high inventory risk",
    "shorts": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "skirt": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "leggings": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "joggers": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "slacks": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "cargo pants": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    # Dresses / Suits
    "dress": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "gown": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "romper": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "jumpsuit": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "suit": "Apparel: 20-40% return rate, complex sizing, high inventory risk",
    "tuxedo": "Apparel: 20-40% return rate, complex sizing, high inventory risk",
    "evening dress": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "maxi dress": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "mini dress": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    # Underwear / Sleepwear / Swimwear
    "underwear": "Apparel: 15-30% return rate, many size/color combos, hygiene/try-on issues",
    "lingerie": "Apparel: 20-35% return rate, complex sizing, sensitive after-sales",
    "bra": "Apparel: 25-40% return rate, extremely complex sizing (band + cup), inventory hell",
    "panty": "Apparel: 15-30% return rate, many size/color combos",
    "boxer": "Apparel: 15-30% return rate, many size/color combos",
    "shapewear": "Apparel: 20-35% return rate, complex sizing",
    "pajamas": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "sleepwear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "nightgown": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "swimwear": "Apparel: 25-40% return rate, strong seasonality, many size/color combos",
    "bikini": "Apparel: 25-40% return rate, strong seasonality, many size/color combos",
    "swimsuit": "Apparel: 25-40% return rate, strong seasonality, many size/color combos",
    # Active / Outdoor Wear
    "activewear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "sportswear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "athletic wear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "gym wear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "compression": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "jersey": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "uniform": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    # Footwear
    "鞋": "Footwear: 25-35% return rate, extensive sizing (US5-13 + half sizes), high inventory risk",
    "shoes": "Footwear: 25-35% return rate, extensive sizing (US5-13 + half sizes), high inventory risk",
    "sneakers": "Footwear: 25-35% return rate, extensive sizing, high inventory risk, intense brand competition",
    "boots": "Footwear: 25-35% return rate, extensive sizing, strong seasonality, high inventory risk",
    "sandals": "Footwear: 25-35% return rate, extensive sizing, strong seasonality, high inventory risk",
    "slippers": "Footwear: 20-30% return rate, extensive sizing, high inventory risk",
    "heels": "Footwear: 30-45% return rate, extensive sizing, comfort complaints common",
    "pumps": "Footwear: 30-45% return rate, extensive sizing, comfort complaints common",
    "loafers": "Footwear: 25-35% return rate, extensive sizing, high inventory risk",
    "running shoes": "Footwear: 25-35% return rate, extensive sizing, intense brand competition",
    "athletic shoes": "Footwear: 25-35% return rate, extensive sizing, intense brand competition",
    "hiking boots": "Footwear: 25-35% return rate, extensive sizing, strong seasonality",
    "work boots": "Footwear: 25-35% return rate, extensive sizing, safety certification required",
    "footwear": "Footwear: 25-35% return rate, extensive sizing, high inventory risk",
    # Bags
    "包": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "handbag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "purse": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "backpack": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "tote": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "luggage": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "suitcase": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "messenger bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "fanny pack": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "diaper bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "travel bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "shoulder bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    # Jewelry
    "珠宝": "Jewelry: Size disputes, material authenticity issues, high returns, counterfeit complaints",
    "首饰": "Jewelry: Size disputes, material authenticity issues, high returns, counterfeit complaints",
    "jewelry": "Jewelry: Size disputes, material authenticity issues, high returns, counterfeit complaints",
    "necklace": "Jewelry: Size disputes, material authenticity issues, high returns",
    "ring": "Jewelry: Size disputes (ring sizing), material authenticity, high returns",
    "bracelet": "Jewelry: Size disputes, material authenticity issues, high returns",
    "earring": "Jewelry: Material allergy disputes, high returns",
    "pendant": "Jewelry: Size disputes, material authenticity issues, high returns",
    # Wigs / Hair Extensions
    "假发": "Wigs/Hair Extensions: Large color/texture variance, extremely high return rate (40-60%), tedious after-sales",
    "wig": "Wigs/Hair Extensions: Large color/texture variance, extremely high return rate, tedious after-sales",
    "hair extension": "Wigs/Hair Extensions: Large color/texture variance, extremely high return rate, tedious after-sales",
    # Large Furniture
    "家具": "Large Furniture: Bulky with high shipping costs, extremely expensive FBA fees, difficult returns, damage-prone",
    "sofa": "Large Furniture: Bulky, extremely expensive FBA fees, difficult returns, damage-prone",
    "couch": "Large Furniture: Bulky, extremely expensive FBA fees, difficult returns, damage-prone",
    "bed frame": "Large Furniture: Bulky, complex assembly, difficult returns",
    "dresser": "Large Furniture: Bulky, extremely expensive FBA fees, difficult returns",
    "bookshelf": "Large Furniture: Bulky, damage-prone, difficult returns",
    "wardrobe": "Large Furniture: Bulky, extremely expensive FBA fees, difficult returns",
    "nightstand": "Large Furniture: Bulky, difficult returns",
    "coffee table": "Large Furniture: Bulky, damage-prone, difficult returns",
    # Mattress / Pillow / Bedding
    "床垫": "Mattress/Pillow: Bulky, cannot resell returns, hygiene concerns",
    "mattress": "Mattress/Pillow: Bulky, cannot resell returns, hygiene concerns",
    "pillow": "Mattress/Pillow: Bulky, post-return hygiene issues, inventory risk",
    "comforter": "Bedding: Bulky, strong seasonality, post-return hygiene issues",
    "duvet": "Bedding: Bulky, strong seasonality, post-return hygiene issues",
    "bedding": "Bedding: Bulky, strong seasonality, post-return hygiene issues",
    # Large Appliances
    "大型家电": "Large Appliances: Complex certification, high after-sales demands, difficult return logistics, liability risk",
    "refrigerator": "Large Appliances: Bulky, complex certification, high after-sales demands, difficult return logistics",
    "washing machine": "Large Appliances: Bulky, complex certification, high after-sales demands, difficult return logistics",
    "dishwasher": "Large Appliances: Bulky, complex certification, high after-sales demands, difficult return logistics",
    "microwave": "Large Appliances: Complex certification, high after-sales demands",
    "air conditioner": "Large Appliances: Bulky, complex certification, high installation/after-sales demands",
    "freezer": "Large Appliances: Bulky, complex certification, high after-sales demands",
    # Bicycle / Large Exercise Equipment
    "自行车": "Bicycle/Large Exercise Equipment: Bulky, complex assembly, high return costs, many components",
    "bicycle": "Bicycle/Large Exercise Equipment: Bulky, complex assembly, high return costs",
    "treadmill": "Large Exercise Equipment: Bulky, complex assembly, high return costs",
    "elliptical": "Large Exercise Equipment: Bulky, complex assembly, high return costs",
    "exercise bike": "Large Exercise Equipment: Bulky, complex assembly, high return costs",
    "rowing machine": "Large Exercise Equipment: Bulky, complex assembly, high return costs",
    "weight bench": "Large Exercise Equipment: Bulky, high return costs",
    # Jewelry/Watches (context-aware — see CONTEXT_OVERRIDES for watch band/strap)
    "watch": "Jewelry/Watches: Complex after-sales, counterfeit complaints, high returns",
}


# ============================================================================
# OPERATIONS-COMPLEX — certification/logistics/after-sales complexity
# ============================================================================
OPS_BLOCK_KEYWORDS = {
    # Electronics / Battery Products
    "充电器": "Electronics: Requires FCC/UL/CE certification, high patent troll risk",
    "电池": "Battery-Containing Product: FBA hazmat restrictions, high certification barrier",
    "移动电源": "Battery-Containing Product: FBA hazmat restrictions, UN38.3 certification required",
    "充电宝": "Battery-Containing Product: FBA hazmat restrictions, UN38.3 certification required",
    "蓝牙耳机": "Electronics: Requires FCC/CE certification, high patent troll risk",
    "无人机": "Electronics: FCC certification, export controls, liability risk",
    # Liquid / Flammable / Pressurized
    "液体": "Liquid/Cream: Heavy FBA restrictions, high breakage rate, expensive freight",
    "精油": "Liquid/Flammable: FBA restrictions, MSDS required",
    "香水": "Liquid/Flammable: FBA restrictions, MSDS required",
    "指甲油": "Liquid/Flammable: FBA restrictions, MSDS required",
    "喷雾": "Pressurized Container/Aerosol: FBA prohibited or restricted, complex logistics",
    "aerosol": "Pressurized Container/Aerosol: FBA prohibited or restricted, complex logistics",
    # IP Licensed / Branded Products
    "迪士尼": "IP Licensed Product: Infringement complaints, extremely high law firm trolling risk",
    "漫威": "IP Licensed Product: Infringement complaints, extremely high law firm trolling risk",
    "任天堂": "IP Licensed Product: Infringement complaints, extremely high law firm trolling risk",
    "联名": "Collaboration/Licensed Product: Complex authorization chain, high infringement risk",
    "licensed": "Licensed Product: Complex authorization chain, high infringement risk",
    "官方授权": "Licensed Product: Complex authorization chain, high infringement risk",
    # Auto Parts
    "汽车配件": "Auto Parts: DOT certification, fitment issues, liability risk, SKU explosion",
    "automotive parts": "Auto Parts: DOT certification, fitment issues, liability risk",
    "car accessories": "Auto Parts: Fitment issues, liability risk",
    "auto parts": "Auto Parts: DOT certification, fitment issues, liability risk",
    "car part": "Auto Parts: DOT certification, fitment issues, liability risk",
    # Safety Equipment
    "helmet": "Safety Equipment: ANSI/EN certification, extreme liability risk",
    "safety goggles": "Safety Equipment: ANSI certification, extreme liability risk",
    "protective gear": "Safety Equipment: High certification requirements, significant liability risk",
    "mouth guard": "Safety Equipment: Certification required, liability risk",
    # BBQ / Outdoor Cooking
    "grill": "Outdoor Cooking: Safety certification, fire hazard, seasonality, FBA restrictions",
    "fire pit": "Outdoor Cooking: Safety certification, fire hazard, FBA restrictions",
    "camping stove": "Outdoor Cooking: Safety certification, fire hazard, FBA restrictions",
    "bbq": "Outdoor Cooking: Safety certification, fire hazard, seasonality",
    "barbecue": "Outdoor Cooking: Safety certification, fire hazard, seasonality",
    # Glass / Fragile
    "mirror": "Glass/Fragile: High breakage rate, expensive packaging, many return disputes",
    "glassware": "Glass/Fragile: High breakage rate, expensive packaging, many return disputes",
    "crystal": "Glass/Fragile: High breakage rate, expensive packaging, many return disputes",
    # Children's Electronic Toys
    "children's electronic toys": "Children's Electronic Toys: Dual CPSC/FCC certification, complex compliance",
    "kids electronic": "Children's Electronic Toys: Dual CPSC/FCC certification, complex compliance",
}


# ============================================================================
# LOW RISK ADVISORY — informational only
# ============================================================================
LOW_RISK_TIP_KEYWORDS = {
    "hat": "Accessories Advisory: 5-15% return rate, low capital commitment, but monitor style trends",
    "cap": "Accessories Advisory: 5-15% return rate, low capital commitment, but monitor style trends",
    "beanie": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "scarf": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "glove": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "sock": "Accessories Advisory: 5-15% return rate, many SKUs but low unit price",
    "socks": "Accessories Advisory: 5-15% return rate, many SKUs but low unit price",
    "belt": "Accessories Advisory: 5-15% return rate, simple sizing",
    "belts": "Accessories Advisory: 5-15% return rate, simple sizing",
    "wallet": "Accessories Advisory: 5-15% return rate, low capital commitment",
    "eyewear": "Eyewear Advisory: 10-20% return rate, watch for prescription/style fit issues",
    "sunglasses": "Eyewear Advisory: 10-20% return rate, strong seasonality",
    "pet supplies": "Pet Supplies Advisory: Ensure non-food items, monitor material safety",
    "pet toy": "Pet Supplies Advisory: Monitor material safety and durability",
    "kitchen utensil": "Basic Kitchenware Advisory: Low return rate, but thin margins and commoditization",
    "cookware": "Basic Kitchenware Advisory: Low return rate, but thin margins and commoditization",
}


# ============================================================================
# CONTEXT OVERRIDES — suppress known false-positive matches
# Map: matched keyword -> list of (benign context regex, downgrade_to_level)
# When a benign context is present, the risk level is downgraded (hard->safe, etc.)
# ============================================================================
CONTEXT_OVERRIDES = {
    # "slip" (apparel slip-dress) — but "non-slip"/"anti-slip" is a functional mat/grip term
    "slip": [("non[ -]?slip|anti[ -]?slip|no slip|nonslip|grip", "safe")],
    # "apple" (Apple brand MFi) — but apple slicer/corer/peeler/cutter is a kitchen fruit tool
    "apple": [("slicer|corer|peeler|cutter|fruit|kitchen", "safe")],
    # "watch" (jewelry) — but watch band/strap/case/buckle is an accessory, not a watch
    "watch": [("band|strap|case|buckle|screen protector|stand", "safe")],
    # "spf" / "防晒" (functional cosmetics) — but UV/UPF apparel is clothing, not sunscreen
    "spf": [("shirt|wear|clothing|jacket|hat|glove|hoodie|fishing|outdoor|sun", "capital")],
    # alcohol/disinfectant cleaning commodities — wipes & pads are consumables, not beverage
    "酒精": [("湿巾|棉片|擦拭|wipe|pad|prep", "safe")],
    "disinfectant": [("wipe|pad|prep|cleanser|cleaner|spray", "safe")],
    # "face mask" / "口罩" (medical device) — but reusable/fashion/cotton masks are apparel
    "口罩": [("棉|布|可水洗|fashion|reusable|cotton|cloth|silk|fabric", "safe")],
    # appliance words used as "…-SAFE" container claims, NOT the appliance itself.
    # "microwave/dishwasher/freezer SAFE" appears on virtually every glass/plastic food
    # container and is NOT a large appliance. Only flag when it IS the appliance.
    "microwave": [("safe|proof|compatible", "safe")],
    "dishwasher": [("safe|proof|compatible|pods|detergent|cleaner", "safe")],
    "freezer": [("safe|proof|compatible|container|storage|bag|organizer|meal|zip|pack", "safe")],
    "air conditioner": [("portable ac", "safe")],
}


# ASCII keywords that need word boundaries (so "apple" brand doesn't fire on "apple slicer")
_WORD_BOUNDARY_KEYS = {"slip", "apple", "watch", "spf", "wear", "hat", "cap", "bag",
                       "suit", "vest", "polo", "ring", "pillow", "tote", "wig",
                       "grill", "mirror", "crystal", "helmet", "glove", "sock",
                       "belt", "shirt", "coat", "boots", "dress", "shorts", "pants",
                       "sweater", "hoodie", "pajamas", "jersey", "bra", "jewelry",
                       "necklace", "bracelet", "earring", "pendant", "backpack",
                       "luggage", "suitcase", "mattress", "comforter", "duvet",
                       "sofa", "couch", "mattress", "fanny pack", "travel bag"}


def _product_text(product: dict) -> str:
    """Extract text from product data for keyword matching (supports both Chinese and English MCP field keys)"""
    parts = []
    for key in ["所属大类", "所属细分类目", "类目", "标题", "品牌", "关键词",
                 "category", "node_name", "top_category", "subcategory",
                 "title", "brand", "keyword", "product_name", "name"]:
        val = product.get(key, "")
        if val:
            parts.append(str(val).lower())
    return " ".join(parts)


def _matches_keyword(keyword: str, text: str) -> bool:
    """Word-boundary-aware keyword match. ASCII keywords get \\b boundaries; CJK match on substring."""
    if re.search(r"[一-鿿]", keyword):
        return keyword.lower() in text
    # English / multi-char: require word boundary (fixes "apple" brand vs "apple slicer", "slip" vs "non-slip" is handled by overrides)
    escaped = re.escape(keyword.lower())
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None


def _downgraded_level(level: str, keyword: str, text: str) -> str:
    """Return downgraded level if a benign context override applies, else the original level."""
    for pattern, target_level in CONTEXT_OVERRIDES.get(keyword, []):
        if re.search(pattern, text):
            return target_level
    return level


def assess_product(product: dict, profile: dict = None) -> Tuple[str, str, list]:
    """
    Non-blocking risk assessment.

    Args:
        product: Product data dict
        profile: Seller profile config (used only to tune warning verbosity; never blocks)

    Returns:
        (risk_level, warning, low_risk_tips)
        risk_level: "hard" | "capital" | "ops" | "trap" | "safe"  (highest severity)
        warning: human-readable specific warning ("" if safe)
        low_risk_tips: list of str (informational, non-blocking)
    """
    text = _product_text(product)
    low_risk_tips = []
    matches = []  # list of (level, keyword, reason)

    # 0. Low-risk advisory tips (always informational)
    for kw, reason in LOW_RISK_TIP_KEYWORDS.items():
        if _matches_keyword(kw, text) and reason not in low_risk_tips:
            low_risk_tips.append(reason)

    # 1. Hard risk matches
    for kw, reason in HARD_BLOCK_KEYWORDS.items():
        if _matches_keyword(kw, text):
            level = _downgraded_level("hard", kw, text)
            matches.append((level, kw, reason))

    # 2. Capital risk matches
    for kw, reason in CAPITAL_BLOCK_KEYWORDS.items():
        if _matches_keyword(kw, text):
            level = _downgraded_level("capital", kw, text)
            matches.append((level, kw, reason))

    # 3. Ops risk matches
    for kw, reason in OPS_BLOCK_KEYWORDS.items():
        if _matches_keyword(kw, text):
            matches.append(("ops", kw, reason))

    # 4. Trap heuristics (data anomalies) — now advisory, not blocking
    price = _to_float(product.get("price", 999))
    reviews = _to_int(product.get("review_count", product.get("Review Count", 99999)))
    sales = _to_int(product.get("monthly_sales_volume", product.get("Sales Volume", 0)))
    rating = _to_float(product.get("rating", product.get("star_rating", product.get("Star Rating", 0))))
    delivery = str(product.get("delivery_type", "")).upper()
    weight = _to_float(product.get("weight", 0))
    fba_fee = _to_float(product.get("fba_fee", 0))
    title = str(product.get("title", "")).lower()
    variation_count = _to_int(product.get("variation_count", 0))

    # Certification Trap: low price + few reviews in regulated-looking categories
    if any(k in text for k in ["电子", "美容", "健康", "electronics", "beauty", "health", "cosmetics"]):
        if price < 20 and reviews < 100:
            matches.append(("trap", "cert_trap",
                "Certification Trap: Electronics/Beauty/Health categories require FCC/FDA/UL certification. Low price with few reviews often signals regulatory barrier filtering — verify certification before sourcing"))

    # Fake Reviews / Merged Reviews Trap
    if reviews < 100 and sales > 30000 and rating >= 4.9:
        matches.append(("trap", "fake_reviews",
            "Fake Reviews / Merged Reviews Trap: Very few reviews but extremely high sales with near-perfect ratings — likely policy violations. Proceed with caution"))

    # FBM Trap
    if delivery == "FBM" and price < 15:
        matches.append(("trap", "fbm",
            "FBM Trap: Low-price products with massive FBM volume suggest FBA restrictions (size/hazmat/margin), not a blue ocean signal"))

    # Seasonality Trap
    seasonal_kws = ["christmas", "halloween", "valentine", "easter", "thanksgiving",
                    "情人节", "圣诞节", "万圣节"]
    if any(sk in title for sk in seasonal_kws):
        launch_days = _to_int(product.get("上架天数", product.get("launch_days", 999)))
        if launch_days < 60 or sales > 50000:
            matches.append(("trap", "seasonal",
                "Seasonality Trap: Strong holiday dependency with short product lifecycle — difficult to clear inventory"))

    # Heavy Goods / High FBA Trap — only when ALSO slow-moving.
    # The API's `weight` is often the bulk/case weight (e.g. a 12-pack of baby wipes
    # reads 6-13kg). High weight with HIGH sales = fast turnover = not a risk.
    # The real risk is heavy + slow (capital sits in freight-bound inventory).
    if (weight > 5 or fba_fee > 15) and sales < 3000:
        matches.append(("trap", "heavy",
            f"Heavy Goods / High FBA Trap: Weight {weight}kg / FBA fee ${fba_fee} with low sales ({sales}/mo) — slow capital turnover, high freight costs"))

    # Size Variation Hell Trap (apparel/footwear/bags)
    if variation_count > 8:
        if any(k in text for k in ["clothing", "apparel", "shoes", "footwear", "dress", "pants", "shirt"]):
            matches.append(("trap", "size_hell",
                f"Size Variation Hell Trap: {variation_count} variations — apparel/footwear size SKU explosion, inventory management nightmare"))

    # Phone Accessories Red Ocean Trap
    phone_redsea = ["phone case", "screen protector", "phone cover", "charger cable",
                     "charging cable", "usb cable", "data cable"]
    if any(k in title for k in phone_redsea):
        if reviews > 5000:
            matches.append(("trap", "phone_redsea",
                "Phone Accessories Red Ocean Trap: Extremely saturated market, razor-thin margins, patent minefield"))

    # Stationery Low Margin Trap
    stationery_kws = ["stationery", "office supplies", "pen", "pencil", "notebook",
                       "stapler", "paper clip", "binder"]
    if any(k in title for k in stationery_kws):
        if price < 10:
            matches.append(("trap", "stationery",
                "Stationery Low Margin Trap: Low ASP, thin margins, severe commoditization"))

    # Pet Oral / Oral-Entry Products (v3.6.1) — oral-entry + hygiene/compliance
    pet_oral_kws = ["dog toothpaste", "pet toothpaste", "dental chew", "dental treats",
                    "dental bones", "pet oral", "dog dental", "pet dental",
                    "宠物牙膏", "狗牙膏", "洁齿骨", "宠物口腔", "口腔清洁"]
    if any(k in text for k in pet_oral_kws):
        matches.append(("trap", "pet_oral",
            "Pet Oral Care Trap: Oral-entry product with hygiene/compliance concerns (dental/health claims). Verify ingredient safety & labeling before sourcing"))

    # Generic Electrically-Powered Devices (v3.6.1) — UL/certification barrier
    electric_kws = ["electric", "电动", "electrical", "corded", "voltage", "110v", "220v",
                    "heating element", "电机", "通电", "电热"]
    if any(k in text for k in electric_kws):
        # Downgrade if clearly low-power/accessory, keep as caution otherwise
        benign = ["non electric", "manual", "hand powered", "不插电", "手动", "无绳充气",
                  "battery-free"]
        if not any(b in text for b in benign):
            matches.append(("ops", "electric",
                "Electrically-Powered Device: UL/FCC/CE certification required — certification barrier & liability risk (newbie account risk)"))

    # ---- Determine highest-severity result ----
    # Drop matches that were downgraded to "safe" by a context override — those are
    # benign by definition and should never surface a warning.
    matches = [m for m in matches if m[0] != "safe"]

    if not matches:
        return "safe", "", low_risk_tips

    # Highest severity level
    best = max(matches, key=lambda m: RISK_ORDER.get(m[0], 0))
    best_level = best[0]
    best_reason = best[2]

    # Include secondary matches in the warning for transparency (dedup by reason)
    other = []
    for level, kw, reason in matches:
        if level != best_level and reason != best_reason and reason not in other:
            other.append(f"[{level.upper()}] {reason}")
    full_warning = best_reason
    if other:
        full_warning = best_reason + " | " + " | ".join(other[:2])

    return best_level, full_warning, low_risk_tips


def evaluate_product(product: dict, profile: dict = None) -> Tuple[bool, str, str, list]:
    """
    [LEGACY COMPAT] Old blocking signature. Kept for external/test code.
    In v3.0 products are NEVER blocked — `should_include` is True unless the
    product is safe, so this shim returns (True, warning, level, tips) always.
    Use `assess_product()` for the new advisory API.
    """
    level, warning, tips = assess_product(product, profile)
    # Legacy callers treated level=="safe" as the only includable set; in advisory
    # mode everything is includable, so always return keep=True + the warning.
    return True, warning, level, tips


def filter_products(products: list, profile: dict = None) -> Tuple[list, list, list]:
    """
    Advisory batch assessment (v3.0): NEVER removes products.

    Returns:
        (annotated_products, risk_warnings, all_low_risk_tips)
        annotated_products: ALL input products, each augmented with:
            _risk_level: str  ("hard"|"capital"|"ops"|"trap"|"safe")
            _risk_warning: str  ("" if safe)
        risk_warnings: list of dicts {asin, title, risk_level, reason} for non-safe products
        all_low_risk_tips: list of dicts {asin, title, tips}
    """
    annotated = []
    risk_warnings = []
    all_low_risk_tips = []

    for p in products:
        level, warning, tips = assess_product(p, profile)
        enriched = dict(p)
        enriched["_risk_level"] = level
        enriched["_risk_warning"] = warning
        annotated.append(enriched)

        asin = p.get("ASIN", p.get("asin", p.get("产品ASIN码", "N/A")))
        title = str(p.get("title", ""))[:40]

        if level != "safe":
            risk_warnings.append({
                "asin": asin,
                "title": title,
                "risk_level": level,
                "reason": warning,
            })
        if tips:
            all_low_risk_tips.append({
                "asin": asin,
                "title": title,
                "tips": tips,
            })

    return annotated, risk_warnings, all_low_risk_tips


def recommend_safe(products: list, profile: dict = None, top_n: int = 5) -> list:
    """
    Return the safest, highest-potential picks — a HIGHLIGHT, not a filter.
    All products remain visible; this just calls out the friendliest subset
    for beginner sellers.
    """
    candidates = []
    for p in products:
        level = p.get("_risk_level", "safe")
        if level == "safe":
            price = _to_float(p.get("price", 0))
            reviews = _to_int(p.get("review_count", p.get("Review Count", 99999)))
            sales = _to_int(p.get("monthly_sales_volume", p.get("Sales Volume", 0)))
            # Beginner-friendly heuristic: moderate price, low reviews, decent sales
            if 10 <= price <= 45 and reviews < 1000 and sales > 500:
                candidates.append(p)
    # Sort by potential/sales as a rough quality signal
    candidates.sort(key=lambda x: _to_float(x.get("potential_index", x.get("monthly_sales_volume", 0))), reverse=True)
    return candidates[:top_n]


def format_risk_warning_table(warnings: list) -> str:
    """Format risk warnings as a Markdown table (advisory — products remain visible)."""
    if not warnings:
        return ""

    lines = [
        "## ⚠️ Risk Advisory — Review Before Committing",
        "",
        "These products remain in the results but carry elevated risk. This is **advisory** — "
        "the final call is yours (or your independent review agent's). Each warning explains the specific concern:",
        "",
        "| Risk Level | ASIN | Title | Risk Warning |",
        "|------------|------|-------|--------------|",
    ]
    level_map = {
        "hard": "🔴 Hard",
        "capital": "🟡 Capital",
        "ops": "🟠 Ops",
        "trap": "⚠️ Trap",
    }
    for item in warnings:
        level_label = level_map.get(item["risk_level"], item["risk_level"])
        reason = str(item["reason"])[:110]
        lines.append(f"| {level_label} | {item['asin']} | {item['title']} | {reason} |")

    hard_count = sum(1 for w in warnings if w["risk_level"] == "hard")
    lines.append("")
    if hard_count:
        lines.append(f"> {len(warnings)} products flagged, {hard_count} with **hard** risk (compliance-heavy). "
                     "If you have the credentials/team for these, they're viable; otherwise filter them out during review. "
                     "An independent review agent can red-team these before you commit.")
    else:
        lines.append(f"> {len(warnings)} products flagged with elevated risk. Review each warning against your "
                     "capabilities before shortlisting.")
    lines.append("")
    return "\n".join(lines)


def format_risk_section(warnings: list, profile: dict = None, show_risks: bool = False) -> str:
    """Risk advisory presentation tuned by profile verbosity (v3.6.0).

    - newbie/grower (risk_verbose=True) or --show-risks: full warning table
    - pro/factory/brand (risk_verbose=False): collapsed footnote + one-line
      proactive hints for hard-risk products. Never hides data, never blocks.
    """
    if not warnings:
        return ""
    verbose = show_risks or (profile or {}).get("risk_verbose", True)
    if verbose:
        return format_risk_warning_table(warnings)

    hard = [w for w in warnings if w["risk_level"] == "hard"]
    other_n = len(warnings) - len(hard)
    lines = []
    # Proactive one-line hints for the highest-severity (hard) products only
    for w in hard:
        lines.append(f"⚠️ `{w['asin']}` {w['title']}: {w['reason'][:80]}")
    if lines:
        lines.append("")
    lines.append(f"🛡️ {len(warnings)} products flagged ({len(hard)} 🔴hard / {other_n} other risk). "
                 "Table collapsed for this profile — use `--show-risks` to expand full warnings.")
    lines.append("")
    return "\n".join(lines)


def format_low_risk_tips_table(tips_list: list) -> str:
    """Format low-risk advisory tips as a Markdown table"""
    if not tips_list:
        return ""

    lines = [
        "### Low Risk Advisory",
        "",
        "The following products fall under **low-risk viable categories**, but still have potential risks worth noting:",
        "",
        "| ASIN | Title | Risk Advisory |",
        "|------|-------|---------------|",
    ]
    for item in tips_list:
        tips_text = "; ".join(item["tips"])
        lines.append(f"| {item['asin']} | {item['title']} | {tips_text} |")

    lines.append("")
    return "\n".join(lines)


def format_all_blocked_page(keyword: str, excluded: list) -> str:
    """[DEPRECATED v3.0] Advisory mode never blocks all products. Kept for backward compat only."""
    return ""


# Short aliases so downstream pickers can migrate incrementally
format_exclusion_table = format_risk_warning_table
