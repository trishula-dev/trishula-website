# Contributing

Contributions are welcome. This document defines the working agreement for
this repo. It states how changes are proposed, reviewed and merged. It states
what the CI gates enforce. This is the docs-only Quarto site repo — no Go, no
appliance stack; the product working agreement lives in the
[trishula repo](https://github.com/trishula-dev/trishula/blob/main/CONTRIBUTING.md).

## The writing standard

This repo follows the org writing standard: ASD-STE100 Simplified Technical
English — one thought per sentence, a 20-word cap, active voice and present
tense. The canonical decision record lives in the main repo:
[docs/adr/0002-asd-ste100-standard.md](https://github.com/trishula-dev/trishula/blob/main/docs/adr/0002-asd-ste100-standard.md).
This repo carries no `docs/adr/` scaffolding; the prose conversion tracks as
issue #39 (TR-WS-4).

## Ground rules

1. **Never commit to `main`.** All work runs on a branch. One change uses one
   branch. The merge runs through a pull request. Branch names follow
   `<type>/<short-description>` in kebab-case, for example `site/nav-order`,
   `docs/badge-row`, `agents/page-refresh`.
2. **Conventional Commits.** Every commit subject follows the
   [specification](https://www.conventionalcommits.org/en/v1.0.0):
   `type: subject` (scope optional on a docs-only site).
   - Standard types: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`,
     `chore`, `perf`, `revert`.
   - Site-surface types (this repo's extension, carried by its history):
     `site` (rendered-page content/layout) and `agents` (the coding-agents
     guide page).
   - Subject: imperative, with no trailing period. Body (optional): what
     changed and why. Body wraps at 72 columns.
   - PR titles follow the same form. Site-track items carry their roadmap id
     in the subject — `site: TR-WS-3 — …` / `docs: TR-42 — …`. Squash merges
     use the PR title as the commit subject
     (`squash_merge_commit_title: COMMIT_OR_PR_TITLE`), so the PR title is
     the commit record. A CI gate checks the form on every PR.
3. **Sign everything.** Commits carry a GPG or SSH signature. The
   `protect-default` ruleset requires signatures (`required_signatures`) —
   an unsigned commit blocks the PR. Verify with `git log --show-signature`.
4. **One logical change per PR.** Small, reviewable diffs merge faster.
5. **Pre-commit runs locally.** Install the hooks once per clone —
   `pre-commit install && pre-commit install --hook-type pre-push`.
   Every `git commit` and `git push` then runs the hook set CI runs.
   pre-commit.ci still gates every PR.

## CI gates

Every pull request runs:

| Check | What it does |
|---|---|
| `site-check` (required) | `quarto render` fails on broken refs; the built HTML must exist |
| `scorecard` | OpenSSF Scorecard (publishes on the default branch) |
| `pr-title-gate` | PR title matches the Conventional Commits form |
| `pre-commit.ci` | the [.pre-commit-config.yaml](.pre-commit-config.yaml) hook set |

The branch ruleset `protect-default` (active) enforces: no deletions, no
non-fast-forward pushes, required signatures, and the PR rule (code-owner
review; extra approval for unattributed changes). Merges to `main` deploy the
site via the Pages workflow (`pages.yml`); the live page is
[trishula.dev](https://trishula.dev).

## Commits and pull requests

- Cut the branch from current `origin/main`. Push and open the PR against
  `main`. The description states what changed, why (the issue) and how the
  rendered output was verified.
- Verify rendered output, not configuration: run `quarto render`, then parse
  the built `_site/*.html` (nav order, labels, TOC anchors) before pushing.
- Merges happen on review. The merge is the maintainer's action.

## Reporting bugs

Open a [GitHub issue](https://github.com/trishula-dev/trishula-website/issues/new)
describing the page, the observed vs expected render, and the commit where
the behaviour appeared. Security issues never go here —
[SECURITY.md](SECURITY.md) is the channel instead.
