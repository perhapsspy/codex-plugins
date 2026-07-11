#!/usr/bin/env python3
"""Validate the perhapsspy Codex plugin marketplace."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen


MARKETPLACE_REL = Path(".agents/plugins/marketplace.json")
MARKETPLACE_NAME = "perhapsspy"
MARKETPLACE_DISPLAY_NAME = "perhapsspy Plugins"

NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)

ROOT_FIELDS = {"name", "interface", "plugins"}
INTERFACE_FIELDS = {"displayName"}
PLUGIN_FIELDS = {"name", "source", "policy", "category"}
SOURCE_FIELDS = {"source", "url", "path", "sha"}
POLICY_FIELDS = {"installation", "authentication"}
INSTALLATION_VALUES = {"NOT_AVAILABLE", "AVAILABLE", "INSTALLED_BY_DEFAULT"}
AUTHENTICATION_VALUES = {"ON_INSTALL", "ON_USE"}
MAX_MANIFEST_BYTES = 1_048_576

RemoteLoader = Callable[[str], Any]


class RemoteManifestError(RuntimeError):
    """A pinned manifest could not be read or decoded."""


def validate_marketplace(
    repo_root: Path,
    *,
    verify_remote: bool = False,
    remote_loader: RemoteLoader | None = None,
) -> list[str]:
    """Return every marketplace contract error below ``repo_root``."""

    marketplace_path = repo_root.resolve() / MARKETPLACE_REL
    errors: list[str] = []
    catalog = load_json(marketplace_path, errors)
    if not isinstance(catalog, dict):
        if catalog is not None:
            add_error(errors, "marketplace", "root must be a JSON object")
        return sorted(errors)

    validate_exact_fields(catalog, ROOT_FIELDS, "marketplace", errors)
    require_exact(catalog, "name", MARKETPLACE_NAME, "marketplace", errors)

    interface = catalog.get("interface")
    if not isinstance(interface, dict):
        add_error(errors, "marketplace.interface", "must be an object")
    else:
        validate_exact_fields(
            interface, INTERFACE_FIELDS, "marketplace.interface", errors
        )
        require_exact(
            interface,
            "displayName",
            MARKETPLACE_DISPLAY_NAME,
            "marketplace.interface",
            errors,
        )

    plugins = catalog.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        add_error(errors, "marketplace.plugins", "must be a non-empty array")
        return sorted(errors)

    seen_names: set[str] = set()
    loader = remote_loader or fetch_remote_json
    for index, plugin in enumerate(plugins):
        location = f"marketplace.plugins[{index}]"
        validate_plugin_entry(
            plugin,
            location,
            seen_names,
            errors,
            verify_remote=verify_remote,
            remote_loader=loader,
        )

    return sorted(errors)


def validate_plugin_entry(
    plugin: Any,
    location: str,
    seen_names: set[str],
    errors: list[str],
    *,
    verify_remote: bool,
    remote_loader: RemoteLoader,
) -> None:
    if not isinstance(plugin, dict):
        add_error(errors, location, "must be an object")
        return

    validate_exact_fields(plugin, PLUGIN_FIELDS, location, errors)

    name = plugin.get("name")
    name_is_valid = isinstance(name, str) and bool(NAME_PATTERN.fullmatch(name))
    if not name_is_valid:
        add_error(errors, f"{location}.name", "must be a non-empty kebab-case name")
    elif name in seen_names:
        add_error(errors, f"{location}.name", f"duplicate plugin name {name!r}")
    else:
        seen_names.add(name)

    source = plugin.get("source")
    source_is_valid = validate_source(source, name, location, errors)
    validate_policy(plugin.get("policy"), location, errors)

    category = plugin.get("category")
    if not isinstance(category, str) or not category.strip():
        add_error(errors, f"{location}.category", "must be a non-empty string")

    if verify_remote and name_is_valid and source_is_valid:
        verify_remote_manifest(
            name,
            source,
            f"{location}.source",
            errors,
            remote_loader,
        )


def validate_source(
    source: Any, plugin_name: Any, plugin_location: str, errors: list[str]
) -> bool:
    location = f"{plugin_location}.source"
    if not isinstance(source, dict):
        add_error(errors, location, "must be an object")
        return False

    initial_error_count = len(errors)
    validate_exact_fields(source, SOURCE_FIELDS, location, errors)
    require_exact(source, "source", "git-subdir", location, errors)

    url = source.get("url")
    if not is_https_git_url(url):
        add_error(
            errors,
            f"{location}.url",
            "must be an HTTPS Git URL ending in .git without credentials, query, or fragment",
        )

    sha = source.get("sha")
    if not isinstance(sha, str) or not SHA_PATTERN.fullmatch(sha):
        add_error(errors, f"{location}.sha", "must be a full lowercase 40-character SHA")

    path = source.get("path")
    if not is_safe_subdir(path):
        add_error(
            errors,
            f"{location}.path",
            "must be a safe ./-relative subdirectory without empty, . or .. segments",
        )
    elif isinstance(plugin_name, str) and path.rsplit("/", 1)[-1] != plugin_name:
        add_error(
            errors,
            f"{location}.path",
            "final path segment must match the plugin name",
        )

    return len(errors) == initial_error_count


def validate_policy(policy: Any, plugin_location: str, errors: list[str]) -> None:
    location = f"{plugin_location}.policy"
    if not isinstance(policy, dict):
        add_error(errors, location, "must be an object")
        return

    validate_exact_fields(policy, POLICY_FIELDS, location, errors)
    installation = policy.get("installation")
    if installation not in INSTALLATION_VALUES:
        allowed = ", ".join(sorted(INSTALLATION_VALUES))
        add_error(errors, f"{location}.installation", f"must be one of: {allowed}")

    authentication = policy.get("authentication")
    if authentication not in AUTHENTICATION_VALUES:
        allowed = ", ".join(sorted(AUTHENTICATION_VALUES))
        add_error(errors, f"{location}.authentication", f"must be one of: {allowed}")


def verify_remote_manifest(
    plugin_name: str,
    source: dict[str, Any],
    location: str,
    errors: list[str],
    remote_loader: RemoteLoader,
) -> None:
    try:
        manifest_url = build_github_manifest_url(
            source["url"], source["sha"], source["path"]
        )
    except ValueError as exc:
        add_error(errors, f"{location}.url", str(exc))
        return

    try:
        manifest = remote_loader(manifest_url)
    except RemoteManifestError as exc:
        add_error(errors, f"{location}.path", str(exc))
        return

    if not isinstance(manifest, dict):
        add_error(errors, f"{location}.path", "remote manifest root must be an object")
        return

    if manifest.get("name") != plugin_name:
        add_error(
            errors,
            f"{location}.path",
            f"remote manifest name must be {plugin_name!r}, got {manifest.get('name')!r}",
        )

    version = manifest.get("version")
    if not isinstance(version, str) or not SEMVER_PATTERN.fullmatch(version):
        add_error(
            errors,
            f"{location}.path",
            f"remote manifest version must be strict SemVer, got {version!r}",
        )


def build_github_manifest_url(git_url: str, sha: str, plugin_path: str) -> str:
    parsed = urlsplit(git_url)
    if parsed.hostname != "github.com":
        raise ValueError("remote verification currently supports github.com Git URLs")

    repository_parts = [part for part in parsed.path.split("/") if part]
    if len(repository_parts) != 2 or not repository_parts[1].endswith(".git"):
        raise ValueError("GitHub URL must identify one owner/repository.git path")

    owner = quote(repository_parts[0], safe="")
    repository = quote(repository_parts[1][:-4], safe="")
    remote_path = plugin_path.removeprefix("./")
    manifest_parts = [
        *(quote(part, safe="") for part in remote_path.split("/")),
        ".codex-plugin",
        "plugin.json",
    ]
    manifest_path = "/".join(manifest_parts)
    return f"https://raw.githubusercontent.com/{owner}/{repository}/{sha}/{manifest_path}"


def fetch_remote_json(url: str) -> Any:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "perhapsspy-codex-marketplace-validator",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            body = response.read(MAX_MANIFEST_BYTES + 1)
    except HTTPError as exc:
        raise RemoteManifestError(
            f"could not read remote manifest at the pinned path (HTTP {exc.code})"
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RemoteManifestError(f"could not read remote manifest ({exc})") from exc

    if len(body) > MAX_MANIFEST_BYTES:
        raise RemoteManifestError("remote manifest exceeds 1 MiB")

    try:
        return json.loads(body.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise RemoteManifestError("remote manifest is not UTF-8") from exc
    except json.JSONDecodeError as exc:
        raise RemoteManifestError(
            f"remote manifest is invalid JSON at line {exc.lineno}, column {exc.colno}"
        ) from exc


def load_json(path: Path, errors: list[str]) -> Any | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        add_error(errors, str(MARKETPLACE_REL), "required marketplace file is missing")
    except UnicodeDecodeError as exc:
        add_error(errors, str(MARKETPLACE_REL), f"must be UTF-8 ({exc})")
    except json.JSONDecodeError as exc:
        add_error(
            errors,
            str(MARKETPLACE_REL),
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
        )
    except OSError as exc:
        add_error(errors, str(MARKETPLACE_REL), f"could not be read ({exc})")
    return None


def validate_exact_fields(
    value: dict[str, Any], expected: set[str], location: str, errors: list[str]
) -> None:
    missing = sorted(expected - value.keys())
    unexpected = sorted(value.keys() - expected)
    if missing:
        add_error(errors, location, f"missing fields: {', '.join(missing)}")
    if unexpected:
        add_error(errors, location, f"unexpected fields: {', '.join(unexpected)}")


def require_exact(
    value: dict[str, Any],
    field: str,
    expected: str,
    location: str,
    errors: list[str],
) -> None:
    if value.get(field) != expected:
        add_error(
            errors,
            f"{location}.{field}",
            f"must be {expected!r}, got {value.get(field)!r}",
        )


def is_https_git_url(value: Any) -> bool:
    if not isinstance(value, str) or any(
        character.isspace() or ord(character) < 32 for character in value
    ):
        return False
    parsed = urlsplit(value)
    return bool(
        parsed.scheme == "https"
        and parsed.hostname
        and parsed.username is None
        and parsed.password is None
        and parsed.path.endswith(".git")
        and parsed.path not in {"", "/", ".git", "/.git"}
        and not parsed.query
        and not parsed.fragment
    )


def is_safe_subdir(value: Any) -> bool:
    if not isinstance(value, str) or not value.startswith("./"):
        return False
    if any(ord(character) < 32 for character in value):
        return False
    if any(character in value for character in ("\\", "?", "#", "%")):
        return False
    relative = value[2:]
    parts = relative.split("/")
    return bool(relative and all(part not in {"", ".", ".."} for part in parts))


def add_error(errors: list[str], location: str, message: str) -> None:
    errors.append(f"{location}: {message}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="marketplace repository root (defaults to this script's parent repository)",
    )
    parser.add_argument(
        "--verify-remote",
        action="store_true",
        help="fetch each manifest from its pinned GitHub commit and path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    errors = validate_marketplace(args.repo_root, verify_remote=args.verify_remote)
    if errors:
        print("Marketplace validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    remote_note = " including remote manifests" if args.verify_remote else ""
    print(f"Marketplace validation passed{remote_note}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
