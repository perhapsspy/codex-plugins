from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "validate_marketplace.py"
SPEC = importlib.util.spec_from_file_location("validate_marketplace", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"could not load validator from {MODULE_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


VALID_SHA = "0eb23f881a373ad4dc203e1f3c6f061927e01c60"


def valid_catalog() -> dict[str, Any]:
    return {
        "name": "perhapsspy",
        "interface": {"displayName": "perhapsspy Plugins"},
        "plugins": [
            {
                "name": "project-legibility",
                "source": {
                    "source": "git-subdir",
                    "url": "https://github.com/perhapsspy/project-legibility.git",
                    "path": "./plugins/project-legibility",
                    "sha": VALID_SHA,
                },
                "policy": {
                    "installation": "AVAILABLE",
                    "authentication": "ON_INSTALL",
                },
                "category": "Developer Tools",
            }
        ],
    }


class MarketplaceValidationTests(unittest.TestCase):
    def validate(
        self,
        catalog: dict[str, Any],
        *,
        verify_remote: bool = False,
        remote_loader: Any = None,
    ) -> list[str]:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo_root = Path(temporary_directory)
            marketplace_path = repo_root / ".agents/plugins/marketplace.json"
            marketplace_path.parent.mkdir(parents=True)
            marketplace_path.write_text(
                json.dumps(catalog, indent=2) + "\n", encoding="utf-8"
            )
            return VALIDATOR.validate_marketplace(
                repo_root,
                verify_remote=verify_remote,
                remote_loader=remote_loader,
            )

    def assert_error_contains(self, errors: list[str], expected: str) -> None:
        self.assertTrue(
            any(expected in error for error in errors),
            f"expected {expected!r} in errors: {errors}",
        )

    def test_valid_catalog_passes(self) -> None:
        self.assertEqual(self.validate(valid_catalog()), [])

    def test_marketplace_identity_is_fixed(self) -> None:
        catalog = valid_catalog()
        catalog["name"] = "another-publisher"
        catalog["interface"]["displayName"] = "Another Publisher"

        errors = self.validate(catalog)

        self.assert_error_contains(errors, "marketplace.name")
        self.assert_error_contains(errors, "marketplace.interface.displayName")

    def test_plugin_names_must_be_unique_kebab_case(self) -> None:
        catalog = valid_catalog()
        duplicate = copy.deepcopy(catalog["plugins"][0])
        catalog["plugins"].append(duplicate)
        invalid = copy.deepcopy(duplicate)
        invalid["name"] = "Not Kebab"
        invalid["source"]["path"] = "./plugins/Not Kebab"
        catalog["plugins"].append(invalid)

        errors = self.validate(catalog)

        self.assert_error_contains(errors, "duplicate plugin name")
        self.assert_error_contains(errors, "must be a non-empty kebab-case name")

    def test_policy_has_exact_fields_and_allowed_values(self) -> None:
        catalog = valid_catalog()
        catalog["plugins"][0]["policy"] = {
            "installation": "PUBLIC",
            "authentication": "NEVER",
            "extra": True,
        }

        errors = self.validate(catalog)

        self.assert_error_contains(errors, "unexpected fields: extra")
        self.assert_error_contains(errors, "policy.installation")
        self.assert_error_contains(errors, "policy.authentication")

    def test_plugin_entry_has_exact_fields(self) -> None:
        catalog = valid_catalog()
        catalog["plugins"][0]["description"] = "Owned by the source manifest"
        del catalog["plugins"][0]["category"]

        errors = self.validate(catalog)

        self.assert_error_contains(errors, "missing fields: category")
        self.assert_error_contains(errors, "unexpected fields: description")

    def test_source_requires_https_git_url_and_full_sha(self) -> None:
        catalog = valid_catalog()
        source = catalog["plugins"][0]["source"]
        source["url"] = "ssh://git@github.com/perhapsspy/project-legibility.git"
        source["sha"] = "main"

        errors = self.validate(catalog)

        self.assert_error_contains(errors, "source.url")
        self.assert_error_contains(errors, "source.sha")

    def test_source_fields_are_exact(self) -> None:
        catalog = valid_catalog()
        source = catalog["plugins"][0]["source"]
        source["ref"] = "main"
        del source["sha"]

        errors = self.validate(catalog)

        self.assert_error_contains(errors, "missing fields: sha")
        self.assert_error_contains(errors, "unexpected fields: ref")

    def test_source_path_must_be_safe_and_relative(self) -> None:
        unsafe_paths = (
            "plugins/project-legibility",
            "./plugins/../project-legibility",
            "./plugins//project-legibility",
            "./plugins\\project-legibility",
            "./plugins/%2e%2e/project-legibility",
        )
        for unsafe_path in unsafe_paths:
            with self.subTest(path=unsafe_path):
                catalog = valid_catalog()
                catalog["plugins"][0]["source"]["path"] = unsafe_path
                self.assert_error_contains(self.validate(catalog), "source.path")

    def test_source_path_must_end_with_plugin_name(self) -> None:
        catalog = valid_catalog()
        catalog["plugins"][0]["source"]["path"] = "./plugins/another-plugin"

        errors = self.validate(catalog)

        self.assert_error_contains(errors, "final path segment must match")

    def test_remote_manifest_uses_pinned_commit_and_path(self) -> None:
        requested_urls: list[str] = []

        def remote_loader(url: str) -> dict[str, str]:
            requested_urls.append(url)
            return {"name": "project-legibility", "version": "0.2.0"}

        errors = self.validate(
            valid_catalog(), verify_remote=True, remote_loader=remote_loader
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            requested_urls,
            [
                "https://raw.githubusercontent.com/perhapsspy/project-legibility/"
                f"{VALID_SHA}/plugins/project-legibility/.codex-plugin/plugin.json"
            ],
        )

    def test_remote_manifest_name_and_version_are_checked(self) -> None:
        def remote_loader(_url: str) -> dict[str, str]:
            return {"name": "wrong-name", "version": "latest"}

        errors = self.validate(
            valid_catalog(), verify_remote=True, remote_loader=remote_loader
        )

        self.assert_error_contains(errors, "remote manifest name")
        self.assert_error_contains(errors, "remote manifest version")

    def test_remote_verification_rejects_unsupported_git_host(self) -> None:
        catalog = valid_catalog()
        catalog["plugins"][0]["source"]["url"] = (
            "https://git.example.com/perhapsspy/project-legibility.git"
        )

        errors = self.validate(catalog, verify_remote=True)

        self.assert_error_contains(errors, "supports github.com")


if __name__ == "__main__":
    unittest.main()
