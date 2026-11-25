"use client";

import { useState } from "react";
import { hunkFile, hunkHeader, hunkShort, hunkWide } from "../data/packet";

export default function HunkViewer() {
  const [wide, setWide] = useState(false);
  const lines = wide ? hunkWide : hunkShort;
  return (
    <div style={{ marginTop: 20 }}>
      <div className="codeblock" aria-label="Excerpt from the shipped packet">
        <span className="dim">{hunkFile}</span>
        {"\n"}
        <span className="hl">{hunkHeader}</span>
        {"\n"}
        {lines.map((line, i) => (
          <span key={i} className={line.kind === "add" ? "add" : undefined}>
            {line.kind === "add" ? "+ " : "  "}
            {line.text}
            {"\n"}
          </span>
        ))}
      </div>
      <button
        type="button"
        className="toggle"
        aria-expanded={wide}
        onClick={() => setWide(!wide)}
      >
        {wide ? "Show less of the hunk" : "Show more of the hunk"}
      </button>
      <p style={{ color: "var(--ink-2)", fontSize: 14, marginTop: 10 }}>
        An excerpt from one hunk of this packet, copied line for line. In the
        packet itself the hunk carries the whole enclosing function around
        these lines.
      </p>
    </div>
  );
}
