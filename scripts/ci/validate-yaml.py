#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

import yaml


ROOT = Path(".")


def fail(message: str) -> None:
    print(
        f"ERROR: {message}",
        file=sys.stderr,
    )
    sys.exit(1)


yaml_files = sorted(
    list(ROOT.rglob("*.yaml"))
    + list(ROOT.rglob("*.yml"))
)


if not yaml_files:
    fail("no YAML files found")


print(
    f"Found {len(yaml_files)} YAML file(s)"
)


for path in yaml_files:
    if not path.is_file():
        fail(f"expected YAML file, found directory: {path}")
    print(f"Checking: {path}")

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as f:
            yaml.safe_load(f)

    except yaml.YAMLError as exc:
        fail(
            f"invalid YAML in {path}: {exc}"
        )


print("YAML syntax: PASS")