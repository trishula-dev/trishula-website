# Contributing

Contributions are welcome. This document defines the working agreement: how
changes are proposed, reviewed, and merged, and what the continuous-integration
gates enforce.

## Ground rules

1. **Never commit to `main`.** All work happens on a branch, one change per
   branch, merged via pull request. Branch names follow
   `<type>/<short-description>` with kebab-case — e.g. `fix/shield-fail-open`,
   `feat/ban-policy`, `docs/academy-labs`.
2. **Conventional Commits.** Every commit message follows
   the [specification](https://www.conventionalcommits.org/en/v1.0.0):
   `type(scope): subject`.
   - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `build`, `ci`, `chore`.
   - `scope` is a component: `shield` (eBPF/XDP/TC), `engine` (ladder, CEL,
     rateban), `operator` (CRDs, bundles), `crd`, `telemetry`, `docs`, `ci`.
   - Subject: imperative, lowercase, no trailing period. Body (optional):
     what changed and why; wrap at 72 columns.
3. **Sign everything.** Commits must be GPG- or SSH-signed
   (`git config --global commit.gpgsign true`); releases are
   signed tags — unsigned commits and unsigned tags are
   not merged/published. Verify with `git log --show-signature` / `git tag -v`.
4. **One logical change per PR.** Small, reviewable diffs merge faster.

## Security-sensitive changes

Anything touching the enforcement path, the CRD contract, or the detection
ladder warrants extra care (see [SECURITY.md](SECURITY.md) for the full
posture):

- **Vulnerabilities are not issues.** Follow [SECURITY.md](SECURITY.md) — never
  open a public issue for an unreported vulnerability.
- **Fail-open posture:** changes that alter the default `failureMode` or any
  fail-open/fail-closed behaviour must state the new verdict order and include
  evidence from the differential suite.
- **Detection ladder changes:** any change to stage ordering, scoring, or ban
  escalation must include before/after differential runs against the OWASP CRS
  reference suite.
- **eBPF programs:** keep `bpf/` the only source of kernel-side logic — every
  loader change must keep the CI verifier check green on the oldest supported
  kernel (5.8).

## CI gates

Every pull request runs:

| Check | What it does |
|---|---|
| `go-build` | compiles shield, engine, operator |
| Dependency Review | flags vulnerable or licence-incompatible dependencies |

## Commits and pull requests

- Push your branch and open a PR against `main`; describe the what and the why.
- Link the `TR-XX` issue the change implements; the referenced PRD section in
  the issue body is the design source.
- Releases are signed tags; unpublished work stays on branches.

## Reporting bugs

Open a [GitHub issue](https://github.com/trishula-dev/trishula/issues/new) with
the commit or release tag, deployment shape (kind / cluster), node kernel
version, and the relevant verdict-record excerpt. Security issues never go
here — [SECURITY.md](SECURITY.md) instead.