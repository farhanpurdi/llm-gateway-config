#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")" &&
  pwd
)"

echo
echo "======================================"
echo "LLM Gateway Config Security Checks"
echo "======================================"

echo
echo "[1/2] Secret scanning"

"$SCRIPT_DIR/scan-secrets.sh"

echo
echo "[2/2] Python dependency audit"

"$SCRIPT_DIR/audit-python.sh" \
  "$SCRIPT_DIR/../ci/requirements.txt"

echo
echo "======================================"
echo "ALL SECURITY CHECKS PASSED"
echo "======================================"