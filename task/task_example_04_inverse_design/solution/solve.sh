#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$HERE/generate_answer.py" "$@"
