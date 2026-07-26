"""
Seller Profile System — 5 preset profiles + per-item custom overrides

Profile tiers (conservative to aggressive):
  newbie  — Beginner Seller, limited capital, strict filtering
  grower  — Growing Seller, accepts moderate risk
  pro     — Professional Seller, has a team, needs trap filtering
  factory — Factory-Direct Seller, supply chain advantage
  brand   — Brand Seller, in-house compliance team
"""

from typing import Dict, Any


# ============================================================================
# Preset Seller Profiles
# ============================================================================
PRESET_PROFILES: Dict[str, Dict[str, Any]] = {
    "newbie": {
        "name": "Beginner Seller",
        "description": "Limited capital, low risk tolerance, lacks overseas warehousing and quick restock capability",
        "hard_block": True,      # Hard Block: ON
        "capital_block": True,   # Capital-Intensive block: ON
        "ops_block": True,       # Operations-Complex block: ON
        "trap_filter": True,     # Trap Filter: ON
        "max_sku_count": 10,     # Recommended max SKU count
        "max_inventory_invest": 5000,  # Recommended max initial capital (USD)
    },
    "grower": {
        "name": "Growing Seller",
        "description": "Has some experience, accepts moderate risk, needs clear risk warnings",
        "hard_block": True,
        "capital_block": True,   # Still blocks capital-intensive, but shows more detailed risk quantification
        "ops_block": False,      # Allows operations-complex (warns but does not block)
        "trap_filter": True,
        "max_sku_count": 30,
        "max_inventory_invest": 15000,
    },
    "pro": {
        "name": "Professional Seller",
        "description": "Has a professional team, familiar with platform rules, needs data-driven decision support",
        "hard_block": True,
        "capital_block": False,  # Allows capital-intensive (warns but does not block)
        "ops_block": False,
        "trap_filter": True,     # Keeps trap filter (not recommended to disable)
        "max_sku_count": 100,
        "max_inventory_invest": 50000,
    },
    "factory": {
        "name": "Factory-Direct Seller",
        "description": "In-house factory or strong supply chain, overseas warehouse capability, accepts high risk for high returns",
        "hard_block": True,
        "capital_block": False,
        "ops_block": False,
        "trap_filter": True,     # Still recommended to keep trap filter
        "max_sku_count": 500,
        "max_inventory_invest": 200000,
    },
    "brand": {
        "name": "Brand Seller",
        "description": "Owns a brand, has compliance team and legal support, needs comprehensive market analysis",
        "hard_block": True,
        "capital_block": False,
        "ops_block": False,
        "trap_filter": True,
        "max_sku_count": 1000,
        "max_inventory_invest": 500000,
    },
}


def get_profile(
    profile_name: str = "newbie",
    allow_hard: bool = False,
    allow_capital: bool = False,
    allow_ops: bool = False,
    skip_traps: bool = False,
) -> Dict[str, Any]:
    """
    Get seller profile configuration

    Args:
        profile_name: Preset profile name
        allow_hard: Allow hard-block categories (⚠️ strongly not recommended unless you have FDA/EPA or similar professional qualifications)
        allow_capital: Allow capital-intensive categories
        allow_ops: Allow operations-complex categories
        skip_traps: Skip trap signal filtering (⚠️ not recommended)

    Returns:
        Merged profile configuration dict
    """
    base = PRESET_PROFILES.get(profile_name, PRESET_PROFILES["newbie"]).copy()

    # Per-item overrides
    if allow_hard:
        base["hard_block"] = False
    if allow_capital:
        base["capital_block"] = False
    if allow_ops:
        base["ops_block"] = False
    if skip_traps:
        base["trap_filter"] = False

    return base


def format_profile_badge(profile: Dict[str, Any]) -> str:
    """Format profile badge for report header"""
    name = profile.get("name", "Unknown")
    desc = profile.get("description", "")

    blocks = []
    if profile.get("hard_block"):
        blocks.append("🔴Hard Block")
    if profile.get("capital_block"):
        blocks.append("🟡Capital-Intensive")
    if profile.get("ops_block"):
        blocks.append("🟠Operations-Complex")
    if profile.get("trap_filter"):
        blocks.append("⚠️Trap Filter")

    block_str = " | ".join(blocks) if blocks else "No filters (⚠️ Dangerous)"

    lines = [
        f"> **Seller Profile: {name}**",
        f"> {desc}",
        f"> Current Filter Rules: {block_str}",
        "",
    ]
    return "\n".join(lines)


def format_profile_help() -> str:
    """Format profile help text"""
    lines = [
        "## Seller Profile Reference",
        "",
        "| Profile | Filter Rules | Best For |",
        "|---------|-------------|----------|",
    ]

    rule_map = {
        (True, True, True, True): "All enabled (strictest)",
        (True, True, False, True): "Hard Block + Capital + Trap",
        (True, False, False, True): "Hard Block + Trap",
        (True, False, False, False): "Hard Block only (loosest)",
    }

    for key, prof in PRESET_PROFILES.items():
        rules = (
            prof["hard_block"],
            prof["capital_block"],
            prof["ops_block"],
            prof["trap_filter"],
        )
        rule_str = rule_map.get(rules, "Custom")
        lines.append(f"| `{key}` | {rule_str} | {prof['name']} |")

    lines.append("")
    lines.append("**Override Switches**:")
    lines.append("- `--allow-capital`: Allow capital-intensive categories (apparel/shoes/bags/furniture, etc.)")
    lines.append("- `--allow-ops`: Allow operations-complex categories (electronics/liquids/auto parts, etc.)")
    lines.append("- `--allow-hard`: Allow hard-block categories (⚠️ not recommended, requires professional qualifications)")
    lines.append("- `--skip-traps`: Skip trap signal filtering (⚠️ not recommended)")
    lines.append("")
    return "\n".join(lines)
