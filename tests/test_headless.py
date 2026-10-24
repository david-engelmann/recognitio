"""The headless review gate, Build 4 of the adaptation plan.

The gate fails a headless run closed on every shape the docs
cannot verify. Each test plants one failure shape from
docs/headless-review.md against the check script and asserts
the gate names it, and the clean run reads green.
"""

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_headless():
    path = ROOT / "scripts" / "check_headless.py"
    spec = importlib.util.spec_from_file_location(
        "gate_check_headless", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


headless = load_headless()

MANIFEST_FILES = ["src/app.py", "src/lib.py"]


def result_event(**fields):
    event = {"type": "result"}
    event.update(fields)
    return event


def clean_structured():
    return {
        "verdict": "pass",
        "findings": [
            {
                "severity": "low",
                "location": "src/app.py:12",
                "evidence": ["src/app.py"],
            }
        ],
    }


class TestHeadlessCheck(unittest.TestCase):
    """The fail closed contract of the headless review shape."""

    def check(self, exit_code, events):
        return headless.headless_problems(
            exit_code, events, MANIFEST_FILES
        )

    def test_a_clean_run_reads_green(self):
        events = [
            result_event(
                permission_denials=[],
                structured_output={
                    "verdict": "pass",
                    "findings": [],
                },
            )
        ]
        self.assertEqual(self.check(0, events), [])

    def test_a_nonzero_exit_fails_the_run(self):
        problems = self.check(1, [])
        self.assertTrue(
            any("exited 1" in problem for problem in problems), problems
        )

    def test_a_stream_with_no_result_message_fails(self):
        problems = self.check(
            0, [{"type": "assistant", "message": {}}]
        )
        self.assertTrue(
            any("no result message" in problem for problem in problems),
            problems,
        )

    def test_permission_denials_fail_the_run(self):
        events = [
            {"type": "system", "subtype": "permission_denied"},
            result_event(
                permission_denials=[{"tool": "Bash"}],
                structured_output={
                    "verdict": "pass",
                    "findings": [],
                },
            ),
        ]
        problems = self.check(0, events)
        self.assertTrue(
            any("permission denials" in problem for problem in problems),
            problems,
        )

    def test_a_run_without_structured_output_fails(self):
        # The docs say a run that ends without valid structured
        # output carries no structured_output field, so the gate
        # must fail on the missing field rather than read the
        # run as clean.
        events = [
            result_event(
                permission_denials=[],
                result="I cannot review this packet.",
            )
        ]
        problems = self.check(0, events)
        self.assertTrue(
            any("no structured output" in problem for problem in problems),
            problems,
        )

    def test_an_in_run_failure_printed_as_the_result_fails(self):
        # A failure inside the run prints as the result on
        # stdout, so exit zero is not proof of a clean run.
        events = [
            result_event(
                permission_denials=[],
                result="Error: missing authentication",
            )
        ]
        problems = self.check(0, events)
        self.assertTrue(problems, problems)
        self.assertTrue(
            any("no structured output" in problem for problem in problems),
            problems,
        )

    def test_schema_drift_fails_the_gate(self):
        events = [
            result_event(
                permission_denials=[],
                structured_output={"verdict": "pass"},
            )
        ]
        problems = self.check(0, events)
        self.assertTrue(
            any("not a list" in problem for problem in problems), problems
        )

    def test_a_wrong_verdict_value_fails_the_gate(self):
        structured = clean_structured()
        structured["verdict"] = "maybe"
        events = [
            result_event(
                permission_denials=[], structured_output=structured
            )
        ]
        problems = self.check(0, events)
        self.assertTrue(
            any("not pass or fail" in problem for problem in problems),
            problems,
        )

    def test_a_finding_missing_keys_fails_the_gate(self):
        structured = {"verdict": "fail", "findings": [{"severity": "high"}]}
        events = [
            result_event(
                permission_denials=[], structured_output=structured
            )
        ]
        problems = self.check(0, events)
        self.assertTrue(
            any("missing" in problem for problem in problems), problems
        )

    def test_evidence_outside_the_packet_fails_the_gate(self):
        structured = {
            "verdict": "fail",
            "findings": [
                {
                    "severity": "high",
                    "location": "src/ghost.py:1",
                    "evidence": ["src/ghost.py"],
                }
            ],
        }
        events = [
            result_event(
                permission_denials=[], structured_output=structured
            )
        ]
        problems = self.check(0, events)
        self.assertTrue(
            any("outside the packet" in problem for problem in problems),
            problems,
        )

    def test_a_pass_verdict_with_findings_fails_the_gate(self):
        structured = {
            "verdict": "pass",
            "findings": [
                {
                    "severity": "low",
                    "location": "src/app.py:1",
                    "evidence": ["src/app.py"],
                }
            ],
        }
        events = [
            result_event(
                permission_denials=[], structured_output=structured
            )
        ]
        problems = self.check(0, events)
        self.assertTrue(
            any("contradict" in problem or "while the run lists" in problem
                for problem in problems),
            problems,
        )

    def test_a_failing_run_with_evidence_reads_green(self):
        structured = {
            "verdict": "fail",
            "findings": [
                {
                    "severity": "high",
                    "location": "src/lib.py:40",
                    "evidence": ["src/lib.py"],
                }
            ],
        }
        events = [
            result_event(
                permission_denials=[], structured_output=structured
            )
        ]
        self.assertEqual(self.check(0, events), [])

    def test_the_doc_schema_matches_what_the_gate_enforces(self):
        doc = (ROOT / "docs" / "headless-review.md").read_text(
            encoding="utf-8"
        )
        match = re.search(r"```json\n(.*?)```", doc, re.DOTALL)
        self.assertIsNotNone(match)
        schema = json.loads(match.group(1))
        self.assertEqual(schema["required"], ["verdict", "findings"])
        self.assertEqual(
            schema["properties"]["findings"]["items"]["required"],
            ["severity", "location", "evidence"],
        )

    def test_the_cli_fails_a_denied_run_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            stream = Path(tmp) / "run.jsonl"
            manifest = Path(tmp) / "manifest.json"
            stream.write_text(
                json.dumps(
                    result_event(
                        permission_denials=[{"tool": "Bash"}],
                        structured_output={
                            "verdict": "pass",
                            "findings": [],
                        },
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            manifest.write_text(
                json.dumps(
                    {"files": [{"path": path} for path in MANIFEST_FILES]}
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "check_headless.py"),
                    "--stream",
                    str(stream),
                    "--manifest",
                    str(manifest),
                    "--exit-code",
                    "0",
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("permission denials", result.stdout)

    def test_the_cli_reads_a_clean_run_green(self):
        with tempfile.TemporaryDirectory() as tmp:
            stream = Path(tmp) / "run.jsonl"
            manifest = Path(tmp) / "manifest.json"
            stream.write_text(
                json.dumps(
                    result_event(
                        permission_denials=[],
                        structured_output={
                            "verdict": "pass",
                            "findings": [],
                        },
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            manifest.write_text(
                json.dumps(
                    {"files": [{"path": path} for path in MANIFEST_FILES]}
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "check_headless.py"),
                    "--stream",
                    str(stream),
                    "--manifest",
                    str(manifest),
                    "--exit-code",
                    "0",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout)


if __name__ == "__main__":
    unittest.main()
