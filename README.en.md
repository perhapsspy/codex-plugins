# perhapsspy Plugins

[한국어](README.md)

This marketplace installs and updates plugins published by perhapsspy. See each linked product repository for its description and release notes.

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

| Name | Install | Product docs | Release notes |
|---|---|---|---|
| Project Legibility | `codex plugin add project-legibility@perhapsspy` | [Overview and usage](https://github.com/perhapsspy/project-legibility/blob/main/README.en.md) | [Changelog](https://github.com/perhapsspy/project-legibility/blob/main/CHANGELOG.en.md) |

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
