#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(
    cd "$(dirname "${BASH_SOURCE[0]}")" &&
    pwd
)"

ROOT_DIR="$(
    cd "$SCRIPT_DIR/.." &&
    pwd
)"

cd "$ROOT_DIR"

echo "======================================"
echo "LLM Gateway Config Validation"
echo "======================================"

required_files=(
    "config/litellm_config.yaml"
    "models/company-fast.yaml"
    "models/company-coding.yaml"
    "providers/openai.yaml"
    "docs/model-catalog.md"
)

echo
echo "[1/2] Repository structure"

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: missing required file:"
        echo "$file"
        exit 1
    fi

    echo "OK: $file"
done

echo
echo "[2/2] Team policies"

python3 \
    "$SCRIPT_DIR/validate-policies.py"

echo
echo "======================================"
echo "CONFIG VALIDATION: PASSED"
echo "======================================"