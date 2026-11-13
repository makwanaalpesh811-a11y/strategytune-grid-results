---
name: github-account-audit
description: "Audit a GitHub account: inventory, secrets, CI, security."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, audit, security, ci, quality, repos]
    category: software-development
    related_skills: [github, requesting-code-review]
---

# GitHub Account Audit

Six-phase audit of a whole GitHub account (or a set of local repos) for
quality, broken references, security leaks, and CI coverage. Produces a
honest quality score and a report — never fabricates results, never
silently deletes anything.

## When to Use

- User asks for a full account/profile quality audit
- User wants to know what's broken before shipping many repos
- Multi-repo hygiene pass after a big batch push
- User asks "does my account look professional?"

**Don't use for:** reviewing one PR (`requesting-code-review`), one skill
fix (edit it in place), or single-repo CI setup (just add the workflow).

## Preservation Rules (HARD — apply to every phase)

These are the standing rules of this class of task. Breaking any one of
them is worse than stopping and asking.

- **Never delete** a repository, skill, SKILL.md, script, reference,
  template, README, or documentation file as part of the audit.
- **Never merge or rename** without first listing the proposed changes
  and getting explicit approval.
- **Never force-push** or rewrite history.
- **Never expose** credentials in chat or in audit artifacts. Report
  secret findings by path + line + pattern name, not by value.
- If a file is risky/outdated, **improve in place** or **document the
  issue** — do not delete.
- Treat all documentation-only skills as legitimate content; label them
  `documentation-only` if they cannot be executed, don't remove them.

## Phase Overview

Seven phases in order. Skip none; a phase that produces no findings is still
a phase — write `PASS` and move on.

| Phase | Output |
|---|---|
| 0. Authoritative pre-flight | Live-API count + local-repo diff before any count is claimed |
| 1. Inventory | `INVENTORY.json` — every repo, skill, script, ref, template, test, CI file |
| 2. Broken refs | Fixed + re-counted; user-home paths like `~/foo/.lock` are **runtime**, not broken |
| 3. SKILL.md validation | `PHASE3_VALIDATION.json` — YAML frontmatter + required sections |
| 4. Tests | `run_tests.py` + `PHASE4_TESTS.json` — Python syntax, YAML, links, secrets, dangerous cmds |
| 5. CI/CD | `.github/workflows/audit.yml` added to every repo |
| 6. Security | `SECURITY.md`, `.gitignore`, `CONTRIBUTING.md` in every repo |
| 7. Final consistency pass | Reconcile every number across all artifacts against authoritative sources |

At the end: `AUDIT_REPORT.md` summarizing before/after and remaining gaps.

## Procedure

### Phase 0 — Authoritative pre-flight (REQUIRED before Phase 1)

`gh repo list` and any cached listing may be stale — it reflects a previous
`gh` call, not the current GitHub state. A stale count will contaminate
every downstream artifact (README badges, scorecard math, reconciliation
report, inventory JSON). Query the live REST API FIRST and save the
response; treat it as the source of truth for repo count.

```bash
curl -s -H "Authorization: Bearer $GH_TOKEN" \
  "https://api.github.com/users/$USER/repos?per_page=100&sort=updated" \
  > repos.json
python3 -c "import json; print(len(json.load(open('repos.json'))))"
```

Do the same for local repos:

```bash
ls -d ~/hermes-repos/*/ | grep -v PENDING | wc -l
```

Then compute the set difference explicitly. `gh repo list` reports repos
you have pushed and can see via `gh`'s cache; the REST API reports what
is actually live right now. If they differ, the REST API wins — the
difference is often a renamed/deleted/transferred repo or a push that
landed under a different account.

Persist the authoritative count in a top-level `VERIFIED_COUNTS.md`
file, referenced by every downstream artifact. If the live API and the
local cache disagree on the repo count, that disagreement is itself a
finding — document both numbers, not the stale one.

### Phase 7 — Final consistency pass (REQUIRED before declaring done)

Only the final phase reconciles numbers across artifacts. Do it after
all other phases have written their outputs. For each metric claim
repeated across `README.md`, `AUDIT_REPORT.md`, `SCORECARD.md`,
`RECONCILIATION_REPORT.md`, `TEST_REPORT.md`, `SKILL_INVENTORY.md`,
`IMPROVEMENT_PLAN.md`, and `INVENTORY.json`, verify against the
authoritative source and correct in place.

Recompute from scratch (do not trust the intermediate numbers):

```bash
# Repos
python3 -c "import json; print('repos:', len(json.load(open('repos.json'))))"
# Files
for f in SKILL.md "*.py" "*.sh" "*.js" "test_*.py" SECURITY.md CONTRIBUTING.md LICENSE .gitignore README.md; do
  echo "$f: $(find ~/hermes-repos -name "$f" -not -path '*/_audit_tmp/*' -not -path '*/__pycache__/*' | wc -l)"
done
```

Then re-execute every test suite claimed as passing. If any test suite
fails or has been un-run since the last claim, remove the claim.

**Test-count discipline:** count only tests actually executed in this
session, not "planned" tests, not tests copied from another repo,
not tests that fail on the runtime (e.g. missing native deps). List
failing tests separately in the report — never include them in a pass
total.

**Split ambiguous file counts.** When a filename matches multiple
semantic buckets, report the split explicitly rather than a single
total. Common cases:
- `.py` files: split into `skill scripts (in skills/*/scripts/)`,
  `test scripts (in tests/)`, `top-level tools (run_tests.py etc.)`.
- `LICENSE`: split into `repo-level (one per repo root)` and
  `nested (in skills/*/LICENSE)` — nested files come from upstream
  skill sources and shouldn't be counted as "repos with a LICENSE".
- `README.md`: same split — repo root vs skill-subtree.

Only after every artifact shows the same numbers, write the final
"verified counts" section at the top of `AUDIT_REPORT.md`.

### Phase 1 — Inventory

Walk every repo, count skills/scripts/references/templates/tests/READMEs/
LICENSEs/CI workflows and total size. Walk with `os.walk`, exclude
`.git`, `node_modules`, `__pycache__`, `.venv`, `venv`. For every
`SKILL.md`, record the file. Also count `LICENSE` files specifically —
its absence is a real finding.

Output: `INVENTORY.json` with `{"repos": {...}, "stats": {...}}`.

### Phase 2 — Broken references

For every `.md` file, extract markdown links `[text](path)` and skip
`http(s)://`, `mailto:`, `#`. Skip anchors (`link.split("#")[0]`).
Resolve relative to the containing dir. If missing, it is a candidate
broken ref.

**False-positive filters (apply before flagging):**

- Any path starting with `~/` — user home, runtime-resolved
- Any line containing `\n` or starting with `cd `, `bash`, `python `, `MAPS=` — it's a shell block, not a link
- Anything containing `<` (template placeholder like `<name>.xlsx`)
- Anything inside fenced code blocks (Python samples like `FX_DISPATCH[sec](r, f, t)` get parsed as links — that's a parser false positive, not a broken ref)
- `[alt](url)` where `url` is literal text in a markdown doc explaining image syntax

After filters, **fix real broken refs by syncing** from a canonical
source if one exists (e.g. local `~/.hermes/skills/<...>/references/`
often holds the truth that the repo is missing). Never invent fake
references — if the file genuinely doesn't exist, document it.

### Phase 3 — SKILL.md validation

For each SKILL.md:

- Starts with `---\n` at byte 0
- Has closing `\n---\n` before body
- Parses as YAML mapping (use `yaml.safe_load` if available; fall back to
  line-splitting on `:` for the top-level keys when pyyaml is absent)
- Required keys: `name`, `description`
- Recommended keys: `version`, `author`, `license`, `platforms`

Save `PHASE3_VALIDATION.json` with per-file issue lists.

**Section-name reality:** real skills use varied section names
(`When to Use`, `Pitfalls`, `Verification`, `Workflow`, `Quick
Reference`, `How to Run`). Don't hard-fail on missing `## Usage` — it
may exist as `## How to Run`. Report missing-section counts as
informational, not as pass/fail.

### Phase 4 — Tests (`run_tests.py`)

Write a reusable `run_tests.py` in the repos root. It must do exactly
these five checks — nothing that calls a real API, opens a network
socket, logs in, or uses real credentials:

1. **Python syntax** — `ast.parse()` every `.py` (no execution).
2. **YAML frontmatter** — same as Phase 3.
3. **Local markdown links** — same filters as Phase 2.
4. **Secrets scan** — regex for `AKIA[A-Z0-9]{16}`, `ghp_[A-Za-z0-9_]{36}`, `github_pat_[A-Za-z0-9_]{22,}`, `-----BEGIN .*PRIVATE KEY-----`, `[0-9]{8,10}:[A-Za-z0-9_-]{35}` (Telegram bot), `xox[baprs]-...`, `AIza[0-9A-Za-z-]{35}`, `sk_live_[0-9a-zA-Z]{24}`. Classify each hit as example vs real based on surrounding line containing `example`, `sample`, `your_key`, `your_token`, `dummy`, `placeholder`, `fake`, `test_`, `xxx`, `your-api`, `not your`, `redacted`, `not a screenshot`, `***`.
5. **Dangerous command review** — `curl ... | bash`, `wget ... | sh`, `chmod 777`, `eval "`, `shell=True`, `rm -rf /` or `rm -rf ~`, `os.system(`. Report as informational with pattern name and context line. Classify: `curl | bash` from official trusted domains is a **documented installer**, not a finding.

Never invoke anything from step 5. The test runner is static-only.

### Phase 5 — CI/CD

Add `.github/workflows/audit.yml` to every repo. Job set:

- **Python syntax validation** (`python3 -m py_compile` over `find . -name '*.py'`)
- **SKILL.md YAML frontmatter** validation (pip install pyyaml, parse each SKILL.md, check `name`+`description`)
- **Markdown local link check** (same filters as Phase 2)
- **Gitleaks secret scanning** (`uses: gitleaks/gitleaks-action@v2`, `continue-on-error: true`)

Triggers: `push` and `pull_request` on `main`/`master`.

Place the workflow under a shared `/_shared/` staging dir first, then
copy into each repo — one file, all repos. Remove `_shared/` after
push.

### Phase 6 — Security hardening

Three files in every repo:

- **`SECURITY.md`** — reporting channel, credential policy (no secrets committed, all read from local paths like `~/.<name>_env`), dangerous-command review notes, safe-by-design disclaimers (Delta MCP read-only, signal bot paper-trade only), license line. Use a **placeholder** email — never put a real email into a public SECURITY.md.
- **`.gitignore`** — blocks `.env`, `*.env`, `*.token`, `*.key`, `*.pem`, `*.p12`, `id_rsa*`, `*credentials*`, `*_token.json`, `gh_token*`, `*.csv`/`*.parquet`/`*.db`, `*.tar`/`*.zip`, `__pycache__/`, `.venv/`, `node_modules/`. Add `!*.env.example` so example files still ship.
- **`CONTRIBUTING.md`** — skill-structure guide (SKILL.md frontmatter shape, required sections, local test command).

### Final report — `AUDIT_REPORT.md`

Structure: score table (before/after per metric), per-phase summary
with concrete numbers, list of new files added, list of what was NOT
fixed with reasoning (section-name variety, missing recommended
frontmatter fields, no live pytest, etc.), preservation-policy check
(no deletions, no force-push, no secrets exposed).

## Pitfalls

- **`gh repo list` is a cache, not a source of truth.** Always query
  the REST API before claiming a repo count. The `gh` CLI reads from
  its own index, which can be stale after renames, deletes, or
  transfers — and a stale count that lands in the README badge and the
  scorecard has to be walked back across every artifact.
- **Only count tests that were actually executed.** A pass total that
  includes planned tests, copied tests, or tests that error on the
  current runtime (missing native deps, etc.) is a lie. Failures
  belong in a separate bucket — never blend them into a green pass
  count.
- **Watch for duplicate YAML frontmatter blocks.** A bulk-edit script
  that prepends frontmatter will run twice on the same file if
  re-invoked, producing two `---\n...\n---` blocks stacked at the top.
  Validate catches this because the regex only matches the first
  block, but the second block appears as body content and looks like
  stray text. Detect by counting `^---\s*$` lines: a well-formed
  SKILL.md has exactly two (opening + closing); more means duplicates.
  Fix by keeping only the first block.
- **Never count nested LICENSE/README files as repo-level artifacts.**
  `skills/*/LICENSE` and `skills/*/README.md` come from upstream skill
  sources and reflect upstream licensing, not the current repo's
  licensing. Report repo-level and nested separately; use repo-level
  for the "X repos with a LICENSE" claim.
- **The `~/.` filter is essential.** Without it, 50% of reported broken
  links will be false positives — the docs reference `~/paper_trade/.lock`
or `~/.hermes/skills/foo/bar.py` which is a runtime path, not a repo
  file. Filter BEFORE flagging.
- **Fenced code blocks produce fake links.** Markdown parsers see
  `[alt](url)` inside a code sample explaining markdown syntax, or
  `FX_DISPATCH[sec](r, f, t)` inside Python code, and report them as
  links. Filter these out — inspect a sample of the "broken" links
  before treating them as findings.
- **`author: Hermes Agent` alone is a violation.** Credit the human
  first if known (e.g. `Alpesh Makwana, Hermes Agent`). If the audit
  adds new SKILL.md content, follow the `hermes-agent-skill-authoring`
  skill's author rules.
- **Never hardcode real emails or handles in SECURITY.md.** Use a
  placeholder like `security@owner.invalid` and document the reporting
  process. Real contact routes should be managed via GitHub's private
  security contact feature.
- **Don't count `curl | bash` in SECURITY.md as a real dangerous
  command finding.** It's the SECURITY.md documenting the review policy.
  The regex will match its own docs; that's a scanner artifact, not a
  repo vulnerability.
- **Sync from a canonical source before declaring a ref missing.** If
  the user has local skills at `~/.hermes/skills/<cat>/<name>/` that
  the repo `hermes-repos/<repo>/skills/<name>/` was built from, the
  local tree often has the missing `references/` and `scripts/` that
  the repo copy never received. `find ~/.hermes/skills -type d -name
  references` then mirror into the repo.
- **Never run live pytest/CI against real APIs during the audit.** The
  test runner must be static-only: `ast.parse` for Python, YAML
  parse for frontmatter, regex for links and secrets. The whole point
  of Phase 4 is proving things without side effects.
- **Rate limit repo creation on new GitHub accounts.** Batch pushes
  hit a wall after ~20-25 repo creates per hour. Space pushes with
  `sleep 1` between, and on 403 rate-limit, save the remaining list to
  a `PENDING_UPLOADS.md` file (with a resume command) and wait for the
  window reset — never retry aggressively.
- **GitHub pin API returns 404 for many users.** Profile pinning has to
  be done in the UI; don't claim API-based pinning worked when the
  response is 404.
- **Avatar upload via API often returns 422.** Same story — manual
  only. Prepare the avatar at the right size (square, ≥ 200px) and
  save to a documented path for the user to upload by hand.
- **Don't touch git history.** Audit is additive: new files, new
  commits. Never `git rebase`, `git reset --hard`, or `--force`.

## Verification

- Phase 0 ran: live-API repo count captured and stored; stale-cache
  discrepancies documented if any.
- All seven phase outputs exist on disk (`INVENTORY.json`,
  `PHASE3_VALIDATION.json`, `PHASE4_TESTS.json`, `PHASE6_SECURITY.json`,
  `run_tests.py`, `VERIFIED_COUNTS.md`, `AUDIT_REPORT.md`).
- Phase 7 reconciliation done: every metric number in every artifact
  matches the same authoritative source.
- `run_tests.py` runs clean: 0 Python syntax errors, 0 SKILL.md
  frontmatter errors, secret findings classified (real vs example),
  dangerous-cmd findings classified (installer vs real risk).
- Every test counted as "passing" was actually executed in this
  session and shown passing; failing tests are listed separately,
  not folded into the pass total.
- Ambiguous file counts (`.py`, `LICENSE`, `README.md`) are split
  into their component buckets and each split is documented.
- Every repo has `.github/workflows/audit.yml`, `SECURITY.md`,
  `CONTRIBUTING.md`, `.gitignore`.
- Every `git push` in the batch returned `master -> master` (not
  rejected, not rate-limited).
- No repo, skill, or SKILL.md was deleted; `git log` shows only
  additive commits.
- Zero real secrets appear in the audit artifacts or the final report.

## Output language

Match the user's language. Default English for the audit files
themselves (they're artifacts that may be read by others), Hinglish or
English for the chat summary.
