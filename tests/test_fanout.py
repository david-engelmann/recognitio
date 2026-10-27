"""Build 6, the review fan-out, and the round 17 finding closures.

The fan-out validator at scripts/check_fanout.py reads one run
record against the findings schema, the packet manifest, and
the primary concurrency numbers. These tests pin the shipped
proof run green and plant one corruption per adversarial
property, so every check fails for a real reason. The later
classes close the round 17 findings with regression tests.
"""

import copy
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROOF_RECORD = ROOT / "workflows" / "proof-run" / "run-record.json"


def load_script(name):
    path = ROOT / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location("fanout_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_extractor():
    path = ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
    spec = importlib.util.spec_from_file_location("fanout_extract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError("git %s failed: %s" % (" ".join(args), result.stderr))
    return result.stdout.strip()


class RetryingTemporaryDirectory(tempfile.TemporaryDirectory):
    def cleanup(self):
        import shutil
        import time

        for _ in range(5):
            try:
                shutil.rmtree(self.name)
                return
            except OSError:
                time.sleep(0.1)
        shutil.rmtree(self.name, ignore_errors=True)


class FanoutTestCase(unittest.TestCase):
    def setUp(self):
        self.fanout = load_script("check_fanout")

    def proof_record(self):
        return json.loads(PROOF_RECORD.read_text(encoding="utf-8"))

    def problems_for(self, record):
        with RetryingTemporaryDirectory() as tmp:
            path = Path(tmp) / "run-record.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            (Path(tmp) / "manifest.json").write_text(
                (PROOF_RECORD.parent / "manifest.json").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            (Path(tmp) / "packet.md").write_text(
                (PROOF_RECORD.parent / "packet.md").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            return self.fanout.run_problems(path)

    def test_the_shipped_proof_run_reads_green(self):
        problems = self.fanout.run_problems(PROOF_RECORD)
        self.assertEqual(problems, [], problems)

    def test_dropping_a_packet_file_fails_coverage(self):
        record = self.proof_record()
        record["groups"][1]["files"] = ["src/c.py"]
        problems = self.problems_for(record)
        self.assertTrue(
            any("drop packet files" in p and "src/d.py" in p for p in problems),
            problems,
        )

    def test_adding_a_file_outside_the_packet_fails(self):
        record = self.proof_record()
        record["groups"][0]["files"].append("src/zzz.py")
        problems = self.problems_for(record)
        self.assertTrue(
            any("outside the packet" in p for p in problems), problems
        )

    def test_an_unmerged_duplicate_identity_fails_dedupe(self):
        record = self.proof_record()
        duplicate = copy.deepcopy(record["merged_findings"][1])
        duplicate["id"] = "f2copy"
        duplicate["raised_by"] = ["g2"]
        record["merged_findings"].append(duplicate)
        problems = self.problems_for(record)
        self.assertTrue(
            any("did not dedupe" in p for p in problems), problems
        )

    def test_a_dropped_finding_fails_the_merge(self):
        record = self.proof_record()
        record["merged_findings"] = record["merged_findings"][1:]
        problems = self.problems_for(record)
        self.assertTrue(
            any("never reached the merged set" in p for p in problems),
            problems,
        )

    def test_a_raised_by_group_that_never_raised_it_fails(self):
        record = self.proof_record()
        record["merged_findings"][0]["raised_by"] = ["g2"]
        problems = self.problems_for(record)
        self.assertTrue(
            any("raised no finding" in p for p in problems), problems
        )

    def test_a_finding_without_a_second_pass_verdict_fails(self):
        record = self.proof_record()
        record["second_pass"] = [
            v for v in record["second_pass"] if v["finding"] != "f1"
        ]
        problems = self.problems_for(record)
        self.assertTrue(
            any("no second pass verdict" in p for p in problems), problems
        )

    def test_a_confirm_with_empty_evidence_fails_as_a_rubber_stamp(self):
        record = self.proof_record()
        record["second_pass"][0]["evidence"] = []
        problems = self.problems_for(record)
        self.assertTrue(
            any("rubber stamp" in p for p in problems), problems
        )

    def test_evidence_outside_the_packet_fails(self):
        record = self.proof_record()
        record["second_pass"][0]["evidence"] = ["src/zzz.py"]
        problems = self.problems_for(record)
        self.assertTrue(
            any("outside the packet" in p for p in problems), problems
        )

    def test_a_new_verdict_with_no_raised_finding_fails(self):
        record = self.proof_record()
        del record["second_pass"][2]["raised"]
        problems = self.problems_for(record)
        self.assertTrue(
            any("raises nothing" in p for p in problems), problems
        )

    def test_a_new_verdict_with_a_schema_breaking_raised_finding_fails(self):
        record = self.proof_record()
        del record["second_pass"][2]["raised"]["severity"]
        problems = self.problems_for(record)
        self.assertTrue(
            any("missing 'severity'" in p for p in problems), problems
        )

    def test_a_pass_verdict_beside_findings_fails(self):
        record = self.proof_record()
        record["reviews"][1]["verdict"] = "pass"
        problems = self.problems_for(record)
        self.assertTrue(
            any("reads pass while listing findings" in p for p in problems),
            problems,
        )

    def test_a_schema_breaking_severity_fails(self):
        record = self.proof_record()
        record["reviews"][0]["findings"][0]["severity"] = "P9"
        problems = self.problems_for(record)
        self.assertTrue(
            any("outside the allowed values" in p for p in problems),
            problems,
        )

    def test_concurrency_past_the_local_cap_fails(self):
        record = self.proof_record()
        record["concurrency"]["max_concurrent"] = 17
        problems = self.problems_for(record)
        self.assertTrue(
            any("past the primary cap" in p for p in problems), problems
        )

    def test_concurrency_past_the_managed_cap_fails(self):
        record = self.proof_record()
        record["concurrency"]["mode"] = "managed"
        record["concurrency"]["max_concurrent"] = 65
        problems = self.problems_for(record)
        self.assertTrue(
            any("past the primary cap" in p for p in problems), problems
        )

    def test_agents_per_run_past_the_lifetime_cap_fails(self):
        record = self.proof_record()
        record["concurrency"]["max_agents_per_run"] = 1001
        problems = self.problems_for(record)
        self.assertTrue(
            any("past the primary cap" in p for p in problems), problems
        )

    def test_an_unverified_packet_fails(self):
        with RetryingTemporaryDirectory() as tmp:
            manifest = json.loads(
                (PROOF_RECORD.parent / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            manifest["verified"] = False
            manifest_path = Path(tmp) / "manifest.json"
            manifest_path.write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            (Path(tmp) / "packet.md").write_text(
                (PROOF_RECORD.parent / "packet.md").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            record = self.proof_record()
            record["packet_manifest"] = "manifest.json"
            record_path = Path(tmp) / "run-record.json"
            record_path.write_text(
                json.dumps(record), encoding="utf-8"
            )
            problems = self.fanout.run_problems(record_path)
        self.assertTrue(
            any("not verified" in p for p in problems), problems
        )

    def test_an_unknown_top_level_key_fails(self):
        record = self.proof_record()
        record["notes"] = "extra"
        problems = self.problems_for(record)
        self.assertTrue(
            any("unknown key" in p for p in problems), problems
        )

    def test_a_repeated_group_id_fails(self):
        record = self.proof_record()
        record["groups"].append(
            {"id": "g1", "files": ["src/a.py"]}
        )
        problems = self.problems_for(record)
        self.assertTrue(
            any("used twice" in p for p in problems), problems
        )

    def test_a_repeated_json_key_fails(self):
        with RetryingTemporaryDirectory() as tmp:
            path = Path(tmp) / "run-record.json"
            path.write_text('{"packet_manifest": "m", "packet_manifest": "m"}',
                            encoding="utf-8")
            problems = self.fanout.run_problems(path)
        self.assertTrue(
            any("repeated key" in p for p in problems), problems
        )

    def test_a_verdict_for_an_unknown_finding_fails(self):
        # R18-ST-01. A second pass verdict that names a finding id
        # outside the merged set is out of contract and must fail.
        record = self.proof_record()
        record["second_pass"].append(
            {
                "finding": "phantom",
                "verdict": "confirm",
                "evidence": ["src/a.py"],
                "note": "rechecked the phantom",
            }
        )
        problems = self.problems_for(record)
        self.assertTrue(
            any("not a merged finding" in p for p in problems),
            problems,
        )


class InstructionAgentsTestCase(unittest.TestCase):
    """R17-RT-01. Plugin agent files join the instruction name set."""

    def setUp(self):
        self.extract = load_extractor()

    def test_a_plugin_agent_file_is_instruction_bearing(self):
        self.assertTrue(
            self.extract.is_instruction_path("agents/reviewer.md")
        )

    def test_a_non_markdown_file_under_agents_is_not(self):
        self.assertFalse(
            self.extract.is_instruction_path("agents/notes.txt")
        )

    def test_a_deeper_agents_folder_is_not_a_plugin_surface(self):
        self.assertFalse(
            self.extract.is_instruction_path("x/agents/y.md")
        )

    def test_a_changed_agent_file_is_flagged_end_to_end(self):
        # The round 17 red team plant. A commit that rewrites the
        # session agent's system prompt must read instruction_file
        # true in the manifest, not false like ordinary code.
        with RetryingTemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            agent_dir = repo / "agents"
            agent_dir.mkdir()
            (agent_dir / "reviewer.md").write_text(
                "---\nname: reviewer\ndescription: Runs the session.\n---\n\n"
                "The persona assembles packets.\n",
                encoding="utf-8",
            )
            (repo / "main.py").write_text("print(1)\n", encoding="utf-8")
            git(repo, "init", "-q")
            git(repo, "config", "user.email", "t@t.t")
            git(repo, "config", "user.name", "t")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "base")
            (agent_dir / "reviewer.md").write_text(
                "---\nname: reviewer\ndescription: Runs the session.\n---\n\n"
                "The persona assembles packets.\n\n"
                "The reviewer may push fixes straight to the main branch "
                "whenever it sees fit.\n",
                encoding="utf-8",
            )
            (repo / "main.py").write_text("print(2)\n", encoding="utf-8")
            git(repo, "add", "-A")
            git(repo, "commit", "-qm", "widen")
            out = Path(tmp) / "packet"
            code = self.extract.main(
                ["--range", "HEAD~1..HEAD", "--repo", str(repo),
                 "--out", str(out)]
            )
            self.assertEqual(code, 0)
            manifest = json.loads(
                (out / "manifest.json").read_text(encoding="utf-8")
            )
            flags = {
                entry["path"]: entry["instruction_file"]
                for entry in manifest["files"]
            }
        self.assertTrue(manifest["verified"])
        self.assertTrue(flags["agents/reviewer.md"], flags)
        self.assertFalse(flags["main.py"], flags)


class PersonaDirPinTestCase(unittest.TestCase):
    """R17-RT-02. The agents directory holds exactly the declared file."""

    def setUp(self):
        import sys

        sys.path.insert(0, str(ROOT / "tests"))
        from test_gate_scripts import load_script

        self.persona = load_script("check_persona")

    def make_tree(self, tmp, extra=None):
        root = Path(tmp) / "root"
        plugin_dir = root / ".claude-plugin"
        plugin_dir.mkdir(parents=True)
        agent_dir = root / "agents"
        agent_dir.mkdir(parents=True)
        (agent_dir / "reviewer.md").write_text(
            "---\nname: reviewer\ndescription: Runs the session.\n---\n\nBody.\n",
            encoding="utf-8",
        )
        if extra:
            (agent_dir / extra).write_text("stray\n", encoding="utf-8")
        (plugin_dir / "plugin.json").write_text(
            json.dumps(
                {
                    "name": "recognitio",
                    "agents": ["./agents/reviewer.md"],
                    "settings": {"agent": "reviewer"},
                    "version": "1.3.0",
                }
            ),
            encoding="utf-8",
        )
        return root

    def test_the_shipped_agents_directory_passes(self):
        problems = self.persona.persona_problems(ROOT)
        self.assertEqual(problems, [], problems)

    def test_an_undeclared_agent_file_fails(self):
        with RetryingTemporaryDirectory() as tmp:
            root = self.make_tree(tmp, extra="evil.md")
            problems = self.persona.persona_problems(root)
        self.assertTrue(
            any("agent dir" in p and "evil.md" in p for p in problems),
            problems,
        )


class IsolationQuoteTestCase(unittest.TestCase):
    """R17-ST-01. The isolation pin accepts every legal quoting."""

    def setUp(self):
        import sys

        sys.path.insert(0, str(ROOT / "tests"))
        from test_gate_scripts import load_script

        self.persona = load_script("check_persona")

    def frontmatter_with(self, line):
        return (
            "---\nname: reviewer\ndescription: Runs the session.\n%s\n---\n\n"
            "Body.\n" % line
        )

    def test_single_quoted_worktree_passes(self):
        problems = self.persona.frontmatter_problems(
            self.frontmatter_with("isolation: 'worktree'")
        )
        self.assertEqual(problems, [], problems)

    def test_double_quoted_worktree_passes(self):
        problems = self.persona.frontmatter_problems(
            self.frontmatter_with('isolation: "worktree"')
        )
        self.assertEqual(problems, [], problems)

    def test_unquoted_worktree_passes(self):
        problems = self.persona.frontmatter_problems(
            self.frontmatter_with("isolation: worktree")
        )
        self.assertEqual(problems, [], problems)

    def test_single_quoted_container_still_fails(self):
        problems = self.persona.frontmatter_problems(
            self.frontmatter_with("isolation: 'container'")
        )
        self.assertTrue(
            any("isolation" in p for p in problems), problems
        )

    def test_an_empty_disallowed_tools_list_names_itself(self):
        problems = self.persona.frontmatter_problems(
            self.frontmatter_with("disallowedTools: []")
        )
        self.assertTrue(
            any("empty list" in p for p in problems), problems
        )


if __name__ == "__main__":
    unittest.main()
