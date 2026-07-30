# Contributing to Sorftime Seller Agent

Thanks for your interest in contributing.

## Ways to Contribute

- **Report bugs** — Open an issue with steps to reproduce
- **Suggest features** — Tell us what seller workflow you want automated
- **Improve docs** — Fix typos, add examples, translate
- **Submit PRs** — Bug fixes, new methodology cards, tool integrations
- **Share feedback** — Real seller use cases help us prioritize

## Getting Started

```bash
git clone https://github.com/DannylydST/sorftime-seller-agent.git
cd sorftime-seller-agent
python3 scripts/install.py
python3 scripts/healthcheck.py
```

## Project Structure

```
scripts/          # Python scripts (bridge, picker, analyst, calculator, discover)
  utils/          # Shared utilities (MCP client, cache, formatter)
references/       # Methodology cards, tool matrix, seed data
tests/            # Test suite
assets/           # Images and GIFs
config/           # Configuration templates
```

## Before Submitting

- Run `python3 tests/run_tool_tests.py` to verify MCP connectivity
- Match the existing code style (4-space indent, docstrings)
- Add a Gotcha to `SKILL.md` if you discover a tool behavior quirk
- Update `CHANGELOG.md` under the latest date header

## Need Help?

Open an issue or reach out on X [@Sorftime](https://x.com).
