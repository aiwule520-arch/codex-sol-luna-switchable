# Release Policy

This repository uses Semantic Versioning tags in the form `vMAJOR.MINOR.PATCH`.

While the project is below `1.0.0`, Codex upstream behavior may still cause compatibility changes between minor releases.

## Version rules

- `PATCH`: documentation corrections, validation fixes, installer fixes, or configuration corrections that preserve the intended routing policy.
- `MINOR`: new profiles, roles, installation behavior, or a material routing-policy change.
- `MAJOR`: breaking layout, incompatible install/uninstall behavior, or a stable public contract change after 1.0.

Release candidates use `vX.Y.Z-rc.N`.

## Release gate

A release may be published only when:

1. The working tree is clean and the release commit is on `main`.
2. `VERSION` matches the tag without the leading `v`.
3. `python scripts/validate.py` passes.
4. `git diff --check` passes.
5. Current Codex model/config assumptions in `docs/COMPATIBILITY.md` have been re-verified.
6. No API keys, tokens, private paths, private repository data, local logs, or user-specific configuration are present.
7. `CHANGELOG.md` contains a section for the release.
8. Release assets are generated from the tagged commit and include SHA-256 checksums.

## Release assets

Every stable release should publish:

- `codex-sol-luna-switchable-vX.Y.Z.zip`
- `SHA256SUMS.txt`

The release ZIP contains installable profiles, agents, installer, launcher, templates, and documentation.

## GitHub Release

Releases are based on Git tags. The included GitHub Actions workflow validates the tag, builds the release ZIP and checksum, then creates the GitHub Release.

Do not manually replace assets after publishing a stable release. Publish a new patch version instead.

## Security fixes

Do not disclose an exploitable security issue in a public issue before a fix is ready. Follow `SECURITY.md`.
