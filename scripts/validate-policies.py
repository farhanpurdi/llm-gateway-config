#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

import yaml


POLICY_DIR = Path("policies/teams")

ALLOWED_MODELS = {
    "company-fast",
    "company-coding",
}

ALLOWED_TOP_LEVEL_FIELDS = {
    "name",
    "description",
    "models",
    "limits",
    "terms"
}


def error(path: Path, message: str) -> None:
    print(
        f"ERROR [{path}]: {message}",
        file=sys.stderr,
    )


def validate_positive_number(
    path: Path,
    value,
    field_name: str,
) -> bool:
    if not isinstance(value, (int, float)):
        error(
            path,
            f"{field_name} must be a number",
        )
        return False

    if value <= 0:
        error(
            path,
            f"{field_name} must be > 0",
        )
        return False

    return True


def validate_policy(path: Path) -> bool:
    print(f"Validating: {path}")

    try:
        with path.open(
            "r",
            encoding="utf-8",
        ) as f:
            policy = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        error(
            path,
            f"Invalid YAML: {exc}",
        )
        return False


    valid = True

    unknown_fields = (
        set(policy)
        - ALLOWED_TOP_LEVEL_FIELDS
    )

    # print(f"Unknown top-level fields: {unknown_fields}")

    if unknown_fields:
        error(
            path,
            "unknown top-level field(s): "
            + ", ".join(sorted(unknown_fields)),
        )
        valid = False

        if not isinstance(policy, dict):
            error(
                path,
                "policy must be a YAML object",
            )
            return False

    #
    # name
    #
    name = policy.get("name")

    if not isinstance(name, str) or not name.strip():
        error(
            path,
            "'name' must be a non-empty string",
        )
        valid = False

    #
    # models
    #
    models = policy.get("models")

    if not isinstance(models, list):
        error(
            path,
            "'models' must be a list",
        )
        valid = False

    elif not models:
        error(
            path,
            "'models' must contain at least one model",
        )
        valid = False

    else:
        unknown_models = (
            set(models) - ALLOWED_MODELS
        )

        if unknown_models:
            error(
                path,
                "unknown model(s): "
                + ", ".join(
                    sorted(unknown_models)
                ),
            )
            valid = False

    #
    # limits
    #
    limits = policy.get("limits")

    if not isinstance(limits, dict):
        error(
            path,
            "'limits' must be an object",
        )
        return False

    team = limits.get("team")

    if not isinstance(team, dict):
        error(
            path,
            "'limits.team' must be an object",
        )
        valid = False
    else:
        required_team_fields = [
            "monthly_budget_usd",
            "rpm",
            "tpm",
        ]

        for field in required_team_fields:
            if field not in team:
                error(
                    path,
                    f"missing limits.team.{field}",
                )
                valid = False
                continue

            if not validate_positive_number(
                path,
                team[field],
                f"limits.team.{field}",
            ):
                valid = False

    member = limits.get("member")

    if not isinstance(member, dict):
        error(
            path,
            "'limits.member' must be an object",
        )
        valid = False

    elif "monthly_budget_usd" not in member:
        error(
            path,
            "missing "
            "limits.member.monthly_budget_usd",
        )
        valid = False

    elif not validate_positive_number(
        path,
        member["monthly_budget_usd"],
        "limits.member.monthly_budget_usd",
    ):
        valid = False

    #
    # Optional sanity check:
    # member allocation should not exceed
    # total team budget.
    #
    if (
        isinstance(team, dict)
        and isinstance(member, dict)
        and isinstance(
            team.get("monthly_budget_usd"),
            (int, float),
        )
        and isinstance(
            member.get("monthly_budget_usd"),
            (int, float),
        )
        and member["monthly_budget_usd"]
        > team["monthly_budget_usd"]
    ):
        error(
            path,
            "member budget cannot exceed "
            "team budget",
        )
        valid = False

    if valid:
        print(f"PASS: {path}")

    return valid


def main() -> int:
    if not POLICY_DIR.exists():
        print(
            f"ERROR: policy directory not found: "
            f"{POLICY_DIR}",
            file=sys.stderr,
        )
        return 1

    policies = sorted(
        POLICY_DIR.glob("*.yaml")
    )

    if not policies:
        print(
            "ERROR: no team policy files found",
            file=sys.stderr,
        )
        return 1

    print(
        f"Found {len(policies)} "
        "team policy file(s)"
    )
    print()

    all_valid = True

    for path in policies:
        if not validate_policy(path):
            all_valid = False

        print()

    if not all_valid:
        print(
            "POLICY VALIDATION: FAILED",
            file=sys.stderr,
        )
        return 1

    print("POLICY VALIDATION: PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())