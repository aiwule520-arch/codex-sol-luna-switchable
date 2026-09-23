# Publishing this repository to GitHub

Recommended repository name:

```text
codex-sol-luna-switchable
```

Recommended description:

```text
Switchable Codex profiles: GPT-6 Sol XHigh orchestrates while GPT-6 Luna handles bounded exploration, implementation, testing, and review.
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

## First public publish

Authenticate GitHub CLI first:

```bash
gh auth status
```

From this repository directory:

```bash
git init
git add .
git commit -m "feat: initial public release"
git branch -M main
gh repo create codex-sol-luna-switchable --public --source=. --remote=origin --push \
  --description "Switchable Codex profiles: GPT-6 Sol XHigh orchestrates while GPT-6 Luna handles bounded exploration, implementation, testing, and review."
```

Then create the first release:

```bash
git tag -a v0.1.0 -m "v0.1.0"
git push origin v0.1.0
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
