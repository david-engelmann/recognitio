#!/usr/bin/env python3
"""Smoke test the extractor end to end on a throwaway repository.

Builds a tiny git history in a temporary directory, runs the bundled
extractor on the range between the two commits, and asserts that the
manifest it writes reports the packet as verified. This is the proof
that the shipped script runs against real git objects rather than
only inside the unit suite.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / "skills" / "recognitio" / "scripts" / "extract.py"

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


def git(repo, *args):
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        env=GIT_ENV,
        capture_output=True,
        text=True,
    )


def main():
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        repo.mkdir()
        git(repo, "init", "-q")
        (repo / "calc.py").write_text(MODULE_V1, encoding="utf-8")
        git(repo, "add", "calc.py")
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
            print("smoke_extract: extractor exited %d" % run.returncode, file=sys.stderr)
            print(run.stdout, file=sys.stderr)
            print(run.stderr, file=sys.stderr)
            return 1

        manifest_path = out / "manifest.json"
        if not manifest_path.is_file():
            print("smoke_extract: no manifest was written", file=sys.stderr)
            return 1
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("verified") is not True:
            print("smoke_extract: manifest does not report verified", file=sys.stderr)
            return 1
        packet = out / "packet.md"
        if not packet.is_file() or not packet.read_text(encoding="utf-8").strip():
            print("smoke_extract: packet is missing or empty", file=sys.stderr)
            return 1
    print("smoke_extract: extractor produced a verified packet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
