# Recognitio Mod

The spawn gate from the recognitio review workflow, packaged as a
plugin on its own.

The mod registers one hook on the agent spawn event in Claude Code.
When a reviewer or any other agent is about to start inside a
session, the hook reads the review packet manifest named by the
RECOGNITIO_PACKET_DIR environment variable. A packet whose manifest
reads verified lets the spawn through. A packet whose manifest is
missing, unreadable, unparsable or not verified denies the spawn
with a reason. When no packet directory is configured, the mod is
inert and every spawn passes through, because the mod enforces the
review workflow and is not a global spawn gate.

A hook crash fails closed. The registration carries a catch
handler that returns the deny shape, so a crashed hook denies the
spawn rather than letting it through. If the catch handler itself
throws or times out, the host skips the hook as if it had no
handler and the spawn proceeds. That second layer fail open is a
stated limit of the build, and the full contract stands in the
brief at [docs/mod-build7.md](../../docs/mod-build7.md).

The main recognitio plugin already includes this mod, because the
hooks folder at the repo root loads with that plugin. This entry
exists for a setup that wants the spawn gate without the skill
bundle, such as a folder copy install of the skill. Install one
shape or the other, and never both, because installing both
registers the same gate twice.

```bash
/plugin marketplace add david-engelmann/recognitio
/plugin install recognitio-mod@recognitio-marketplace
```

The files under hooks in this folder are byte identical copies of
the module in the hooks folder at the repo root, and the repo gate
pins the copies to the original so the two can never drift apart.

## License

MIT
