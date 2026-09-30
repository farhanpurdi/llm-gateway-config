#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CONFIG_FILE="$ROOT_DIR/config/litellm_config.yaml"

echo "======================================"
echo "Validating LLM Gateway configuration"
echo "======================================"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: LiteLLM config not found:"
    echo "$CONFIG_FILE"
    exit 1
fi

echo "[OK] LiteLLM config exists"

required_files=(
    "$ROOT_DIR/models/company-fast.yaml"
    "$ROOT_DIR/models/company-coding.yaml"
    "$ROOT_DIR/providers/openai.yaml"
    "$ROOT_DIR/docs/model-catalog.md"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Missing required file:"
        echo "$file"
        exit 1
    fi

    echo "[OK] $(basename "$file")"
done

echo
echo "Configuration structure is valid."