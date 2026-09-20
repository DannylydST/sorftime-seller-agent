# Security Notes — sorftime-seller-agent

This file documents every externally-flagged code pattern in this package and why
it is safe. Written for security reviewers and automated analyzers.

## 1. Command execution (subprocess / os.execv) — all argv-list, never shell strings

| Site | What it does | Why it is safe |
|------|--------------|----------------|
| `scripts/install.py` `run()` | Runs pip / venv bootstrap for the explicit install step | argv list of package-internal constants; `shell=False` explicit; `assert isinstance(cmd, list)` guards every call |
| `scripts/healthcheck.py:88/151` | `python -c "<fixed test code>"` subprocess probes | argv list: `[python, "-c", literal]` — the code string is a module-level constant, no user input |
| `scripts/batch_deep_analysis.py` | Batch ASIN analysis | argv list; ASINs pass `validate_asin()` (regex `^[A-Z0-9]{10}$`), sites pass `validate_site()` (`^[A-Z]{2}$`); `shell=False` explicit |
| `scripts/utils/mcp_client.py` | One-shot bridge invocation | argv list `[python, bridge.py, "--one-shot", tool_name, json_args]`; `tool_name` is validated against the tool registry; arguments are JSON, never interpolated into a shell line |
| `scripts/sorftime_bridge.py:47/49` `os.execve/os.execv` | Re-exec into the bundled venv interpreter | The exec target path is derived from `__file__` (package-internal `.venv`), never from user input; argv is `[venv_python, __file__] + sys.argv` |

No call site in this package passes `shell=True`, and no user/model-controlled
string (keyword, category, ASIN, Key) is ever concatenated into a command line.

## 2. Credential flow — one endpoint, whitelisted

- The Sorftime Account-SK is stored only in the user's own environment
  (`~/.sorftime/env` / `SORFTIME_MCP_KEY`), never inside the package.
- The credential is sent to exactly one endpoint: the official
  `https://mcp.sorftime.com` (declared in SKILL.md). This is enforced in code by
  `ALLOWED_OUTBOUND_HOSTS = ("mcp.sorftime.com",)` and `_assert_official_url()`
  in `scripts/sorftime_bridge.py` — any credential-bearing request to a
  non-whitelisted host raises immediately.
- Requests carry only the MCP JSON-RPC payload (tool name + arguments of the
  user's query). No telemetry, analytics, or channel endpoint exists in this
  package.

## 3. File writes — inside declared roots

- Config write: `~/.sorftime/env` (single fixed path).
- Workflow outputs go under `${SORFTIME_OUTPUT_DIR:-~/Documents/sorftime}/`;
  category/platform components are slugified (see references/workflows/
  closed-loop-selection.md "Output directory safety") and the resolved path is
  prefix-checked against the declared root.
- `scripts/stage_formatter.py` opens exactly the file path the operator passed
  on its own CLI (a local formatting utility).

## 4. Notes on benign flagged strings

- `"top1_share_label"` in `sorftime_bridge.py` is a sample field label in a
  tool's example arguments — not a credential.
- `SORFTIME_CACHE_DIR` / `CLAUDE_CODE` environment reads are a cache-directory
  override and a host-environment probe respectively — not credentials.
- `list_tools()` is the standard MCP protocol handshake for advertising the
  tool catalog to the connecting agent.
