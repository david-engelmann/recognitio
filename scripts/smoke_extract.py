#!/usr/bin/env python3
"""Smoke test the extractor end to end on a throwaway repository.

Builds a tiny git history in a temporary directory, runs the bundled
extractor on the range between the two commits, and asserts that the
manifest it writes reports the packet as verified and that the packet
carries real companion and history content. The packet check script
then validates the same output the way a reviewer would before
stamping a gate report. This is the proof that the shipped script
runs against real git objects rather than only inside the unit suite.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "skills" / "recognitio" / "scripts" / "extract.py"
CHECK_PACKET = ROOT / "scripts" / "check_packet.py"

import os

GIT_ENV = dict(
    os.environ,
    GIT_AUTHOR_NAME="Recognitio Smoke",
    GIT_AUTHOR_EMAIL="smoke@example.invalid",
    GIT_COMMITTER_NAME="Recognitio Smoke",
    GIT_COMMITTER_EMAIL="smoke@example.invalid",
)

MODULE_V1 = '''"""Fixture module for the smoke run."""


def total(values):
    result = 0
    for value in values:
        result += value
    return result
'''

MODULE_V2 = MODULE_V1.replace("result = 0", "result = 1")

CALLER = '''from calc import total


def run():
    return total([1, 2, 3])
'''

TEST_CALC = '''from calc import total


def test_total():
    assert total([1, 2]) == 3
'''


def git(repo, *args):
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        env=GIT_ENV,
        capture_output=True,
        text=True,
    )


def fail(message, run=None):
    print("smoke_extract: %s" % message, file=sys.stderr)
    if run is not None:
        print(run.stdout, file=sys.stderr)
        print(run.stderr, file=sys.stderr)
    return 1


def main():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        (repo / "calc.py").write_text(MODULE_V1, encoding="utf-8")
        (repo / "caller.py").write_text(CALLER, encoding="utf-8")
        (repo / "test_calc.py").write_text(TEST_CALC, encoding="utf-8")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "first")
        (repo / "calc.py").write_text(MODULE_V2, encoding="utf-8")
        git(repo, "add", "calc.py")
        git(repo, "commit", "-q", "-m", "second")

        out = Path(tmp) / "out"
        run = subprocess.run(
            [
                sys.executable,
                str(EXTRACT),
                "--range",
                "HEAD~1..HEAD",
                "--out",
                str(out),
                "--repo",
                str(repo),
            ],
            capture_output=True,
            text=True,
        )
        if run.returncode != 0:
            return fail("extractor exited %d" % run.returncode, run)

        manifest_path = out / "manifest.json"
        if not manifest_path.is_file():
            return fail("no manifest was written")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("verified") is not True:
            return fail("manifest does not report verified")
        packet_path = out / "packet.md"
        if not packet_path.is_file():
            return fail("packet is missing")
        packet = packet_path.read_text(encoding="utf-8")
        if not packet.strip():
            return fail("packet is empty")
        for needle in (
            "Call sites for total",
            "caller.py",
            "test_calc.py",
            "Blame summary for changed ranges",
        ):
            if needle not in packet:
                return fail("packet is missing expected content: %s" % needle)

        check = subprocess.run(
            [
                sys.executable,
                str(CHECK_PACKET),
                str(out),
                "--repo",
                str(repo),
            ],
            capture_output=True,
            text=True,
        )
        if check.returncode != 0:
            return fail("packet check rejected the smoke packet", check)
    print("smoke_extract: extractor produced a verified packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
