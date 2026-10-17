#!/usr/bin/env python3
"""Exercise real validator CLIs against temporary, secret-free config copies."""
import copy
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = "config/litellm_config.yaml"
FAST = "models/company-fast.yaml"
CODING = "models/company-coding.yaml"
PROVIDER = "providers/openai.yaml"
PARAMS = ("model_list", 0, "litellm_params")
CASES = [
    ("runtime_empty", RUNTIME, (), {}),
    ("runtime_scalar", RUNTIME, (), "invalid"),
    ("runtime_models_null", RUNTIME, ("model_list",), None),
    ("runtime_models_empty", RUNTIME, ("model_list",), []),
    ("runtime_models_object", RUNTIME, ("model_list",), {}),
    ("runtime_entry_scalar", RUNTIME, ("model_list", 0), "invalid"),
    ("runtime_alias_not_string", RUNTIME, ("model_list", 0, "model_name"), ["company-fast"]),
    ("runtime_alias_unknown", RUNTIME, ("model_list", 0, "model_name"), "other"),
    ("runtime_alias_wildcard", RUNTIME, ("model_list", 0, "model_name"), "*"),
    ("runtime_alias_duplicate", RUNTIME, ("model_list", 1, "model_name"), "company-fast"),
    ("runtime_params_null", RUNTIME, PARAMS, None),
    ("runtime_wrong_fast", RUNTIME, PARAMS + ("model",), "openai/unapproved"),
    ("runtime_wrong_coding", RUNTIME, ("model_list", 1, "litellm_params", "model"), "openai/unapproved"),
    ("runtime_provider_other", RUNTIME, PARAMS + ("model",), "anthropic/unapproved"),
    ("runtime_no_provider_prefix", RUNTIME, PARAMS + ("model",), "gpt-5.6-terra"),
    ("runtime_credential_other_env", RUNTIME, PARAMS + ("api_key",), "os.environ/OTHER_KEY"),
    ("runtime_credential_inline", RUNTIME, PARAMS + ("api_key",), "test-placeholder"),
    ("runtime_provider_override", RUNTIME, PARAMS + ("custom_llm_provider",), "anthropic"),
    ("runtime_endpoint_override", RUNTIME, PARAMS + ("api_base",), "https://example.invalid/v1"),
    ("runtime_base_url_override", RUNTIME, PARAMS + ("base_url",), "https://example.invalid/v1"),
    ("runtime_api_type_override", RUNTIME, PARAMS + ("api_type",), "azure"),
    ("runtime_master_other_env", RUNTIME, ("general_settings", "master_key"), "os.environ/OTHER_KEY"),
    ("runtime_database_other_env", RUNTIME, ("general_settings", "database_url"), "os.environ/OTHER_DATABASE"),
    ("runtime_general_null", RUNTIME, ("general_settings",), None),
    ("runtime_settings_null", RUNTIME, ("litellm_settings",), None),
    ("runtime_fallback", RUNTIME, ("litellm_settings", "fallbacks"), [{"company-fast": ["other"]}]),
    ("runtime_router_alias", RUNTIME, ("router_settings",), {"model_group_alias": {"extra": "company-fast"}}),
    ("runtime_top_fallback", RUNTIME, ("fallbacks",), [{"company-fast": ["other"]}]),
    ("runtime_general_default", RUNTIME, ("general_settings", "default_model"), "other"),
    ("catalog_fast_provider", FAST, ("routing", "primary", "provider"), "anthropic"),
    ("catalog_fast_upstream", FAST, ("routing", "primary", "model"), "unapproved"),
    ("catalog_coding_upstream", CODING, ("routing", "primary", "model"), "unapproved"),
    ("catalog_name_disagrees", FAST, ("name",), "company-coding"),
    ("catalog_logical_name", FAST, ("logical_name",), "company-fast"),
    ("catalog_inactive", FAST, ("status",), "disabled"),
    ("catalog_routing_null", FAST, ("routing",), None),
    ("catalog_primary_null", FAST, ("routing", "primary"), None),
    ("catalog_fallback", FAST, ("routing", "fallback"), {"provider": "other", "model": "other"}),
    ("catalog_extra_endpoint", FAST, ("routing", "primary", "api_base"), "https://example.invalid"),
    ("provider_wrong_identity", PROVIDER, ("provider",), "anthropic"),
    ("provider_disabled", PROVIDER, ("enabled",), False),
    ("provider_enabled_string", PROVIDER, ("enabled",), "true"),
    ("provider_credential_type", PROVIDER, ("credential", "type"), "inline"),
    ("provider_credential_env", PROVIDER, ("credential", "environment_variable"), "OTHER_KEY"),
    ("provider_inline_credential", PROVIDER, ("credential", "value"), "test-placeholder"),
    ("provider_models_null", PROVIDER, ("logical_models",), None),
    ("provider_models_empty", PROVIDER, ("logical_models",), []),
    ("provider_entry_scalar", PROVIDER, ("logical_models", 0), "invalid"),
    ("provider_alias_duplicate", PROVIDER, ("logical_models", 1, "logical_name"), "company-fast"),
    ("provider_alias_unknown", PROVIDER, ("logical_models", 0, "logical_name"), "other"),
    ("provider_fast_upstream", PROVIDER, ("logical_models", 0, "provider_model"), "unapproved"),
    ("provider_coding_upstream", PROVIDER, ("logical_models", 1, "provider_model"), "unapproved"),
    ("provider_route_disabled", PROVIDER, ("logical_models", 0, "enabled"), False),
    ("provider_route_enabled_string", PROVIDER, ("logical_models", 0, "enabled"), "true"),
]


class ContractValidation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "config-repo"
        self.root.mkdir()
        self.env = dict(os.environ, PATH=f"{Path(sys.executable).parent}:{os.environ['PATH']}")
        for directory in ("config", "models", "providers", "scripts/ci", "policies", "clients"):
            shutil.copytree(ROOT / directory, self.root / directory, dirs_exist_ok=True)
        shutil.copy2(ROOT / "scripts/validate.sh", self.root / "scripts/validate.sh")
        shutil.copy2(ROOT / "README.md", self.root / "README.md")

    def change(self, file, keys, value):
        path = self.root / file
        doc = yaml.safe_load(path.read_text())
        if not keys:
            doc = value
        else:
            target = doc
            for key in keys[:-1]:
                target = target[key]
            target[keys[-1]] = value
        path.write_text(yaml.safe_dump(doc, sort_keys=False))

    def check(self, valid):
        for script in ("validate-runtime-config.py", "validate-model-catalog.py"):
            with self.subTest(entrypoint=script):
                result = subprocess.run([sys.executable, str(self.root / "scripts/ci" / script)],
                                        cwd=self.root, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0 if valid else 1, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("PASS" if valid else "ERROR:", result.stdout + result.stderr)

    def test_approved_config(self):
        self.check(True)

    def test_timeout_comment_and_order_changes_are_allowed(self):
        self.change(RUNTIME, PARAMS + ("timeout",), 181)
        for file, field in ((RUNTIME, "model_list"), (PROVIDER, "logical_models")):
            values = yaml.safe_load((self.root / file).read_text())[field]
            self.change(file, (field,), list(reversed(values)))
        with (self.root / RUNTIME).open("a") as stream:
            stream.write("\n# harmless comment\n")
        self.check(True)

    def test_model_identity_without_descriptive_name(self):
        path = self.root / FAST
        doc = yaml.safe_load(path.read_text())
        del doc["name"]
        path.write_text(yaml.safe_dump(doc))
        self.check(True)

    def test_runtime_extra_alias(self):
        models = yaml.safe_load((self.root / RUNTIME).read_text())["model_list"]
        extra = copy.deepcopy(models[0])
        extra["model_name"] = "extra"
        self.change(RUNTIME, ("model_list",), models + [extra])
        self.check(False)

    def test_provider_extra_alias(self):
        entries = yaml.safe_load((self.root / PROVIDER).read_text())["logical_models"]
        extra = copy.deepcopy(entries[0])
        extra["logical_name"] = "extra"
        self.change(PROVIDER, ("logical_models",), entries + [extra])
        self.check(False)

    def test_coordinated_wrong_route_in_all_three_sources_is_rejected(self):
        self.change(RUNTIME, PARAMS + ("model",), "openai/unapproved")
        self.change(FAST, ("routing", "primary", "model"), "unapproved")
        self.change(PROVIDER, ("logical_models", 0, "provider_model"), "unapproved")
        self.check(False)

    def test_missing_and_extra_catalog_files(self):
        for file in (FAST, CODING, PROVIDER):
            with self.subTest(file=file):
                path = self.root / file
                original = path.read_bytes()
                path.unlink()
                self.check(False)
                path.write_bytes(original)
        for file in ("models/extra.yaml", "providers/other.yml", "models/company-fast.yml"):
            with self.subTest(file=file):
                path = self.root / file
                path.write_text("{}\n")
                self.check(False)
                path.unlink()

    def test_yaml_duplicate_keys_and_malformed_content(self):
        for file in (RUNTIME, FAST, PROVIDER):
            path = self.root / file
            original = path.read_bytes()
            for content in ("duplicate: 1\nduplicate: 2\n" + original.decode(), "[broken", ""):
                with self.subTest(file=file,content=content[:10]):
                    path.write_text(content)
                    self.check(False)
            path.write_bytes(original)

    def test_both_shell_entrypoints_reject_wrong_routes(self):
        self.change(RUNTIME, PARAMS + ("model",), "openai/unapproved")
        for entrypoint in ("scripts/validate.sh", "scripts/ci/validate.sh"):
            with self.subTest(entrypoint=entrypoint):
                result = subprocess.run(["bash", str(self.root / entrypoint)], cwd=self.root,
                                        env=self.env, capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("upstream must be", result.stderr)
                self.assertNotIn("CONFIG VALIDATION: PASSED", result.stdout)


def mutation_test(file, keys, value):
    def test(self):
        self.change(file, keys, value)
        self.check(False)
    return test


for name, file, keys, value in CASES:
    setattr(ContractValidation, f"test_{name}", mutation_test(file, keys, value))


if __name__ == "__main__":
    unittest.main(verbosity=2)
