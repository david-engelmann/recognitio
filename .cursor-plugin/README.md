# The recognitio Cursor plugin

This is the Cursor plugin for recognitio. It ships the same skill
the Claude Code plugin ships, as a real directory copy under
`skills/recognitio/`, plus one rule file under `rules/` that
restates the packet discipline. The copy is real files on
purpose. Cursor skips a symlink in the local plugin folder that
points at a plugin repository elsewhere on disk, so a symlinked
skill would load nothing.

## What it ships

The manifest at `plugin.json` declares the skill and the rule
with explicit relative paths. The plugin ships no agents, no
commands, no MCP servers, and no hooks. The reviewer persona
stays a Claude Code plugin agent, so this plugin carries no
second persona. There is no `mcp.json`, because there is no MCP
server to declare.

## Installing

The plugin is distributed through the manually reviewed Cursor
Marketplace. Every plugin is manually reviewed before it is
listed, and all plugins must be open source. Reviewed updates
auto deploy to clients pinned at the commit SHA, with no user
version pinning. A running Cloud Agent keeps the plugin versions
it started with, so start a new agent to pick up an update.

For a local load test, copy this folder into the local plugin
folder and reload the window, then confirm every component in
Customize.

```bash
cp -r .cursor-plugin ~/.cursor/plugins/local/recognitio
```

## The Bugbot rules beside it

The repo's Bugbot rules live at `.cursor/BUGBOT.md` with the repo
config at `.cursor/config/bugbot.yaml`. They are review guidance
for pull requests, not plugin components. Bugbot findings default
to neutral, so a merge gate built on Bugbot must enable fail on
unresolved issues where the organization offers it. Effort level
is a Teams dashboard setting, not a `bugbot.yaml` control.
