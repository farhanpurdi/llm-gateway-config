"""Offline Phase 1 contract shared by the config validator entrypoints."""
from pathlib import Path

import yaml


# Approved decisions must not be inferred from mutable catalogs.
PHASE1_MODELS = {
    "company-fast": "gpt-5.6-terra",
    "company-coding": "gpt-5.6-sol",
}
ENV_REFS = {
    "master_key": "os.environ/LITELLM_MASTER_KEY",
    "database_url": "os.environ/DATABASE_URL",
}
ROUTING_OVERRIDES = {
    "fallbacks", "default_fallbacks", "context_window_fallbacks",
    "content_policy_fallbacks", "model_group_alias", "default_model",
}


class ContractError(ValueError):
    """Invalid or inconsistent Phase 1 configuration."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate keys rather than silently accepting the last value."""

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        keys = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                if key in keys:
                    raise ContractError("duplicate YAML mapping key")
                keys.add(key)
            except TypeError as exc:
                raise ContractError("YAML mapping keys must be scalar values") from exc
        return super().construct_mapping(node, deep=deep)


def load_yaml(path):
    try:
        with Path(path).open(encoding="utf-8") as stream:
            data = yaml.load(stream, Loader=UniqueKeyLoader)
    except (OSError, yaml.YAMLError, ContractError) as exc:
        # Never echo YAML values: malformed files might contain credentials.
        raise ContractError(f"{path}: unreadable or invalid YAML ({type(exc).__name__})") from exc
    return mapping(data, str(path))


def mapping(value, location):
    if not isinstance(value, dict):
        raise ContractError(f"{location}: must be a YAML object")
    return value


def exact_aliases(names, location):
    if any(not isinstance(name, str) for name in names):
        raise ContractError(f"{location}: aliases must be strings")
    if len(names) != len(set(names)):
        raise ContractError(f"{location}: duplicate logical alias")
    if set(names) != set(PHASE1_MODELS):
        raise ContractError(f"{location}: expected exactly company-fast and company-coding")


def validate_runtime(config):
    config = mapping(config, "runtime config")
    models = config.get("model_list")
    if not isinstance(models, list):
        raise ContractError("model_list: must be a list")
    names = [mapping(item, f"model_list[{index}]").get("model_name")
             for index, item in enumerate(models)]
    exact_aliases(names, "model_list")
    routes = {}
    for item in models:
        name = item["model_name"]
        params = mapping(item.get("litellm_params"), f"{name}.litellm_params")
        expected = f"openai/{PHASE1_MODELS[name]}"
        if params.get("model") != expected:
            raise ContractError(f"{name}: upstream must be {expected}")
        if params.get("api_key") != "os.environ/OPENAI_API_KEY":
            raise ContractError(f"{name}: credential must use os.environ/OPENAI_API_KEY")
        if params.get("custom_llm_provider", "openai") != "openai":
            raise ContractError(f"{name}: provider override is not approved")
        if any(field in params for field in ("api_base", "base_url", "api_type")):
            raise ContractError(f"{name}: endpoint/type override requires an approved contract")
        routes[name] = params["model"]
    general = mapping(config.get("general_settings"), "general_settings")
    for field, expected in ENV_REFS.items():
        if general.get(field) != expected:
            raise ContractError(f"general_settings.{field}: must use {expected}")
    # Extra routing can bypass an otherwise correct model_list. Empty defaults are OK.
    for location, settings in [("config", config)] + [
        (key, mapping(config[key], key))
        for key in ("litellm_settings", "router_settings", "general_settings")
        if key in config
    ]:
        for field in ROUTING_OVERRIDES:
            if field in settings and settings[field] not in (None, [], {}):
                raise ContractError(f"{location}.{field}: alternate routing is not approved")
    return routes


def yaml_files(directory):
    if not directory.is_dir():
        raise ContractError(f"{directory}: directory not found")
    return sorted(set(directory.glob("*.yaml")) | set(directory.glob("*.yml")))


def validate_repository(root):
    """Require runtime, model files and provider catalog to agree with the ADRs."""
    root = Path(root)
    routes = validate_runtime(load_yaml(root / "config/litellm_config.yaml"))
    model_files = yaml_files(root / "models")
    exact_aliases([path.stem for path in model_files], "model catalog filenames")
    for path in model_files:
        name = path.stem  # Filename remains the logical identity.
        if path.name != f"{name}.yaml":
            raise ContractError(f"{path}: expected the approved .yaml filename")
        model = load_yaml(path)
        if "logical_name" in model:
            raise ContractError(f"{path}: logical identity must come from the filename")
        if "name" in model and model["name"] != name:
            raise ContractError(f"{path}: descriptive name differs from filename")
        if model.get("status") != "active":
            raise ContractError(f"{path}: approved model must be active")
        routing = mapping(model.get("routing"), f"{path}.routing")
        if set(routing) != {"primary"}:
            raise ContractError(f"{path}: only the approved primary route is allowed")
        primary = mapping(routing["primary"], f"{path}.routing.primary")
        if primary != {"provider": "openai", "model": PHASE1_MODELS[name]}:
            raise ContractError(f"{path}: primary route differs from the approved contract")
        if routes[name] != f"{primary['provider']}/{primary['model']}":
            raise ContractError(f"{path}: route differs from runtime")

    provider_files = yaml_files(root / "providers")
    if [path.name for path in provider_files] != ["openai.yaml"]:
        raise ContractError("provider catalog: expected only providers/openai.yaml")
    provider = load_yaml(provider_files[0])
    if provider.get("provider") != "openai" or provider.get("enabled") is not True:
        raise ContractError("provider catalog: OpenAI must be the only enabled provider")
    credential = mapping(provider.get("credential"), "provider.credential")
    if credential != {"type": "environment", "environment_variable": "OPENAI_API_KEY"}:
        raise ContractError("provider credential: must reference environment OPENAI_API_KEY")
    entries = provider.get("logical_models")
    if not isinstance(entries, list):
        raise ContractError("provider.logical_models: must be a list")
    names = [mapping(item, "provider.logical_models entry").get("logical_name")
             for item in entries]
    exact_aliases(names, "provider.logical_models")
    for item in entries:
        name = item["logical_name"]
        if item.get("enabled") is not True:
            raise ContractError(f"provider.{name}: approved route must be enabled")
        if item.get("provider_model") != PHASE1_MODELS[name]:
            raise ContractError(f"provider.{name}: upstream differs from runtime/model catalog")
    return routes


def cli(label):
    import sys
    try:
        routes = validate_repository(Path.cwd())
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    for name, upstream in sorted(routes.items()):
        print(f"  {name} -> {upstream}")
    print(f"{label}: PASS (runtime + model catalog + OpenAI provider contract)")
    return 0
