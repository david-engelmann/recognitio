# The recognitio Cursor plugin

Pulls the relevant changes from a pull request or a commit range, with the context a reviewer needs, into one verified review packet.

## What it ships

The same skill the Claude Code plugin ships, as a real
directory copy under `skills/recognitio/`, plus one rule file
under `rules/` that restates the packet discipline. The
manifest at `plugin.json` declares the skill and the rule with
explicit relative paths.

The copy is real files on purpose. Cursor skips a symlink in
the local plugin folder that points at a plugin repository
elsewhere on disk, so a symlinked skill would load nothing.

The plugin ships no agents, no commands, no MCP servers, and
no hooks. There is no `mcp.json`, because there is no MCP
server to declare. The reviewer persona stays a Claude Code
plugin agent, so this plugin carries no second persona.

## Installing

The plugin ships in this repo as a plugin package. No Cursor
Marketplace listing exists or has been submitted for it, so the
local load route below is the route.

For a local load test, copy this folder into the local plugin
folder and reload the window, then confirm every component in
Customize.

```bash
cp -r .cursor-plugin ~/.cursor/plugins/local/recognitio
```

## The Bugbot rules beside it

The repo Bugbot rules live at `.cursor/BUGBOT.md` with the repo
config at `.cursor/config/bugbot.yaml`. They are review
guidance for pull requests, not plugin components.

Bugbot findings default to neutral, so a merge gate built on
Bugbot must enable fail on unresolved issues where the
organization offers it. Effort level is a Teams dashboard
setting, not a `bugbot.yaml` control.
