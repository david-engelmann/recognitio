import TierStepper from "./components/TierStepper";
import { manifestExcerpt, packetFacts, recountLines } from "./data/packet";

const repoUrl = "https://github.com/david-engelmann/recognitio";
const packetUrl = `${repoUrl}/tree/main/examples/example-packet-991ac6a`;

export default function Page() {
  return (
    <main>
      <header className="topbar">
        <div className="wrap">
          <span className="wordmark">
            recognitio<span className="dot">.</span>
          </span>
          <nav>
            <a href="#problem">The problem</a>
            <a href="#packet">The packet</a>
            <a href="#receipt">The receipt</a>
            <a href="#install">Install</a>
          </nav>
        </div>
      </header>

      <div className="wrap">
        <div className="hero">
          <span className="eyebrow">An agent skill for code review</span>
          <h1>The whole change, with its context, in one verified packet</h1>
          <p className="lede">
            Recognitio pulls the changes from a pull request or a commit range
            out of your local clone and assembles them into one review packet.
            The packet holds the change inside its enclosing functions, the
            call sites and tests that belong with it, and a recount that
            proves nothing was left behind.
          </p>
          <div className="receipt-strip" aria-label="Figures from the example packet">
            <div className="cell">
              <div className="num">{packetFacts.filesChanged}</div>
              <div className="lab">files in the example packet</div>
            </div>
            <div className="cell">
              <div className="num">{packetFacts.hunks}</div>
              <div className="lab">hunks carried in full</div>
            </div>
            <div className="cell">
              <div className="num">{packetFacts.addedLines}</div>
              <div className="lab">added lines, none deleted</div>
            </div>
            <div className="cell">
              <div className="num">
                {packetFacts.packetTokens.toLocaleString("en-US")}
              </div>
              <div className="lab">tokens in the packet estimate</div>
            </div>
            <div className="cell verified">
              <div className="num">Verified</div>
              <div className="lab">the recount matches the manifest</div>
            </div>
          </div>
          <p style={{ color: "var(--ink-2)", fontSize: 14, marginTop: 14 }}>
            Every figure on this page comes from one real packet shipped in
            the repository. It covers a single commit in recognitio itself,
            the one that taught the Devin gate to catch membership stated
            through a pure modifier chain. Open the packet and its manifest in{" "}
            <a href={packetUrl}>examples/example-packet-991ac6a</a> and check
            any figure on this page against them.
          </p>
        </div>

        <section id="problem">
          <h2>A diff alone is not what a reviewer reads</h2>
          <p className="section-lede">
            A reviewer reads the change inside its enclosing function, follows
            changed names to the places that call them, opens the tests that
            touch the changed module, and checks who shaped these lines in the
            past. The surfaces reviewers are handed do none of that, and some
            of them quietly hand over less than the whole change.
          </p>
          <div className="cards">
            <div className="card">
              <h3>Hosted diffs stop early</h3>
              <p>
                Hosted diff endpoints cap their file counts and drop
                oversized patches without a flag. A large pull request can be
                reviewed in part while everyone believes it was reviewed in
                whole.
              </p>
            </div>
            <div className="card">
              <h3>A fixed slice misses the shape</h3>
              <p>
                Most tools hand the reviewer a fixed slice of lines around
                each change and stay silent when the slice runs out. The
                enclosing function, the callers and the tests sit outside the
                slice.
              </p>
            </div>
            <div className="card">
              <h3>Silence is the failure</h3>
              <p>
                A missing file that stops the run is an inconvenience. A
                missing file that nobody mentions is a review built on a
                change that was never fully read. Recognitio takes the second
                failure off the table.
              </p>
            </div>
          </div>
        </section>

        <section id="packet">
          <h2>One packet, four tiers</h2>
          <p className="section-lede">
            The packet is built in four tiers and closes with a verification
            recount. Step through the tiers of the real example packet, and
            open the change tier to read one of its hunks.
          </p>
          <TierStepper />
          <p style={{ color: "var(--ink-2)", fontSize: 14, marginTop: 16 }}>
            The full packet runs to {packetFacts.packetLines} lines with all
            four tiers included and nothing dropped. It stands in the
            repository beside its manifest, and nothing in it was written or
            edited by hand.
          </p>
        </section>

        <section id="receipt">
          <h2>The receipt is part of the packet</h2>
          <p className="section-lede">
            A run writes two files into the output folder. The packet is the
            reading document, and the manifest beside it is the receipt, with
            the resolved refs, the command that produced it, the per file
            record, the tier accounting and the verified flag.
          </p>
          <div className="manifest-grid">
            <div>
              <div className="codeblock">{manifestExcerpt}</div>
              <p style={{ color: "var(--ink-2)", fontSize: 14 }}>
                Fields drawn from the real manifest of this packet, values
                exact. The full manifest ships beside the packet in the
                repository.
              </p>
              <div className="codeblock">{recountLines}</div>
              <p style={{ color: "var(--ink-2)", fontSize: 14 }}>
                The closing lines of the verification recount in this packet,
                word for word.
              </p>
            </div>
            <ul className="checklist">
              <li>
                <strong>Counted twice.</strong> After assembly the extractor
                recounts the changed files, their statuses, their hunks and
                their added and deleted lines with separate git invocations,
                and compares the recount against the manifest.
              </li>
              <li>
                <strong>Fails closed.</strong> A disagreement writes a
                manifest whose verified flag is false, prints the discrepancy
                and exits nonzero. A packet that failed its check is never
                reviewed as if it were whole.
              </li>
              <li>
                <strong>Caps are printed.</strong> When a search or a history
                read hits its cap, the packet prints the cap on its face.
                This packet does it in its history tier, and the tier stepper
                above shows the note.
              </li>
              <li>
                <strong>Verified has one meaning.</strong> Verified means
                this packet holds the whole change it names. It does not
                mean the change is correct, and it does not mean the change
                is safe.
              </li>
              <li>
                <strong>Local only.</strong> Extraction runs against the
                local clone, where there is no file count cap and the full
                history is present. The extractor takes no third party
                dependencies.
              </li>
            </ul>
          </div>
        </section>

        <section id="install">
          <h2>Take one route</h2>
          <p className="section-lede">
            Installing through two routes installs the skill twice, so take
            one. Every route needs Python 3.10 or newer and git, and pull
            request mode also needs the GitHub CLI. Pin the install to a
            commit SHA before you rely on it, because a skill ships executable
            code and an unpinned route can move under you.
          </p>
          <div className="install-grid">
            <div className="card">
              <h3>Claude Code plugin</h3>
              <p>
                Register the repo as a marketplace and install the plugin
                from its listing.
              </p>
              <div className="codeblock">
                /plugin marketplace add david-engelmann/recognitio{"\n"}
                /plugin install recognitio@recognitio-marketplace
              </div>
            </div>
            <div className="card">
              <h3>Any agent</h3>
              <p>
                The generic route works with any agent that reads the skill
                format.
              </p>
              <div className="codeblock">
                npx skills add david-engelmann/recognitio
              </div>
            </div>
            <div className="card">
              <h3>Folder copy</h3>
              <p>
                Copy the skill folder into any skills directory your agent
                reads.
              </p>
              <div className="codeblock">
                cp -r .agents/skills/recognitio ~/.claude/skills/recognitio
              </div>
            </div>
            <div className="card">
              <h3>A first run in sixty seconds</h3>
              <p>
                Inside a clone of the repo, build a packet for the same
                commit this page reads. A run that ends on the word verified
                has passed its recount.
              </p>
              <div className="codeblock">
                python3 .agents/skills/recognitio/scripts/extract.py \
                {"\n  "}--commit 991ac6a --out packet --repo .
              </div>
            </div>
          </div>
        </section>
      </div>

      <footer>
        <div className="wrap">
          <span>
            Recognitio is a Latin word for a formal re-examination of a
            matter with the record open. The packet it builds is the record
            the examination runs on.
          </span>
          <span>
            <a href={repoUrl}>The repository</a>
            {" · "}
            <a href={packetUrl}>The example packet</a>
          </span>
        </div>
      </footer>
    </main>
  );
}
