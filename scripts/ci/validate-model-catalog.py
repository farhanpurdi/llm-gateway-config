#!/usr/bin/env python3
"""Validate filename identities, provider metadata and runtime routing together."""
from model_contract import cli


if __name__ == "__main__":
    raise SystemExit(cli("Model catalog validation"))
