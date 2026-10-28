# Example packet

This folder holds one complete real packet a visitor can open without installing anything. The packet stands in [the packet file](example-packet-991ac6a/packet.md) beside this note, and its receipt stands in [the manifest](example-packet-991ac6a/manifest.json) beside the packet.

## What change it covers

The packet covers a single commit in the recognitio repo itself. The commit taught the Devin gate to catch membership stated through a pure modifier chain, and it also touched the Antigravity gate beside it.

- Head commit 991ac6ae80d3c00c0b6c7fc06a4a35bdafb2d965
- Base commit eba549658f9c21e78115f6caf96034dd142af4e6
- Files changed 2, being `scripts/check_devin.py` and `scripts/check_antigravity.py`
- Size 2 hunks with 24 added lines and 0 deleted lines
- Packet length 624 lines in `packet.md` with all four tiers included and nothing dropped

## The command that produced it

The extractor ran from a clone of this repo with this command, and it wrote `packet.md` and `manifest.json` into the example packet folder.

```bash
python3 .agents/skills/\
recognitio/scripts/\
extract.py \
  --commit 991ac6a \
  --out examples/\
example-packet-991ac6a \
  --repo .
```

Nothing in the packet was written or edited by hand.

## Verified status from the manifest

The manifest records verified as true with an empty discrepancies list. The extractor printed the same verdict when it finished the run. The packet closes with a verification recount that matches the manifest on every count, and it ends on the limit sentence the shipped packet format carries. Verified here means the packet holds the whole change it names, and the Objections section of the README states what it does not mean.
