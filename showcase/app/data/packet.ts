// Every figure and every quoted line in this file comes from one real packet
// shipped in the recognitio repository at examples/example-packet-991ac6a,
// regenerated and verified by the repo gates. Provenance is recorded in
// ~/workspace/recognitio-showcase/build-record.md, Stage 4.

export const packetFacts = {
  label: "commit 991ac6ae80d3",
  commitSubject:
    "fix: catch membership stated through a pure modifier chain in the Devin gate",
  base: "eba549658f9c21e78115f6caf96034dd142af4e6",
  head: "991ac6ae80d3c00c0b6c7fc06a4a35bdafb2d965",
  filesChanged: 2,
  hunks: 2,
  addedLines: 24,
  deletedLines: 0,
  packetTokens: 6096,
  packetLines: 630,
  verified: true,
};

export type Tier = {
  id: string;
  name: string;
  carries: string;
  facts: { label: string; value: string }[];
};

export const tiers: Tier[] = [
  {
    id: "T0",
    name: "T0 Triage",
    carries:
      "The file list, the numstat summary and the commit list for the range. A changed file whose name marks it as an instruction bearing file is flagged in this list, so a reviewer can tell which changed files will steer the next agent that loads the tree.",
    facts: [
      { label: "Tokens in this packet", value: "114" },
      { label: "Files", value: "2" },
      {
        label: "The files",
        value: "scripts/check_antigravity.py and scripts/check_devin.py",
      },
      {
        label: "The commit",
        value:
          "fix: catch membership stated through a pure modifier chain in the Devin gate",
      },
    ],
  },
  {
    id: "T1",
    name: "T1 The change",
    carries:
      "Per file diffs that carry whole enclosing function context instead of a fixed line radius. The change itself never drops and never truncates, and a budget spends itself in tier order with this tier last in line to go.",
    facts: [
      { label: "Tokens in this packet", value: "3,285" },
      { label: "Files", value: "2" },
      { label: "Hunks", value: "2" },
      { label: "Added lines", value: "24" },
      { label: "Deleted lines", value: "0" },
    ],
  },
  {
    id: "T2",
    name: "T2 Companions",
    carries:
      "Call sites of the changed names elsewhere in the repo, the imports of each changed file, definitions of the changed names outside the changed files, and test files that mention the changed modules. The searches are deterministic, each one is capped, and the packet says when a cap was hit.",
    facts: [
      { label: "Tokens in this packet", value: "354" },
      { label: "Files searched", value: "2" },
      {
        label: "Test files found",
        value: "tests/test_antigravity.py and tests/test_devin.py",
      },
      {
        label: "Call sites outside the changed files",
        value: "none found, and the packet says so",
      },
    ],
  },
  {
    id: "T3",
    name: "T3 History",
    carries:
      "A blame summary for the changed ranges in the most changed files, the recent evolution of the changed functions, and prior pull requests touching those files when the GitHub CLI can name them. When the CLI cannot name them, the tier says so in plain words, as it does in this packet.",
    facts: [
      { label: "Tokens in this packet", value: "1,886" },
      { label: "Files", value: "2" },
      {
        label: "Cap note printed in this packet",
        value: "history for semantic_problems capped at 4000 of 17427",
      },
      {
        label: "Blame for the changed ranges",
        value: "David Engelmann, 14 lines and 10 lines",
      },
    ],
  },
];

export type DiffLine = { kind: "ctx" | "add"; text: string };

const ctx = (text: string): DiffLine => ({ kind: "ctx", text });
const add = (text: string): DiffLine => ({ kind: "add", text });

// Lines copied from the scripts/check_devin.py hunk in T1 of the shipped
// packet, with the diff marker characters removed for display and no other
// character changed. The short form shows the added block with two context
// lines on each side. The wide form shows more of the same hunk, including
// the second added line where the new value joins the condition.
export const hunkShort: DiffLine[] = [
  ctx(String.raw`        membership_near_resolved = bool(re.search(`),
  ctx(String.raw`            r"\b(" + MEMBERSHIP_PHRASES + r")\b.{0,15}\bresolved\b",`),
  ctx(String.raw`            low,`),
  ctx(String.raw`        ))`),
  add(String.raw`        # Modifier chain from R36-E1-02. A membership phrase`),
  add(String.raw`        # followed by a pure modifier chain and then`),
  add(String.raw`        # resolved states the same membership at any gap`),
  add(String.raw`        # length, so it fires beside the bounded form.`),
  add(String.raw`        membership_modifier_chain = bool(re.search(`),
  add(String.raw`            r"\b(" + MEMBERSHIP_PHRASES + r")\b"`),
  add(String.raw`            + MEMBERSHIP_MODIFIER_GAP + r"resolved\b",`),
  add(String.raw`            low,`),
  add(String.raw`        ))`),
  ctx(String.raw`        # Verb plus membership from S4. A listed verb within`),
  ctx(String.raw`        # 30 of a membership phrase with resolved within 20`),
];

export const hunkWide: DiffLine[] = [
  ctx(String.raw`        verb_then_equivalence = bool(re.search(`),
  ctx(String.raw`            r"\b(" + RESOLVED_VERBS + r")\b.{0,80}\b("`),
  ctx(String.raw`            + EQUIVALENCE_PHRASES + r")\b",`),
  ctx(String.raw`            low,`),
  ctx(String.raw`        ))`),
  ...hunkShort,
  ctx(String.raw`        # of the phrase restores the long filler verb shape.`),
  ctx(String.raw`        # The 19 filler comprehensive shape fires while the`),
  ctx(String.raw`        # 21 filler audit trail shape stays out, and a probe`),
  ctx(String.raw`        # with no listed verb stays out on the verb test`),
  ctx(String.raw`        # alone even before the bounds are reached.`),
  ctx(String.raw`        verb_then_membership_near_resolved = bool(re.search(`),
  ctx(String.raw`            r"\b(" + RESOLVED_VERBS + r")\b.{0,30}\b("`),
  ctx(String.raw`            + MEMBERSHIP_PHRASES + r")\b.{0,20}\bresolved\b",`),
  ctx(String.raw`            low,`),
  ctx(String.raw`        ))`),
  ctx(String.raw`        if (`),
  ctx(String.raw`            "resolved" not in seen`),
  ctx(String.raw`            and not negated`),
  ctx(String.raw`            and not correct_definition`),
  ctx(String.raw`            and "dismissed" in low`),
  ctx(String.raw`            and "resolved" in low`),
  ctx(String.raw`            and (`),
  ctx(String.raw`                verb_then_equivalence`),
  ctx(String.raw`                or membership_near_resolved`),
  add(String.raw`                or membership_modifier_chain`),
  ctx(String.raw`                or verb_then_membership_near_resolved`),
  ctx(String.raw`            )`),
  ctx(String.raw`        ):`),
];

export const hunkHeader = "@@ -421,163 +421,173 @@";
export const hunkFile = "scripts/check_devin.py";

// Fields drawn from the real manifest of this packet, values exact. The full
// manifest ships beside the packet in the repository.
export const manifestExcerpt = `{
  "extractor": "recognitio extract.py",
  "version": "1.3.0",
  "mode": "commit",
  "label": "commit 991ac6ae80d3",
  "base": "eba549658f9c21e78115f6caf96034dd142af4e6",
  "head": "991ac6ae80d3c00c0b6c7fc06a4a35bdafb2d965",
  "tiers": {
    "T0": { "emitted_tokens": 114, "files": 2 },
    "T1": { "emitted_tokens": 3285, "files": 2 },
    "T2": { "emitted_tokens": 354, "files": 2 },
    "T3": { "emitted_tokens": 1886, "files": 2 }
  },
  "verified": true,
  "discrepancies": []
}`;

// The closing lines of the verification recount in this packet, word for word.
export const recountLines = `Recount passed
The recount covered 2 files with their statuses and old paths, 2 hunks, and 24 added lines and 0 deleted lines
The recount matches the manifest on every count`;
