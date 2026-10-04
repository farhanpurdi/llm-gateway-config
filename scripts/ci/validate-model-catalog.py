#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

import yaml


MODEL_DIR = Path("models")

REQUIRED_MODELS = {
    "company-fast",
    "company-coding",
}


def fail(message: str) -> None:
    print(
        f"ERROR: {message}",
        file=sys.stderr,
    )
    sys.exit(1)


if not MODEL_DIR.exists():
    fail("models directory not found")


model_files = sorted(
    MODEL_DIR.glob("*.yaml")
)


if not model_files:
    fail("no logical model definitions found")


logical_names: list[str] = []


for path in model_files:
    print(f"Validating model: {path}")

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as f:
            model = yaml.safe_load(f)

    except yaml.YAMLError as exc:
        fail(
            f"{path}: invalid YAML: {exc}"
        )

    if not isinstance(model, dict):
        fail(
            f"{path}: model definition "
            "must be a YAML object"
        )

    #
    # Logical model identity comes
    # from the filename.
    #
    logical_name = path.stem

    if not logical_name:
        fail(
            f"{path}: invalid model filename"
        )

    logical_names.append(
        logical_name
    )


duplicates = {
    name
    for name in logical_names
    if logical_names.count(name) > 1
}


if duplicates:
    fail(
        "duplicate logical model(s): "
        + ", ".join(
            sorted(duplicates)
        )
    )


missing = (
    REQUIRED_MODELS
    - set(logical_names)
)


if missing:
    fail(
        "required logical model(s) missing: "
        + ", ".join(
            sorted(missing)
        )
    )


print()
print("Logical models:")

for model in sorted(logical_names):
    print(f"  - {model}")


print()
print("Model catalog validation: PASS")