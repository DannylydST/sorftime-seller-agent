"""
MCP client helper: call sorftime-mcp-bridge in --one-shot mode
Stable, direct, no mcporter registration needed
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_SKILL_ROOT = Path(__file__).resolve().parent.parent.parent
BRIDGE_SCRIPT = _SKILL_ROOT / "scripts" / "sorftime_bridge.py"

sys.path.insert(0, str(_SKILL_ROOT / "scripts"))
from utils.env_config import has_key, load_env
from utils.platform_utils import get_venv_python, get_cache_dir

VENV_PYTHON = get_venv_python()

load_env()

# Tools known to be out of current MCP coverage (for graceful degradation)
UNSUPPORTED_TOOLS = {
    "tiktok_product_search",
    "shopee_category_report",
    "temu_category_report",
}

# Deprecated/renamed tools, with automatic remapping
DEPRECATED_TOOL_MAP = {
    "keyword_search": "keyword_search_results",
    "product_keywords": "competitor_product_keywords",
}

GAPS_LOG = get_cache_dir() / "unsupported-requests.log"

# ── Parameter alias mapping: same business concept, different param names across tools ──
# When a caller uses an alias, auto-correct to the correct parameter name in that tool's Schema.
# Format: {alias: [possible correct param names]}, matched against Schema for confirmation.
PARAM_ALIASES = {
    # Search term / keyword
    "search_name":     ["keyword", "category_name", "product_name", "search_name"],
    "keyword":         ["search_name", "category_name", "product_name", "keyword"],
    "category_name":   ["keyword", "search_name", "product_name", "category_name"],
    "product_name":    ["keyword", "search_name", "category_name", "product_name"],
    # Site
    "site":            ["amz_site", "keyword_support_site", "site"],
    "amz_site":        ["site", "keyword_support_site", "amz_site"],
    "keyword_support_site": ["amz_site", "site", "keyword_support_site"],
    # Category ID
    "node_id":         ["top_node", "category_id", "node_id"],
    "category_id":     ["node_id", "top_node", "category_id"],
    "top_node":        ["node_id", "category_id", "top_node"],
    # Product ID
    "asin":            ["product_id", "product_name", "asin"],
    "product_id":      ["asin", "product_name", "product_id"],
    # Trend / time
    "trend_type":      ["product_trend_type", "trend_type"],
    "date":            ["search_time", "start_date", "date"],
    # Shopee/TEMU/TikTok: unified "name"
    "product_name":    ["keyword", "search_name", "category_name", "name", "product_name"],
    "category_name":   ["keyword", "search_name", "product_name", "name", "category_name"],
    # TikTok category search uses bare "name" — common mismatch target
    "name":            ["search_name", "category_name", "keyword", "product_name", "name"],
    "search_name":     ["keyword", "category_name", "product_name", "name", "search_name"],
}

# Lazily loaded tool Schema cache
_SCHEMA_CACHE: dict = None


def _load_schemas() -> dict:
    """Load inputSchema for all tools from schema-store or bridge source"""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is not None:
        return _SCHEMA_CACHE

    # Prefer schema-store (most up-to-date)
    schema_store = get_cache_dir() / "schema-store"
    schemas = {}
    if schema_store.exists():
        for f in sorted(schema_store.glob("schema-*.json"), reverse=True):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                for tool in data.get("tools", []):
                    name = tool.get("name", "")
                    if name and "inputSchema" in tool:
                        schemas[name] = tool["inputSchema"]
                if schemas:
                    break
            except Exception:
                continue

    # Fallback: extract from bridge source code
    if not schemas:
        import re
        with open(BRIDGE_SCRIPT) as f:
            content = f.read()
        for m in re.finditer(r'"name":\s*"(\w+)"', content):
            name = m.group(1)
            start = m.start()
            block = content[start:start + 3000]
            schema_m = re.search(r'"inputSchema":\s*(\{.*?"required":\s*\[[^\]]*\]\s*\}\s*\})', block, re.DOTALL)
            if schema_m:
                try:
                    schemas[name] = json.loads(schema_m.group(1))
                except json.JSONDecodeError:
                    pass

    _SCHEMA_CACHE = schemas
    return schemas


def _validate_and_normalize_params(tool_name: str, arguments: dict) -> dict:
    """Validate parameter names, auto-correct known aliases.

    Returns normalized arguments, or raises RuntimeError if parameters are uncorrectable.
    """
    schemas = _load_schemas()
    schema = schemas.get(tool_name)

    if not schema:
        return arguments  # Unknown tool, skip validation (let server report the error)

    valid_params = set(schema.get("properties", {}).keys())
    required_params = set(schema.get("required", []))

    normalized = {}
    warnings = []

    for key, value in arguments.items():
        if key in valid_params:
            normalized[key] = value
            continue

        # Parameter name not in Schema → attempt correction
        aliases = PARAM_ALIASES.get(key, [])
        corrected = None
        for candidate in aliases:
            if candidate in valid_params and candidate != key:
                corrected = candidate
                break

        if corrected:
            warnings.append(f"Parameter '{key}' → auto-corrected to '{corrected}'")
            normalized[corrected] = value
        else:
            # Cannot correct → keep original name, let server give a clearer error
            warnings.append(
                f"Parameter '{key}' is not in {tool_name} Schema. "
                f"Available params: {sorted(valid_params)}"
            )
            normalized[key] = value

    # Check required parameters
    missing = required_params - set(normalized.keys())
    if missing:
        raise RuntimeError(
            f"Missing required parameters for {tool_name}: {sorted(missing)}. "
            f"Required: {sorted(required_params)}, provided: {sorted(normalized.keys())}"
        )

    if warnings:
        import sys as _sys
        print(f"⚠️  [{tool_name}] Parameter warnings:", file=_sys.stderr)
        for w in warnings:
            print(f"    {w}", file=_sys.stderr)

    return normalized


def _log_gap(tool_name: str, reason: str, arguments: dict):
    """Log requests outside current script design scope, for future capability gap analysis"""
    GAPS_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = json.dumps({
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "reason": reason,
        "arguments": arguments,
    }, ensure_ascii=False)
    with GAPS_LOG.open("a", encoding="utf-8") as f:
        f.write(entry + "\n")


def call_tool(tool_name: str, arguments: dict) -> str:
    """Call a Sorftime MCP tool, return raw text string"""
    # 0. Key pre-check — give onboarding guidance when Key is missing
    if not has_key():
        raise RuntimeError(
            "[SORFTIME_ONBOARDING_REQUIRED] "
            "Sorftime MCP Key not configured.\n"
            "Get it at: https://open-intl.sorftime.com/mcp\n"
            "Config command: python3 scripts/install.py --unattended --key <your-key>\n"
            "Or tell your agent: 'Help me configure Sorftime'."
        )

    # 1. Deprecated tool auto-remapping
    if tool_name in DEPRECATED_TOOL_MAP:
        mapped = DEPRECATED_TOOL_MAP[tool_name]
        _log_gap(tool_name, f"auto_remap_to_{mapped}", arguments)
        tool_name = mapped

    # 2. Out-of-scope tool interception and degradation
    if tool_name in UNSUPPORTED_TOOLS:
        _log_gap(tool_name, "unsupported_tool", arguments)
        raise RuntimeError(
            f"Sorftime MCP does not currently provide '{tool_name}' tool. "
            f"Alternative: try passthrough via `sorftime_raw_call`, or contact the tech team to assess integration priority."
        )

    # 1.5 Parameter name validation and auto-correction
    arguments = _validate_and_normalize_params(tool_name, arguments)

    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    args_json = json.dumps(arguments, ensure_ascii=False)
    cmd = [python, str(BRIDGE_SCRIPT), "--one-shot", tool_name, args_json]
    env = os.environ.copy()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        err = result.stderr or "Unknown error"
        # Onboarding guard: throw machine-readable error when Key is not set
        if "SORFTIME_MCP_KEY" in err and ("not set" in err.lower() or "未设置" in err):
            raise RuntimeError(
                "[SORFTIME_ONBOARDING_REQUIRED] "
                "Sorftime MCP Key not configured. "
                "Provide your Key to the agent (get it at: https://open-intl.sorftime.com/mcp), "
                "or say 'Help me configure Sorftime'."
            )
        # Log unknown errors for drift analysis
        if "Unknown tool" in err or "not found" in err.lower():
            _log_gap(tool_name, "unknown_tool_error", arguments)
        raise RuntimeError(f"Call to {tool_name} failed: {err}")
    return result.stdout.strip()


def _parse_kv_text(raw: str) -> dict:
    """Parse Chinese key-value text returned by some Sorftime tools (e.g. product_detail)"""
    result = {}
    current_key = None
    current_value = []
    for line in raw.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if '：' in line:
            if current_key is not None:
                result[current_key] = '\n'.join(current_value).strip()
            parts = line.split('：', 1)
            current_key = parts[0].strip()
            current_value = [parts[1].strip()]
        else:
            if current_key is not None:
                current_value.append(line.strip())
    if current_key is not None:
        result[current_key] = '\n'.join(current_value).strip()

    # Try to parse values as JSON (e.g. attributes field)
    for k, v in list(result.items()):
        if v.startswith('{') or v.startswith('['):
            try:
                result[k] = json.loads(v)
            except json.JSONDecodeError:
                pass
    return result


def call_tool_json(tool_name: str, arguments: dict):
    """Call a Sorftime MCP tool, auto-extract and return JSON object from the response text"""
    raw = call_tool(tool_name, arguments)
    # Sorftime response text usually contains a description line + \n + JSON
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Find first [ or { position
    for i, ch in enumerate(raw):
        if ch in ("[", "{"):
            try:
                return json.loads(raw[i:])
            except json.JSONDecodeError:
                continue
    # Some tools return Chinese key-value text (e.g. product_detail)
    if '：' in raw:
        parsed = _parse_kv_text(raw)
        if parsed:
            return parsed
    raise RuntimeError(f"Cannot parse JSON from {tool_name} response. Raw response:\n{raw[:500]}")
