# Publishing this repository to GitHub

Recommended repository name:

```text
codex-sol-luna-switchable
```

Recommended description:

```text
Switchable Codex profiles: keep your selected root model while GPT-6 Luna handles bounded exploration, implementation, testing, and review.
```

Recommended topics:

```text
codex
gpt-6
ai-agents
multi-agent
orchestration
developer-tools
```

## Current release: v0.2.1

Authenticate GitHub CLI first:

```bash
gh auth status
```

From this existing repository directory:

```bash
git status --short --branch
git pull --ff-only
python scripts/validate.py
git diff --check
git add .
git commit -m "fix: make root orchestration fully model-agnostic"
git push origin main
```

Create and push the annotated release tag only after confirming it does not already exist:

```bash
git ls-remote --tags origin
git tag -a v0.2.1 -m "v0.2.1: model-agnostic root cleanup"
git push origin v0.2.1
```

The included `Release` GitHub Actions workflow will validate the tag, build the ZIP and SHA-256 checksum, and create the GitHub Release automatically.

## Repository settings after publish

Recommended GitHub settings:

- Default branch: `main`
- Enable Issues
- Enable private vulnerability reporting
- Enable secret scanning and push protection when available
- Add branch protection/ruleset requiring the `Validate` workflow before merging to `main`
- Require pull requests for changes once other contributors begin participating
- Do not allow force-pushes to `main`

The repository already includes README, LICENSE, CONTRIBUTING, SECURITY, Code of Conduct, issue templates, PR template, release policy, and Actions workflows.
