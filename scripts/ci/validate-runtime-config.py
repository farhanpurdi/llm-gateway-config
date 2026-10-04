#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

import yaml


CONFIG_FILE = Path(
    "config/litellm_config.yaml"
)


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


if not CONFIG_FILE.exists():
    fail(
        f"runtime config not found: "
        f"{CONFIG_FILE}"
    )


with CONFIG_FILE.open(
    "r",
    encoding="utf-8",
) as f:
    config = yaml.safe_load(f)


if not isinstance(config, dict):
    fail(
        "LiteLLM config must be "
        "a YAML object"
    )


model_list = config.get(
    "model_list"
)


if not isinstance(model_list, list):
    fail(
        "'model_list' must be a list"
    )


if not model_list:
    fail(
        "'model_list' cannot be empty"
    )


logical_models = []


for index, item in enumerate(
    model_list
):
    if not isinstance(item, dict):
        fail(
            f"model_list[{index}] "
            "must be an object"
        )

    model_name = item.get(
        "model_name"
    )

    if (
        not isinstance(
            model_name,
            str,
        )
        or not model_name.strip()
    ):
        fail(
            f"model_list[{index}] "
            "has invalid model_name"
        )

    params = item.get(
        "litellm_params"
    )

    if not isinstance(
        params,
        dict,
    ):
        fail(
            f"{model_name}: "
            "litellm_params missing"
        )

    provider_model = params.get(
        "model"
    )

    if (
        not isinstance(
            provider_model,
            str,
        )
        or not provider_model.strip()
    ):
        fail(
            f"{model_name}: "
            "litellm_params.model missing"
        )

    api_key = params.get(
        "api_key"
    )

    if api_key != (
        "os.environ/OPENAI_API_KEY"
    ):
        fail(
            f"{model_name}: provider "
            "credential must use "
            "os.environ/OPENAI_API_KEY"
        )

    logical_models.append(
        model_name
    )


duplicates = {
    model
    for model in logical_models
    if logical_models.count(model) > 1
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
    - set(logical_models)
)


if missing:
    fail(
        "required logical model(s) "
        "missing: "
        + ", ".join(
            sorted(missing)
        )
    )


general_settings = config.get(
    "general_settings"
)


if not isinstance(
    general_settings,
    dict,
):
    fail(
        "general_settings missing"
    )


if (
    general_settings.get(
        "master_key"
    )
    != "os.environ/LITELLM_MASTER_KEY"
):
    fail(
        "master_key must use "
        "os.environ/LITELLM_MASTER_KEY"
    )


if (
    general_settings.get(
        "database_url"
    )
    != "os.environ/DATABASE_URL"
):
    fail(
        "database_url must use "
        "os.environ/DATABASE_URL"
    )


print(
    "Runtime logical models:"
)


for model in sorted(
    logical_models
):
    print(f"  - {model}")


print(
    "LiteLLM runtime config: PASS"
)