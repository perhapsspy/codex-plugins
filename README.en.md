# perhapsspy Codex Plugins

[한국어](README.md)

This repository lists the Codex plugins published by perhapsspy. Each product repository owns its code and releases; this catalog records the reviewed commit that Codex installs.

## Install

Add the marketplace once:

```bash
codex plugin marketplace add perhapsspy/codex-plugins
```

Then install the plugin you need:

```bash
codex plugin add project-legibility@perhapsspy
```

## Plugins

| Name | Purpose | Source |
|---|---|---|
| Project Legibility | Ten skills for continuing repository work across tasks and checking port sources, async state, and documentation | [perhapsspy/project-legibility](https://github.com/perhapsspy/project-legibility) |

Usage and release notes for each plugin live in its source repository.

## Update and remove

```bash
# Refresh the marketplace catalog
codex plugin marketplace upgrade perhapsspy

# Reinstall from the version selected by the catalog
codex plugin add project-legibility@perhapsspy

# Remove the plugin
codex plugin remove project-legibility@perhapsspy
```

To remove the marketplace registration as well, remove its plugins first and then run:

```bash
codex plugin marketplace remove perhapsspy
```

## Maintenance

See [CONTRIBUTING.en.md](CONTRIBUTING.en.md) for catalog changes. Every remote plugin is pinned to a full commit SHA rather than a branch or tag, and CI checks the manifest at that path.

## License

[MIT](LICENSE)
