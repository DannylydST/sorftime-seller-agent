# GitHub Maintenance Checklist

> Run through this every time new features, methodology, or content is shipped.

---

## 0. Branch Sync Targets (every release — run `scripts/sync_github.sh`)

| Target | Rule |
|--------|------|
| `origin/channel` | The release branch — every commit lands here first |
| `origin/main` | Default branch = public-facing mirror of channel. Keep fast-forwarded: `git push origin channel:main` |
| `cn/channel` | China mirror repo (`sorftime-seller-agent-cn`) — same commits |
| `cn/main` | Default branch of the cn repo — mirror of channel |

One command after each release: `bash scripts/sync_github.sh` (pushes all 4 targets, prints remote tips — all four must point at the same commit).

If `origin/main` rejects the push (protected branch, non-fast-forward): lift protection → push → restore the exact rules.

```bash
gh api -X DELETE repos/DannylydST/sorftime-seller-agent/branches/main/protection
git push origin channel:main --force-with-lease
gh api -X PUT repos/DannylydST/sorftime-seller-agent/branches/main/protection --input - <<'EOF'
{
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "required_status_checks": null,
  "restrictions": null,
  "enforce_admins": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_linear_history": false,
  "required_conversation_resolution": false,
  "lock_branch": false,
  "block_creations": false,
  "allow_fork_syncing": false
}
EOF
```

Known failure mode (2026-10-27): a release pushed only `origin/channel`; `origin/main` stayed 44 commits behind showing an August README, and the cn repo missed 4 commits — marketplace and GitHub diverged silently. The 4-target script closes this gap.

---

## 1. README.md

| Check | Detail |
|-------|--------|
| ☐ What's New updated | Top section, dated. Link to Wiki pages if relevant |
| ☐ Use Case table | New exclusive features → add a row in "What You Can Do" |
| ☐ Example Conversations | New methodology → add a realistic dialog example |
| ☐ Comparison table | `160+ dimensions + 20 proprietary indices` line — update count if needed |
| ☐ Language audit | `python3 -c "import re; ..."` scan for CJK chars. Wiki + README are **pure English** |

## 2. Repo Metadata (GitHub settings)

| Check | Detail |
|-------|--------|
| ☐ Description | Max **350 chars**. Must mention key differentiators. Update via `gh repo edit` |
| ☐ Counts in description | Tool/endpoint counts must match the current release (e.g. `118 MCP tools · 8 platform endpoints`) |
| ☐ Topics/Tags | Max **20**. When adding a new tag, remove one. Evaluate overlap (e.g. `product-research` vs `amazon-product-research`) |
| ☐ Website/Homepage | Should point to `open.sorftime.com` |

## 3. Wiki

### New feature/methodology → create page + cross-link to ALL of:

| File | Action |
|------|--------|
| ☐ `_Sidebar.md` | Add new page link under the right section |
| ☐ `Home.md` | Add to Quick Links |
| ☐ `Glossary.md` | Add term + ⭐ marker if exclusive |
| ☐ `Exclusive-Methodology.md` | Add section if it's a proprietary feature |
| ☐ `Methodology-Overview.md` | Add card entry if it's a new methodology card |
| ☐ Platform page (Amazon/Shopee/etc.) | Add tool reference if it maps to an MCP tool |
| ☐ Related pages | Add "Related Pages" cross-link at bottom |

### Language rules:

| Scope | Language | Exception |
|-------|---------|-----------|
| Wiki pages | **Pure English** | 1688 certification names (`实力商家`) — keep as functional reference |
| Methodology cards | **Pure English** | — |
| README.md | **Pure English** | — |
| SKILL.md | Bilingual (supports both) | Gotchas + code comments OK in either language |
| test-scenarios.md | Chinese (internal QA) | — |

### Language audit commands:

```bash
# Scan Wiki for CJK (expect only 1688 terms)
python3 -c "
import os, re
p = re.compile(r'[一-鿿]')
for r,d,f in os.walk('/tmp/sorftime-seller-agent.wiki'):
    if '.git' in r: continue
    for fn in f:
        if fn.endswith('.md'):
            for i,l in enumerate(open(os.path.join(r,fn))):
                if p.search(l): print(f'{fn}:{i}: {l.strip()[:120]}')
"

# Same for README + methodology cards
grep -rn '独家\|隐赚\|低价\|中文' README.md references/methodology-cards/
```

## 4. SKILL.md

| Check | Detail |
|-------|--------|
| ☐ Routing table | New trigger phrases → add row |
| ☐ trigger field | Add new trigger keywords |
| ☐ Gotchas section | New tools/params → add note |
| ☐ CLI examples | New `--one-shot` examples if new tool |
| ☐ Parameter traps | New parameter mismatches → add to table |

## 5. Pre-Push Sanity

```bash
# 1. Git status — no unintended files
git status

# 2. Verify no Chinese in English surfaces
<run language audit from section 3>

# 3. Verify cross-links aren't dead
grep -rn '\[.*\](.*\.md)' --include="*.md" wiki/ | while read line; do
  # check each link target exists
done

# 4. Commit with descriptive message
git commit -m "<area>: <what changed>"
```

## 6. Post-Push

| Check | Detail |
|-------|--------|
| ☐ Wiki renders correctly | Open a few pages in browser, check sidebar |
| ☐ Repo description visible | Check github.com repo card |
| ☐ Tags updated | Check repo topics section |
| ☐ What's New dates correct | Don't ship with stale dates |

---

## Common Mistakes (from this session)

| Mistake | Prevention |
|---------|-----------|
| Chinese leaked into README comparison table | Language audit before commit |
| Forgot to update What's New | Add to checklist, not optional |
| Forgot to cross-link Wiki pages | Sidebar + Home + Glossary + Exclusive-Methodology all need updates |
| Repo description over 350 chars | Count before `gh repo edit` |
| Changed wrong skill (seller-agent vs CLI) | Confirm target repo before editing |
| Used Chinese in Gotchas while rest is English | Match the existing language of the section |
