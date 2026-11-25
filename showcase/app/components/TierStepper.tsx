"use client";

import { useState } from "react";
import { tiers } from "../data/packet";
import HunkViewer from "./HunkViewer";

export default function TierStepper() {
  const [active, setActive] = useState(0);
  const tier = tiers[active];
  return (
    <div>
      <div className="tierbar" role="group" aria-label="Packet tiers">
        {tiers.map((t, i) => (
          <button
            key={t.id}
            type="button"
            aria-pressed={i === active}
            onClick={() => setActive(i)}
          >
            {t.name}
          </button>
        ))}
      </div>
      <div className="tierpanel">
        <h3>{tier.name}</h3>
        <p className="carries">{tier.carries}</p>
        <div className="tierfacts">
          {tier.facts.map((f) => (
            <span key={f.label}>
              <strong>{f.value}</strong> {f.label.toLowerCase()}
            </span>
          ))}
        </div>
        {tier.id === "T1" ? <HunkViewer /> : null}
      </div>
    </div>
  );
}
