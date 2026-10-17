#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(
  cd "$(dirname "${BASH_SOURCE[0]}")" &&
  pwd
)"

REPO_ROOT="$(
  cd "$SCRIPT_DIR/../.." &&
  pwd
)"

cd "$REPO_ROOT"

echo
echo "======================================"
echo "LLM Gateway Config Validation"
echo "======================================"

echo
echo "[1/7] Required repository structure"

required_files=(
  "config/litellm_config.yaml"
  "models/company-fast.yaml"
  "models/company-coding.yaml"
  "providers/openai.yaml"
  "clients/opencode/opencode.jsonc"
  "README.md"
)

for file in "${required_files[@]}"; do

  if [ ! -f "$file" ]; then
    echo "ERROR: missing required file:"
    echo "$file"
    exit 1
  fi

  echo "OK: $file"

done

echo "Repository structure: PASS"


echo
echo "[2/7] YAML syntax"

python3 \
  scripts/ci/validate-yaml.py


echo
echo "[3/7] Logical model catalog and provider consistency"

python3 \
  scripts/ci/validate-model-catalog.py


echo
echo "[4/7] LiteLLM runtime contract"

python3 \
  scripts/ci/validate-runtime-config.py


echo
echo "[5/7] Team policies"

python3 \
  scripts/ci/validate-policies.py


echo
echo "[6/7] Offline contract regression tests"

python3 scripts/ci/test-model-contract.py

echo
echo "[7/7] Git safety"

if git ls-files \
  | grep -qE '(^|/)\.env$'; then

  echo "ERROR: .env is tracked by Git."
  exit 1
fi


if git ls-files \
  | grep -qE \
  '\.(pem|key|p12|pfx|dump|sql)$'; then

  echo "ERROR: sensitive file "
  echo "is tracked by Git."
  exit 1
fi


echo "Git safety: PASS"


echo
echo "======================================"
echo "CONFIG VALIDATION: PASSED"
echo "======================================"
