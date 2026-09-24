#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
case "$MODE" in
  on|off) ;;
  fast) ;;
  *)
    echo "Usage: $0 {on|off|fast}" >&2
    exit 2
    ;;
esac
shift
if [[ "$MODE" == "on" || "$MODE" == "off" ]]; then
  SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
  python "$SCRIPT_DIR/install.py" "$MODE"
  exec codex "$@"
fi

# Fast is an explicit whole-session Advanced profile.
exec codex --profile sol-luna-fast "$@"
