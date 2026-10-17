#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Keep the historical command while running the same complete checks as CI.
exec "$SCRIPT_DIR/ci/validate.sh" "$@"
