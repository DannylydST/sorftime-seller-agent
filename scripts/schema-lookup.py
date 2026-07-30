#!/usr/bin/env python3
"""Schema quick-lookup: dump a tool's required params, all params, and enum values.
Usage: python3 scripts/schema-lookup.py <tool_name>
Example: python3 scripts/schema-lookup.py category_keywords
"""
import sys, json, os

TOOL = sys.argv[1] if len(sys.argv) > 1 else None
if not TOOL:
    print("Usage: python3 scripts/schema-lookup.py <tool_name>")
    sys.exit(1)

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(SKILL_DIR, "scripts", "sorftime_bridge.py")

with open(BRIDGE) as f:
    src = f.read()

# Find the tool block
marker = f'"name": "{TOOL}"'
idx = src.find(marker)
if idx == -1:
    print(f"❌ Tool '{TOOL}' not found in sorftime_bridge.py")
    print(f"   Maybe need to sync? Run: python3 tests/auto_sync.py")
    sys.exit(1)

# Extract the full JSON block (from "name" to the closing "}")
block = src[idx:]
depth = 0
end = 0
for i, c in enumerate(block):
    if c == '{': depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0:
            end = i + 1
            break

try:
    raw = "{" + block[:end] + "}"
    schema = json.loads(raw)
except Exception:
    # Fallback: show raw block
    print(block[:end])
    sys.exit(0)

props = schema.get("inputSchema", {}).get("properties", {})
required = schema.get("inputSchema", {}).get("required", [])

print(f"\n{'='*60}")
print(f"  Tool: {TOOL}")
print(f"  Description: {schema.get('description', 'N/A')[:120]}")
print(f"{'='*60}")
print(f"\n📋 REQUIRED parameters: {required if required else '(none — all optional)'}")

print(f"\n📝 ALL parameters:")
for name, spec in props.items():
    req_mark = "🔴 REQUIRED" if name in required else "⚪ optional"
    desc = spec.get("description", "")[:100]
    ptype = spec.get("type", "?")
    enum = spec.get("enum")
    default = spec.get("default")

    extra = []
    if enum:
        sites = [e for e in enum if e != "Unknow"]
        extra.append(f"enum: [{', '.join(sites[:7])}{'...' if len(sites) > 7 else ''}]")
    if default is not None:
        extra.append(f"default: {default}")

    extras = f" ({'; '.join(extra)})" if extra else ""
    print(f"  {req_mark}  {name}: {ptype}{extras}")
    if desc:
        print(f"          {desc}")

print()
