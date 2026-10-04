#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

import yaml


POLICY_DIR = Path(
    "policies/teams"
)

MODEL_DIR = Path(
    "models"
)


ALLOWED_TOP_LEVEL_FIELDS = {
    "name",
    "description",
    "models",
    "limits",
}


ALLOWED_LIMIT_FIELDS = {
    "team",
    "member",
}


ALLOWED_TEAM_LIMIT_FIELDS = {
    "monthly_budget_usd",
    "rpm",
    "tpm",
}


ALLOWED_MEMBER_LIMIT_FIELDS = {
    "monthly_budget_usd",
}


def error(
    path: Path,
    message: str,
) -> None:

    print(
        f"ERROR [{path}]: "
        f"{message}",
        file=sys.stderr,
    )


def read_model_catalog() -> set[str]:

    models: set[str] = set()

    for path in sorted(
        MODEL_DIR.glob("*.yaml")
    ):
        models.add(
            path.stem
        )

    return models


def positive_number(
    path: Path,
    value,
    field: str,
) -> bool:

    if isinstance(
        value,
        bool,
    ):
        error(
            path,
            f"{field} must be "
            "a positive number",
        )
        return False

    if not isinstance(
        value,
        (int, float),
    ):
        error(
            path,
            f"{field} must be "
            "a number",
        )
        return False

    if value <= 0:
        error(
            path,
            f"{field} must be > 0",
        )
        return False

    return True


def unknown_fields(
    path: Path,
    data: dict,
    allowed: set[str],
    location: str,
) -> bool:

    unknown = (
        set(data)
        - allowed
    )

    if not unknown:
        return False

    error(
        path,
        f"unknown field(s) in "
        f"{location}: "
        + ", ".join(
            sorted(unknown)
        ),
    )

    return True


def validate_policy(
    path: Path,
    allowed_models: set[str],
) -> bool:

    print(
        f"Validating policy: {path}"
    )

    with path.open(
        "r",
        encoding="utf-8",
    ) as f:
        policy = yaml.safe_load(f)

    if not isinstance(
        policy,
        dict,
    ):
        error(
            path,
            "policy must be "
            "a YAML object",
        )
        return False

    valid = True

    if unknown_fields(
        path,
        policy,
        ALLOWED_TOP_LEVEL_FIELDS,
        "policy",
    ):
        valid = False


    name = policy.get(
        "name"
    )

    if (
        not isinstance(
            name,
            str,
        )
        or not name.strip()
    ):
        error(
            path,
            "name must be "
            "a non-empty string",
        )
        valid = False

    elif path.name != f"{name}.yaml":
        error(
            path,
            "filename must match "
            f"policy name: {name}.yaml",
        )
        valid = False


    models = policy.get(
        "models"
    )

    if not isinstance(
        models,
        list,
    ):
        error(
            path,
            "models must be a list",
        )
        valid = False

    elif not models:
        error(
            path,
            "models must not be empty",
        )
        valid = False

    else:
        duplicates = {
            model
            for model in models
            if models.count(model) > 1
        }

        if duplicates:
            error(
                path,
                "duplicate model(s): "
                + ", ".join(
                    sorted(duplicates)
                ),
            )
            valid = False

        unknown_models = (
            set(models)
            - allowed_models
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


    limits = policy.get(
        "limits"
    )

    if not isinstance(
        limits,
        dict,
    ):
        error(
            path,
            "limits must be an object",
        )
        return False


    if unknown_fields(
        path,
        limits,
        ALLOWED_LIMIT_FIELDS,
        "limits",
    ):
        valid = False


    team = limits.get(
        "team"
    )

    if not isinstance(
        team,
        dict,
    ):
        error(
            path,
            "limits.team "
            "must be an object",
        )
        valid = False

    else:
        if unknown_fields(
            path,
            team,
            ALLOWED_TEAM_LIMIT_FIELDS,
            "limits.team",
        ):
            valid = False

        for field in sorted(
            ALLOWED_TEAM_LIMIT_FIELDS
        ):
            if field not in team:
                error(
                    path,
                    f"missing "
                    f"limits.team.{field}",
                )
                valid = False
                continue

            if not positive_number(
                path,
                team[field],
                f"limits.team.{field}",
            ):
                valid = False


    member = limits.get(
        "member"
    )

    if not isinstance(
        member,
        dict,
    ):
        error(
            path,
            "limits.member "
            "must be an object",
        )
        valid = False

    else:
        if unknown_fields(
            path,
            member,
            ALLOWED_MEMBER_LIMIT_FIELDS,
            "limits.member",
        ):
            valid = False

        field = (
            "monthly_budget_usd"
        )

        if field not in member:
            error(
                path,
                "missing "
                "limits.member."
                "monthly_budget_usd",
            )
            valid = False

        elif not positive_number(
            path,
            member[field],
            "limits.member."
            "monthly_budget_usd",
        ):
            valid = False


    if (
        isinstance(team, dict)
        and isinstance(
            member,
            dict,
        )
    ):
        team_budget = team.get(
            "monthly_budget_usd"
        )

        member_budget = member.get(
            "monthly_budget_usd"
        )

        if (
            isinstance(
                team_budget,
                (int, float),
            )
            and not isinstance(
                team_budget,
                bool,
            )
            and isinstance(
                member_budget,
                (int, float),
            )
            and not isinstance(
                member_budget,
                bool,
            )
            and member_budget
            > team_budget
        ):
            error(
                path,
                "member monthly budget "
                "cannot exceed team "
                "monthly budget",
            )
            valid = False


    if valid:
        print(
            f"PASS: {path}"
        )

    return valid


def main() -> int:

    if not POLICY_DIR.exists():
        print(
            "ERROR: policy directory "
            "not found",
            file=sys.stderr,
        )
        return 1


    allowed_models = (
        read_model_catalog()
    )


    if not allowed_models:
        print(
            "ERROR: no logical models "
            "found",
            file=sys.stderr,
        )
        return 1


    policies = sorted(
        POLICY_DIR.glob("*.yaml")
    )


    if not policies:
        print(
            "ERROR: no team policies "
            "found",
            file=sys.stderr,
        )
        return 1


    print(
        "Allowed logical models:"
    )

    for model in sorted(
        allowed_models
    ):
        print(f"  - {model}")

    print()


    all_valid = True


    for path in policies:

        if not validate_policy(
            path,
            allowed_models,
        ):
            all_valid = False

        print()


    if not all_valid:
        print(
            "POLICY VALIDATION: FAILED",
            file=sys.stderr,
        )
        return 1


    print(
        "POLICY VALIDATION: PASSED"
    )

    return 0


if __name__ == "__main__":
    sys.exit(
        main()
    )