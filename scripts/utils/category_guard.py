"""
China Small/Medium Seller Safe Sourcing — Category Risk Assessment & Filter v2.0

Four-Level Risk System + Seller Profile Support + Enhanced Trap Signals

Risk Levels:
  hard    — Hard Block (extremely high compliance barrier)
  capital — Capital-Intensive Block (high inventory/returns/SKU complexity)
  ops     — Operations-Complex Block (complex certification/logistics/after-sales)
  trap    — Trap Signal (data anomaly/red ocean/suspected violation)
  safe    — Safe

Low Risk Advisory (non-blocking):
  Accessories, eyewear, pet supplies (non-food), basic kitchenware
"""

from typing import Tuple, List, Dict, Any


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
# HARD BLOCK — Extremely high compliance barrier; essentially impossible for small/medium sellers
# ============================================================================
HARD_BLOCK_KEYWORDS = {
    # Food / Beverage
    "食品": "Food/Beverage: FDA compliance, customs quarantine, shelf-life management — not recommended for small sellers",
    "饮料": "Food/Beverage: FDA compliance, customs quarantine, shelf-life management — not recommended for small sellers",
    "零食": "Food/Beverage: FDA compliance, customs quarantine, shelf-life management — not recommended for small sellers",
    "酒水": "Alcohol: Requires liquor license, heavy platform restrictions, complex logistics",
    "茶叶": "Food: Pesticide residue testing, FDA labeling compliance required",
    "咖啡": "Food/Beverage: FDA compliance, shelf-life management, intense competition",
    # Dietary Supplements / Health Products
    "蛋白": "Dietary Supplement/Food: FDA compliance, strict ingredient labeling required",
    "protein": "Dietary Supplement/Food: FDA compliance, strict ingredient labeling required",
    "supplement": "Dietary Supplement: FDA certification, import approval, stringent labeling requirements",
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
    "口罩": "Medical Device/PPE: Strict regulation, platform delisting risk",
    "体温计": "Medical Device: Requires registration certificate, significant post-sale liability",
    "血压计": "Medical Device: Requires registration certificate, significant post-sale liability",
    "助听器": "Medical Device: FDA Class II, extremely high compliance barrier",
    "雾化器": "Medical Device: FDA regulated, complex certification process",
    # Functional Cosmetics
    "化妆品": "Cosmetics: Animal testing ban, ingredient labeling, extensive platform review",
    "护肤品": "Cosmetics: Animal testing ban, ingredient labeling, extensive platform review",
    "美白": "Functional Cosmetics: FDA strictly regulates efficacy claims",
    "祛斑": "Functional Cosmetics: FDA strictly regulates efficacy claims",
    "防晒": "Functional Cosmetics: SPF claims require FDA certification",
    "药妆": "Cosmeceutical (cosmetic/drug borderline): Platform-sensitive, strict review",
    "spf": "Functional Cosmetics: SPF claims require FDA certification",
    "anti-aging": "Functional Cosmetics: FDA strictly regulates efficacy claims",
    "祛痘": "Functional Cosmetics: FDA strictly regulates efficacy claims",
    # Baby Food
    "奶粉": "Baby Food: Strictest regulation, high brand trust barrier",
    "婴儿食品": "Baby Food: Strictest regulation, high brand trust barrier",
    "辅食": "Baby Food: Strictest regulation, high brand trust barrier",
    "formula": "Baby Food: Strictest regulation, high brand trust barrier",
    # Pesticides / Chemicals
    "农药": "Pesticide/Chemical: Requires EPA registration, hazardous material shipping restrictions",
    "杀虫剂": "Pesticide/Chemical: Requires EPA registration, hazardous material shipping restrictions",
    "消毒液": "Chemical: Dual EPA/FDA regulation, platform-sensitive",
    "清洁剂": "Chemical: Ingredient regulation, EPA/platform restrictions",
    "pesticide": "Pesticide/Chemical: Requires EPA registration, hazardous material shipping restrictions",
    "disinfectant": "Chemical: Dual EPA/FDA regulation, platform-sensitive",
    # Alcohol
    "酒精": "Alcohol: Requires liquor license, heavy platform restrictions, complex logistics",
    "wine": "Alcohol: Requires liquor license, age verification, shipping restrictions",
    "beer": "Alcohol: Requires liquor license, interstate shipping restrictions",
    "liquor": "Alcohol: Requires liquor license, platform ban or heavy restrictions",
    "spirits": "Alcohol: Requires liquor license, complex logistics",
}


# ============================================================================
# CAPITAL-INTENSIVE BLOCK — High inventory/returns/SKU complexity; significant capital pressure for small/medium sellers
# ============================================================================
CAPITAL_BLOCK_KEYWORDS = {
    # ===== Apparel (main) =====
    "服装": "Apparel: 20-40% return rate, SKU explosion (sizes x colors), extreme inventory risk",
    "clothing": "Apparel: 20-40% return rate, SKU explosion, extreme inventory risk",
    "apparel": "Apparel: 20-40% return rate, SKU explosion, extreme inventory risk",
    "garment": "Apparel: 20-40% return rate, SKU explosion, extreme inventory risk",
    "wear": "Apparel: 20-40% return rate, SKU explosion, extreme inventory risk",
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
    "dress pants": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    # Dresses / Suits
    "dress": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "gown": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "romper": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "jumpsuit": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "suit": "Apparel: 20-40% return rate, complex sizing, high inventory risk",
    "tuxedo": "Apparel: 20-40% return rate, complex sizing, high inventory risk",
    "formal wear": "Apparel: 20-40% return rate, complex sizing, high inventory risk",
    "evening dress": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "maxi dress": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    "mini dress": "Apparel: 20-40% return rate, many size/color combinations, high inventory risk",
    # Underwear / Sleepwear / Swimwear
    "underwear": "Apparel: 15-30% return rate, many size/color combos, hygiene/try-on issues",
    "lingerie": "Apparel: 20-35% return rate, complex sizing, sensitive after-sales",
    "bra": "Apparel: 25-40% return rate, extremely complex sizing (band + cup), inventory hell",
    "panty": "Apparel: 15-30% return rate, many size/color combos",
    "boxer": "Apparel: 15-30% return rate, many size/color combos",
    "brief": "Apparel: 15-30% return rate, many size/color combos",
    "shapewear": "Apparel: 20-35% return rate, complex sizing",
    "camisole": "Apparel: 20-40% return rate, many size/color combos",
    "slip": "Apparel: 20-40% return rate, many size/color combos",
    "robe": "Apparel: 20-40% return rate, many size/color combos",
    "pajamas": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "sleepwear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "nightgown": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "swimwear": "Apparel: 25-40% return rate, strong seasonality, many size/color combos",
    "bikini": "Apparel: 25-40% return rate, strong seasonality, many size/color combos",
    "swimsuit": "Apparel: 25-40% return rate, strong seasonality, many size/color combos",
    "trunks": "Apparel: 20-40% return rate, many size/color combos",
    "board shorts": "Apparel: 20-40% return rate, many size/color combos",
    "rash guard": "Apparel: 20-40% return rate, many size/color combos",
    "wetsuit": "Apparel: 20-40% return rate, many size/color combos",
    # Active / Outdoor Wear
    "activewear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "sportswear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "athletic wear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "gym wear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "workout clothes": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "yoga pants": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "compression": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "jersey": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "uniform": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "team wear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "cycling wear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    "ski wear": "Apparel: 20-40% return rate, strong seasonality, many size/color combos",
    "hiking wear": "Apparel: 20-40% return rate, many size/color combos, high inventory risk",
    # Baby / Infant Clothing
    "baby clothes": "Apparel: 15-25% return rate, wide size range (0-24M), strong seasonality",
    "infant clothing": "Apparel: 15-25% return rate, wide size range, strong seasonality",
    "onesie": "Apparel: 15-25% return rate, wide size range, strong seasonality",
    "bodysuit": "Apparel: 15-25% return rate, wide size range, strong seasonality",

    # ===== Footwear =====
    "鞋": "Footwear: 25-35% return rate, extensive sizing (US5-13 + half sizes), high inventory risk",
    "shoes": "Footwear: 25-35% return rate, extensive sizing (US5-13 + half sizes), high inventory risk",
    "sneakers": "Footwear: 25-35% return rate, extensive sizing, high inventory risk, intense brand competition",
    "boots": "Footwear: 25-35% return rate, extensive sizing, strong seasonality, high inventory risk",
    "sandals": "Footwear: 25-35% return rate, extensive sizing, strong seasonality, high inventory risk",
    "slippers": "Footwear: 20-30% return rate, extensive sizing, high inventory risk",
    "heels": "Footwear: 30-45% return rate, extensive sizing, comfort complaints common, high return rate",
    "pumps": "Footwear: 30-45% return rate, extensive sizing, comfort complaints common, high return rate",
    "loafers": "Footwear: 25-35% return rate, extensive sizing, high inventory risk",
    "oxfords": "Footwear: 25-35% return rate, extensive sizing, high inventory risk",
    "running shoes": "Footwear: 25-35% return rate, extensive sizing, intense brand competition",
    "athletic shoes": "Footwear: 25-35% return rate, extensive sizing, intense brand competition",
    "tennis shoes": "Footwear: 25-35% return rate, extensive sizing, intense brand competition",
    "hiking boots": "Footwear: 25-35% return rate, extensive sizing, strong seasonality",
    "work boots": "Footwear: 25-35% return rate, extensive sizing, safety certification required",
    "rain boots": "Footwear: 25-35% return rate, extensive sizing, strong seasonality",
    "snow boots": "Footwear: 25-35% return rate, extensive sizing, strong seasonality",
    "flip flops": "Footwear: 20-30% return rate, extensive sizing, strong seasonality",
    "espadrilles": "Footwear: 25-35% return rate, extensive sizing, high inventory risk",
    "ballet flats": "Footwear: 25-35% return rate, extensive sizing, high inventory risk",
    "footwear": "Footwear: 25-35% return rate, extensive sizing, high inventory risk",

    # ===== Bags =====
    "包": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "handbag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "purse": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "backpack": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "tote": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "duffel": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "luggage": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "suitcase": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "briefcase": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "crossbody": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "messenger bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "fanny pack": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "waist pack": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "clutch": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "wristlet": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "diaper bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "gym bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "travel bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "shoulder bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "hobo bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "bucket bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "satchel": "Bags: Fast fashion cycles, high return rates, significant inventory risk",
    "bag": "Bags: Fast fashion cycles, high return rates, significant inventory risk",

    # ===== Jewelry =====
    "珠宝": "Jewelry: Size disputes, material authenticity issues, high returns, counterfeit complaints",
    "首饰": "Jewelry: Size disputes, material authenticity issues, high returns, counterfeit complaints",
    "jewelry": "Jewelry: Size disputes, material authenticity issues, high returns, counterfeit complaints",
    "necklace": "Jewelry: Size disputes, material authenticity issues, high returns",
    "ring": "Jewelry: Size disputes (ring sizing), material authenticity, high returns",
    "watch": "Jewelry/Watches: Complex after-sales, counterfeit complaints, high returns",
    "bracelet": "Jewelry: Size disputes, material authenticity issues, high returns",
    "earring": "Jewelry: Material allergy disputes, high returns",
    "pendant": "Jewelry: Size disputes, material authenticity issues, high returns",
    "anklet": "Jewelry: Size disputes, material authenticity issues, high returns",
    "brooch": "Jewelry: Material authenticity issues, high returns",
    "tiara": "Jewelry: Material authenticity issues, high returns",

    # ===== Wigs / Hair Extensions =====
    "假发": "Wigs/Hair Extensions: Large color/texture variance, extremely high return rate (40-60%), tedious after-sales",
    "wig": "Wigs/Hair Extensions: Large color/texture variance, extremely high return rate (40-60%), tedious after-sales",
    "hair extension": "Wigs/Hair Extensions: Large color/texture variance, extremely high return rate, tedious after-sales",
    "hairpiece": "Wigs/Hair Extensions: Large color/texture variance, extremely high return rate, tedious after-sales",
    "toupee": "Wigs/Hair Extensions: Extremely high return rate, tedious after-sales",
    "weave": "Wigs/Hair Extensions: Extremely high return rate, tedious after-sales",
    "braid": "Wigs/Hair Extensions: Extremely high return rate, tedious after-sales",

    # ===== Large Furniture =====
    "家具": "Large Furniture: Bulky with high shipping costs, extremely expensive FBA fees, difficult returns, damage-prone",
    "sofa": "Large Furniture: Bulky, extremely expensive FBA fees, difficult returns, damage-prone",
    "couch": "Large Furniture: Bulky, extremely expensive FBA fees, difficult returns, damage-prone",
    "bed frame": "Large Furniture: Bulky, complex assembly, difficult returns",
    "dresser": "Large Furniture: Bulky, extremely expensive FBA fees, difficult returns",
    "bookshelf": "Large Furniture: Bulky, damage-prone, difficult returns",
    "wardrobe": "Large Furniture: Bulky, extremely expensive FBA fees, difficult returns",
    "nightstand": "Large Furniture: Bulky, difficult returns",
    "coffee table": "Large Furniture: Bulky, damage-prone, difficult returns",
    "dining table": "Large Furniture: Bulky, damage-prone, difficult returns",
    "ottoman": "Large Furniture: Bulky, difficult returns",
    "recliner": "Large Furniture: Bulky, difficult returns",
    "futon": "Large Furniture: Bulky, difficult returns",

    # ===== Mattress / Pillow / Bedding =====
    "床垫": "Mattress/Pillow: Bulky, cannot resell returns, hygiene concerns",
    "mattress": "Mattress/Pillow: Bulky, cannot resell returns, hygiene concerns",
    "pillow": "Mattress/Pillow: Bulky, post-return hygiene issues, inventory risk",
    "comforter": "Bedding: Bulky, strong seasonality, post-return hygiene issues",
    "duvet": "Bedding: Bulky, strong seasonality, post-return hygiene issues",
    "bedding": "Bedding: Bulky, strong seasonality, post-return hygiene issues",
    "blanket": "Bedding: Bulky, strong seasonality",
    "quilt": "Bedding: Bulky, strong seasonality",

    # ===== Large Appliances =====
    "大型家电": "Large Appliances: Complex certification, high after-sales demands, difficult return logistics, liability risk",
    "refrigerator": "Large Appliances: Bulky, complex certification, high after-sales demands, difficult return logistics",
    "washing machine": "Large Appliances: Bulky, complex certification, high after-sales demands, difficult return logistics",
    "dishwasher": "Large Appliances: Bulky, complex certification, high after-sales demands, difficult return logistics",
    "oven": "Large Appliances: Complex certification, high after-sales demands, difficult return logistics",
    "stove": "Large Appliances: Complex certification, high after-sales demands, difficult return logistics",
    "microwave": "Large Appliances: Complex certification, high after-sales demands",
    "air conditioner": "Large Appliances: Bulky, complex certification, high installation/after-sales demands",
    "water heater": "Large Appliances: Complex certification, high installation demands, significant liability risk",
    "freezer": "Large Appliances: Bulky, complex certification, high after-sales demands",
    "dryer": "Large Appliances: Bulky, complex certification, high after-sales demands",

    # ===== Bicycle / Large Exercise Equipment =====
    "自行车": "Bicycle/Large Exercise Equipment: Bulky, complex assembly, high return costs, many components",
    "bicycle": "Bicycle/Large Exercise Equipment: Bulky, complex assembly, high return costs",
    "treadmill": "Large Exercise Equipment: Bulky, complex assembly, high return costs, demanding after-sales",
    "elliptical": "Large Exercise Equipment: Bulky, complex assembly, high return costs",
    "exercise bike": "Large Exercise Equipment: Bulky, complex assembly, high return costs",
    "rowing machine": "Large Exercise Equipment: Bulky, complex assembly, high return costs",
    "home gym": "Large Exercise Equipment: Bulky, complex assembly, high return costs",
    "weight bench": "Large Exercise Equipment: Bulky, high return costs",
    "power rack": "Large Exercise Equipment: Bulky, high return costs",
}


# ============================================================================
# OPERATIONS-COMPLEX BLOCK — Complex certification/logistics/after-sales; requires professional supply chain capability
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
    "nike": "Branded Product: High authorization barrier, significant counterfeit/infringement risk",
    "apple": "Brand Accessories: MFi certification required, frequent patent/infringement complaints",
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
    "knee pad": "Safety Equipment: Certification required, liability risk",
    "elbow pad": "Safety Equipment: Certification required, liability risk",
    "mouth guard": "Safety Equipment: Certification required, liability risk",
    # BBQ / Outdoor Cooking
    "grill": "Outdoor Cooking: Safety certification, fire hazard, seasonality, FBA restrictions",
    "stove": "Outdoor Cooking: Safety certification, fire hazard, FBA restrictions",
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
    "toy electronic": "Children's Electronic Toys: Dual CPSC/FCC certification, complex compliance",
}


# ============================================================================
# LOW RISK ADVISORY — Non-blocking; surfaced during analysis to flag potential risks
# ============================================================================
LOW_RISK_TIP_KEYWORDS = {
    "hat": "Accessories Advisory: 5-15% return rate, low capital commitment, but monitor style trends",
    "cap": "Accessories Advisory: 5-15% return rate, low capital commitment, but monitor style trends",
    "beanie": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "scarf": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "glove": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "mitten": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "tie": "Accessories Advisory: 5-15% return rate, style trend changes",
    "bow tie": "Accessories Advisory: 5-15% return rate, style trend changes",
    "sock": "Accessories Advisory: 5-15% return rate, many SKUs but low unit price",
    "socks": "Accessories Advisory: 5-15% return rate, many SKUs but low unit price",
    "stocking": "Accessories Advisory: 5-15% return rate, many SKUs but low unit price",
    "stockings": "Accessories Advisory: 5-15% return rate, many SKUs but low unit price",
    "tights": "Accessories Advisory: 5-15% return rate, many SKUs",
    "pantyhose": "Accessories Advisory: 5-15% return rate, many SKUs",
    "belt": "Accessories Advisory: 5-15% return rate, simple sizing",
    "belts": "Accessories Advisory: 5-15% return rate, simple sizing",
    "wallet": "Accessories Advisory: 5-15% return rate, low capital commitment",
    "wallets": "Accessories Advisory: 5-15% return rate, low capital commitment",
    "hat": "Accessories Advisory: 5-15% return rate, low capital commitment, but monitor style trends",
    "hats": "Accessories Advisory: 5-15% return rate, low capital commitment, but monitor style trends",
    "cap": "Accessories Advisory: 5-15% return rate, low capital commitment, but monitor style trends",
    "caps": "Accessories Advisory: 5-15% return rate, low capital commitment, but monitor style trends",
    "beanie": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "beanies": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "scarf": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "scarves": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "glove": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "gloves": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "mitten": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "mittens": "Accessories Advisory: 5-15% return rate, strong seasonality",
    "tie": "Accessories Advisory: 5-15% return rate, style trend changes",
    "ties": "Accessories Advisory: 5-15% return rate, style trend changes",
    "bow tie": "Accessories Advisory: 5-15% return rate, style trend changes",
    "bow ties": "Accessories Advisory: 5-15% return rate, style trend changes",
    "eyewear": "Eyewear Advisory: 10-20% return rate, watch for prescription/style fit issues",
    "sunglasses": "Eyewear Advisory: 10-20% return rate, strong seasonality",
    "reading glasses": "Eyewear Advisory: 10-20% return rate, prescription fit issues",
    "pet supplies": "Pet Supplies Advisory: Ensure non-food items, monitor material safety",
    "pet toy": "Pet Supplies Advisory: Monitor material safety and durability",
    "kitchen utensil": "Basic Kitchenware Advisory: Low return rate, but thin margins and commoditization",
    "cookware": "Basic Kitchenware Advisory: Low return rate, but thin margins and commoditization",
}


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


def evaluate_product(product: dict, profile: dict = None) -> Tuple[bool, str, str, list]:
    """
    Evaluate risk level for a single product

    Args:
        product: Product data dict
        profile: Seller profile config with keys:
            - hard_block: bool  Enable hard block (default True, not recommended to disable)
            - capital_block: bool  Enable capital-intensive block
            - ops_block: bool  Enable operations-complex block
            - trap_filter: bool  Enable trap signal filtering

    Returns: (should_include, reason_if_excluded, risk_level, low_risk_tips)
        risk_level: "hard" | "capital" | "ops" | "trap" | "safe"
        low_risk_tips: list of str, low-risk advisories (non-blocking, informational only)
    """
    # Default profile: strictest small/medium seller safe mode
    if profile is None:
        profile = {
            "hard_block": True,
            "capital_block": True,
            "ops_block": True,
            "trap_filter": True,
        }

    text = _product_text(product)
    low_risk_tips = []

    # 0. Collect low-risk tips (always runs, never blocks)
    for kw, reason in LOW_RISK_TIP_KEYWORDS.items():
        if kw.lower() in text:
            low_risk_tips.append(reason)

    # 1. Hard block (extremely high compliance barrier)
    if profile.get("hard_block", True):
        for kw, reason in HARD_BLOCK_KEYWORDS.items():
            if kw.lower() in text:
                return False, reason, "hard", low_risk_tips

    # 2. Capital block (capital-intensive)
    if profile.get("capital_block", True):
        for kw, reason in CAPITAL_BLOCK_KEYWORDS.items():
            if kw.lower() in text:
                return False, reason, "capital", low_risk_tips

    # 3. Ops block (operations-complex)
    if profile.get("ops_block", True):
        for kw, reason in OPS_BLOCK_KEYWORDS.items():
            if kw.lower() in text:
                return False, reason, "ops", low_risk_tips

    # 4. Trap heuristics
    if profile.get("trap_filter", True):
        price = _to_float(product.get("price", 999))
        reviews = _to_int(product.get("review_count", product.get("Review Count", 99999)))
        sales = _to_int(product.get("monthly_sales_volume", product.get("Sales Volume", 0)))
        rating = _to_float(product.get("rating", product.get("star_rating", product.get("Star Rating", 0))))
        delivery = str(product.get("delivery_type", "")).upper()
        weight = _to_float(product.get("weight", 0))
        fba_fee = _to_float(product.get("fba_fee", 0))
        title = str(product.get("title", "")).lower()
        brand = str(product.get("brand", "")).lower()
        variation_count = _to_int(product.get("variation_count", 0))

        # Certification Trap: electronics/beauty/health categories + low price + low reviews
        if any(k in text for k in ["电子", "美容", "健康", "electronics", "beauty", "health", "cosmetics"]):
            if price < 20 and reviews < 100:
                return False, "Certification Trap: Electronics/Beauty/Health categories require FCC/FDA/UL certification. Low price with few reviews often signals regulatory barrier filtering, not a real opportunity", "trap", low_risk_tips

        # Fake Reviews / Merged Reviews Trap
        if reviews < 100 and sales > 30000 and rating >= 4.9:
            return False, "Fake Reviews / Merged Reviews Trap: Very few reviews but extremely high sales with near-perfect ratings — likely policy violations. Proceed with caution", "trap", low_risk_tips

        # FBM Trap
        if delivery == "FBM" and price < 15:
            return False, "FBM Trap: Low-price products with massive FBM volume suggest FBA restrictions (size/hazmat/margin), not a blue ocean signal", "trap", low_risk_tips

        # Seasonality Trap
        seasonal_kws = ["christmas", "halloween", "valentine", "easter", "thanksgiving",
                        "情人节", "圣诞节", "万圣节"]
        if any(sk in title for sk in seasonal_kws):
            launch_days = _to_int(product.get("上架天数", product.get("launch_days", 999)))
            if launch_days < 60 or sales > 50000:
                return False, "Seasonality Trap: Strong holiday dependency with short product lifecycle — difficult for small sellers to clear inventory", "trap", low_risk_tips

        # Heavy Goods / High FBA Trap
        if weight > 5 or fba_fee > 15:
            return False, f"Heavy Goods / High FBA Trap: Weight {weight}kg / FBA fee ${fba_fee} — slow capital turnover, high freight costs", "trap", low_risk_tips

        # Size Variation Hell Trap (common in apparel/footwear/bags)
        if variation_count > 8:
            if any(k in text for k in ["clothing", "apparel", "shoes", "footwear", "dress", "pants", "shirt"]):
                return False, f"Size Variation Hell Trap: {variation_count} variations — apparel/footwear size SKU explosion, inventory management nightmare for small sellers", "trap", low_risk_tips

        # Phone Accessories Red Ocean Trap
        phone_redsea = ["phone case", "screen protector", "phone cover", "charger cable",
                         "charging cable", "usb cable", "data cable"]
        if any(k in title for k in phone_redsea):
            if reviews > 5000:
                return False, "Phone Accessories Red Ocean Trap: Extremely saturated market, razor-thin margins, patent minefield — virtually no opportunity for new entrants", "trap", low_risk_tips

        # Stationery Low Margin Trap
        stationery_kws = ["stationery", "office supplies", "pen", "pencil", "notebook",
                           "stapler", "paper clip", "binder"]
        if any(k in title for k in stationery_kws):
            if price < 10:
                return False, "Stationery Low Margin Trap: Low ASP, thin margins, severe commoditization — difficult to achieve profitability", "trap", low_risk_tips

    return True, "", "safe", low_risk_tips


def filter_products(products: list, profile: dict = None) -> Tuple[list, list, list]:
    """
    Batch filter product list

    Returns: (included_products, excluded_summaries, all_low_risk_tips)
        excluded_summaries: list of dicts with keys: asin, title, reason, risk_level
        all_low_risk_tips: list of dicts with keys: asin, title, tips
    """
    included = []
    excluded = []
    all_low_risk_tips = []

    for p in products:
        keep, reason, level, tips = evaluate_product(p, profile)
        asin = p.get("ASIN", p.get("asin", p.get("产品ASIN码", "N/A")))
        title = p.get("title", "")[:40]

        if keep:
            included.append(p)
            if tips:
                all_low_risk_tips.append({
                    "asin": asin,
                    "title": title,
                    "tips": tips,
                })
        else:
            excluded.append({
                "asin": asin,
                "title": title,
                "reason": reason,
                "risk_level": level,
            })

    return included, excluded, all_low_risk_tips


def format_exclusion_table(excluded: list) -> str:
    """Format excluded products as a Markdown table"""
    if not excluded:
        return ""

    lines = [
        "## Safety Mode Filter Details",
        "",
        "Currently in **Chinese Small/Medium Seller Safe Sourcing Mode**. The following products have been automatically excluded due to compliance/logistics/capital/operations risks:",
        "",
        "| Risk Level | ASIN | Title | Exclusion Reason |",
        "|------------|------|-------|------------------|",
    ]
    level_map = {
        "hard": "Hard Block",
        "capital": "Capital-Intensive",
        "ops": "Operations-Complex",
        "trap": "Trap Signal",
    }
    for item in excluded:
        level_label = level_map.get(item["risk_level"], item["risk_level"])
        lines.append(f"| {level_label} | {item['asin']} | {item['title']} | {item['reason']} |")

    lines.append("")
    lines.append(f"> Filtered out {len(excluded)} products total. If you have the corresponding qualifications or supply chain capabilities, use `--profile factory` or `--allow-capital` / `--allow-ops` to view full results.")
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
    """When ALL results are filtered out, output a dedicated block page"""
    lines = [
        f"# Blue Ocean Sourcing Report: {keyword or 'Hot Category'} (AMAZON US)",
        "",
        "## Safety Mode Block",
        "",
        "All results under the current keyword/category belong to **high-risk categories** and have been entirely filtered under Chinese Small/Medium Seller Safe Mode.",
        "",
        "**Common High-Risk Reasons**:",
        "- **Hard Block**: Food/Beverage/Supplements/Medical Devices/Cosmetics/Pesticides/Chemicals — extremely high FDA/EPA/platform compliance barrier",
        "- **Capital-Intensive**: Apparel/Footwear/Bags/Jewelry/Wigs/Furniture/Appliances/Bicycles — high return rates, high SKU complexity, bulky items",
        "- **Operations-Complex**: Electronics/Liquids/Flammables/IP Licensed/Auto Parts/Safety Equipment — complex certification, restricted logistics",
        "- **Trap Signal**: Fake reviews/price wars/red ocean/seasonality/heavy goods — data anomalies or extremely saturated markets",
        "",
        "### Recommendations",
        "1. **Try different keywords**: Search for related but safer peripheral products (e.g. use *shaker bottle* instead of *protein shake*).",
        "2. **Switch seller profile**: If you have factory or overseas warehouse capabilities, run `--profile factory` to view full results.",
        "3. **Override filters individually**: If you specifically want to do apparel, run `--allow-capital` to disable capital-intensive filtering.",
        "",
        "### Filter Details",
        "",
        "| Risk Level | ASIN | Title | Exclusion Reason |",
        "|------------|------|-------|------------------|",
    ]
    level_map = {
        "hard": "Hard Block",
        "capital": "Capital-Intensive",
        "ops": "Operations-Complex",
        "trap": "Trap Signal",
    }
    for item in excluded:
        level_label = level_map.get(item["risk_level"], item["risk_level"])
        lines.append(f"| {level_label} | {item['asin']} | {item['title']} | {item['reason']} |")
    lines.append("")
    return "\n".join(lines)
