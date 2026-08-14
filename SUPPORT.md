# Support

## Free Trial

新账号在 [open.sorftime.com](https://open.sorftime.com) 注册可免费体验。手机号注册（支持微信扫码登录），无需信用卡。

## Documentation

- **[SKILL.md](SKILL.md)** — Full skill reference: tools, parameters, gotchas, workflows
- **[README.md](README.md)** — Quick start, use cases, platform coverage
- **[CHANGELOG.md](CHANGELOG.md)** — Version history
- **[references/](references/)** — Methodology cards, tool matrix, seed data

## Getting Help

- **GitHub Issues** — Bug reports and feature requests
- **X (Twitter)** — [@Sorftime](https://x.com)
- **Email** — service@sorftime.com

## FAQ

**Q: Why am I getting "SORFTIME_MCP_KEY not set"?**
Run `python3 scripts/install.py` to configure your key, or set the environment variable manually.

**Q: A tool returns "No relevant data"?**
Check parameter names first — the same concept uses different parameter names across tools (e.g., `amz_site` vs `keyword_support_site` vs `site`). See [SKILL.md § Parameter Traps](SKILL.md).

**Q: How do I sync to the latest tools?**
Run `python3 tests/auto_sync.py` to pull server schema updates.

**Q: Can I use this without an AI agent?**
Yes — all scripts work standalone: `python3 scripts/picker.py --keyword "yoga mat"`.
