# Contributing

[한국어](CONTRIBUTING.md)

This repository owns only the plugin list and installation pins. Change and validate plugin behavior, documentation, and manifests in the relevant source repository first.

## Update a pin

1. Validate the source repository change and push it to the public remote.
2. Set `source.sha` in `.agents/plugins/marketplace.json` to the commit's full 40-character SHA.
3. Run the checks below.
4. Confirm that the marketplace diff changes only the intended plugin, URL, path, and SHA.

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/validate_marketplace.py --verify-remote
```

`--verify-remote` reads `.codex-plugin/plugin.json` from the pinned commit and plugin path, then checks its name and SemVer version.

## Add a plugin

Add an entry to the `plugins` array in `.agents/plugins/marketplace.json`. Names must use kebab-case and must be unique.

```json
{
  "name": "plugin-name",
  "source": {
    "source": "git-subdir",
    "url": "https://github.com/perhapsspy/plugin-name.git",
    "path": "./plugins/plugin-name",
    "sha": "0123456789abcdef0123456789abcdef01234567"
  },
  "policy": {
    "installation": "AVAILABLE",
    "authentication": "ON_INSTALL"
  },
  "category": "Developer Tools"
}
```

The SHA above demonstrates the format only. A real entry must use a remote commit that passes validation. If a plugin lives at the repository root, update the validator and catalog contract together and add a test for that source shape.

## Review checklist

- The marketplace name and display name remain `perhapsspy` and `perhapsspy Plugins`.
- The URL is an HTTPS Git URL without embedded credentials.
- The path begins with `./` and cannot escape the remote repository.
- The full SHA resolves to the public plugin manifest.
- Policy fields and values follow the Codex marketplace contract.
