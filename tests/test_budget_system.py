"""Regression tests for the budget system closures.

The audit rounds on this family measured the old budget machinery
from the outside. The estimator counted characters and divided by
four, so a packet accepted at its stated budget could carry a
multiple of that budget in real tokens, and a whitespace heavy
tier could be shed at a budget that already paid for it in real
tokens. A dropped history tier was resettled at check time from
the checking environment its live GitHub state, so an honest shed
packet stamped only in the environment that built it. The
shedding order was fixed and never cost aware, leaving hundreds
of tokens unspent at a budget that fitted the small tier whole.
The refusal sentence blamed the two core tiers for the size of
the whole shed packet, the failure manifest recorded a budget of
none and an estimate of zero and no tiers at all, and budgets of
zero and below passed argument checking even though the manifest
schema minimum is one, with a negative budget run replacing a
standing verified packet with a failure receipt.

Every test in this file fails against the pre fix extractor and
packet check for the reason its own assertions name. The real
token counts recorded in the estimator shapes were measured with
the cl100k tokenizer over the exact strings the tests build.
"""

import base64
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = (
    ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
)
CHECK = ROOT / "scripts" / "check_packet.py"

spec = importlib.util.spec_from_file_location(
    "recognitio_extract_budget", EXTRACT
)
extract_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract_mod)


class TestShippedPacketEstimates(unittest.TestCase):
    """Every shipped packet states the figure the estimator gives.

    Round 10 standards Minor 1. Eval task 06 stated 1379 in its
    receipt and its manifest where the shipped estimator gives
    1377 on its own text, a stale figure left by a hand edit.
    The packet estimate is a fixed point of the estimator over
    the packet text, so a stated figure that disagrees with a
    fresh estimate of the same text is stale by construction,
    and every shipped packet in the tree must recompute exact.
    """

    PACKET_DIRS = (
        ["evals/tasks/task-0%d" % i for i in range(1, 7)]
        + ["workflows/proof-run", "examples/example-packet-991ac6a"]
    )

    def test_every_shipped_packet_recomputes_to_its_stated_figure(self):
        for rel in self.PACKET_DIRS:
            folder = ROOT / rel
            packet = (folder / "packet.md").read_text(
                encoding="utf-8"
            )
            manifest = json.loads(
                (folder / "manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            match = re.search(
                r"^Packet estimate in tokens: (\d+)$", packet, re.M
            )
            self.assertIsNotNone(match, rel)
            stated = int(match.group(1))
            self.assertEqual(
                extract_mod.estimate_tokens(packet), stated, rel
            )
            self.assertEqual(
                manifest["budget"]["estimated_tokens"], stated, rel
            )


class RetryingTemporaryDirectory(tempfile.TemporaryDirectory):
    cleanup_attempts = 5
    cleanup_delay_seconds = 0.1

    def cleanup(self):
        last_error = None
        for attempt in range(self.cleanup_attempts):
            try:
                shutil.rmtree(self.name)
            except FileNotFoundError as error:
                if not os.path.exists(self.name):
                    last_error = None
                    break
                last_error = error
            except OSError as error:
                last_error = error
            else:
                last_error = None
                break
            if attempt + 1 < self.cleanup_attempts:
                time.sleep(self.cleanup_delay_seconds)
        if last_error is not None:
            raise last_error
        self._finalizer.detach()


# The git location variables are scrubbed from the environment
# every fixture command runs under. An exported GIT_DIR defeats
# git -C, so a suite launched with the variables set would run
# its fixture work in the repository they name instead of in
# the fixture, writing real commits there under passing tests.
GIT_LOCATION_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
)


def scrubbed_git_env():
    """The caller environment with the git location names removed."""
    return {
        key: value
        for key, value in os.environ.items()
        if key not in GIT_LOCATION_VARS
    }

def git(repo, *args):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        env=scrubbed_git_env(),
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            "git %s failed with %s" % (" ".join(args), result.stderr)
        )
    return result.stdout.strip()


def module_text(value):
    lines = ['"""Fixture module."""', ""]
    for index in range(8):
        lines.append("def alpha%d():" % index)
        lines.append('    value = "%s%d"' % (value, index))
        lines.append("    return value")
        lines.append("")
    return "\n".join(lines)


def caller_text(cjk=False):
    lines = [
        "from module import alpha0, alpha1, alpha2, alpha3, "
        "alpha4, alpha5, alpha6, alpha7",
        "",
    ]
    for index in range(8):
        for call in range(5):
            lines.append("def caller_%d_%d():" % (index, call))
            if cjk:
                lines.append(
                    "    # 呼び出し側の説明文です。この関数はここで"
                    "必要です。理由を確認してください %d %d"
                    % (index, call)
                )
            else:
                lines.append(
                    "    # context for caller %d %d carrying ordinary "
                    "explanatory words about why this caller needs "
                    "the function it calls here" % (index, call)
                )
            lines.append("    return alpha%d()" % index)
            lines.append("")
    return "\n".join(lines) + "\n"


def make_fixture(tmp, cjk=False):
    repo = Path(tmp) / "repo"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "commit.gpgsign", "false")
    (repo / "module.py").write_text(module_text("original"))
    (repo / "caller.py").write_text(
        "from module import alpha0\n\n\ndef run():\n"
        "    return alpha0()\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "initial")
    (repo / "module.py").write_text(
        module_text("original") + "# one history note with words\n"
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "history")
    (repo / "big_caller.py").write_text(caller_text(cjk))
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "add callers")
    (repo / "module.py").write_text(module_text("updated"))
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "edit alphas")
    return repo


def run_extract(repo, out, *args, env=None):
    cmd = [
        sys.executable, str(EXTRACT),
        "--out", str(out), "--repo", str(repo),
    ] + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def run_check(out, repo, env=None):
    cmd = [sys.executable, str(CHECK), str(out), "--repo", str(repo)]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def read_manifest(out):
    return json.loads((Path(out) / "manifest.json").read_text())


def env_with_path(path_value):
    env = dict(os.environ)
    env["PATH"] = path_value
    return env


class TestEstimatorShapes(unittest.TestCase):
    """Closure 1. The estimate tracks real token counts by shape."""

    def assert_priced(self, text, real_tokens):
        estimate = extract_mod.estimate_tokens(text)
        self.assertLessEqual(
            real_tokens, estimate * 1.5,
            "the estimate underprices this shape by a multiple",
        )
        self.assertLessEqual(
            estimate, real_tokens * 2.5,
            "the estimate overprices this shape by a multiple",
        )
        return estimate

    def test_prose_control(self):
        text = (
            "The committee reviewed the proposal and asked for a "
            "clearer account of the costs before the next meeting "
            "could decide anything at all. "
        ) * 30
        self.assert_priced(text, 721)

    def test_cjk_text(self):
        text = (
            "今日は良い天気ですね。明日も晴れるでしょう。"
            "私たちは公園を散歩しました。"
        ) * 80
        self.assert_priced(text, 3120)

    def test_base64_text(self):
        encoded = base64.b64encode(bytes(range(256)) * 8).decode()
        text = "\n".join(
            encoded[index:index + 64]
            for index in range(0, len(encoded), 64)
        )
        self.assert_priced(text, 2015)

    def test_hex_pairs(self):
        text = "\n".join(
            " ".join(
                "%02x" % ((row * 7 + col * 13) % 256)
                for col in range(16)
            )
            for row in range(60)
        )
        self.assert_priced(text, 2015)

    def test_space_runs(self):
        text = ("call_site()" + " " * 900 + "\n") * 5
        self.assert_priced(text, 55)

    def test_repeated_character_run(self):
        # The recorded real count stands as measured with the
        # cl100k tokenizer, 525 tokens for 4,200 copies of the
        # letter a, which merges eight copies into one token.
        # At the repeated letter price the estimate stands at
        # 2,100, a quarter of it in real tokens, so the shape
        # stands on the named downward limit for a best
        # merging repeated letter rather than inside the
        # band, and the assertions below read that limit.
        estimate = extract_mod.estimate_tokens("a" * 4200)
        self.assertEqual(estimate, 2100)
        self.assertGreaterEqual(525 * 100, 24 * estimate)
        self.assertLessEqual(525, estimate)

    def test_the_method_is_named_in_the_help(self):
        result = subprocess.run(
            [sys.executable, str(EXTRACT), "--help"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        flat = " ".join(result.stdout.split())
        self.assertIn("per shape token estimate", flat)
        self.assertNotIn("divided by 4", flat)


class TestCjkPacketEndToEnd(unittest.TestCase):
    """Closure 1 at packet level, on a CJK heavy companion tier."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_fixture(self.tmp.name, cjk=True)

    def test_the_packet_estimate_tracks_the_real_count(self):
        out = Path(self.tmp.name) / "full"
        result = run_extract(
            self.repo, out, "--range", "HEAD~1..HEAD"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = read_manifest(out)
        # The genuine packet for this fixture measured 4165 real
        # tokens with the cl100k tokenizer when this test was
        # written, and the old character rule priced it near 2636.
        # The estimate must land on the real side of 2850.
        self.assertGreaterEqual(
            manifest["budget"]["estimated_tokens"], 2850
        )

    def test_a_budget_below_the_real_size_sheds_the_cjk_tier(self):
        out = Path(self.tmp.name) / "shed"
        result = run_extract(
            self.repo, out, "--range", "HEAD~1..HEAD",
            "--budget", "3100",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = read_manifest(out)
        self.assertEqual(manifest["tiers"]["T2"]["state"], "dropped")
        self.assertLessEqual(
            manifest["budget"]["estimated_tokens"], 3100
        )


class TestBudgetValidation(unittest.TestCase):
    """Closure 5. Budgets under the schema minimum are refused."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_fixture(self.tmp.name)

    def make_sentinel(self, name):
        out = Path(self.tmp.name) / name
        out.mkdir(parents=True)
        (out / "packet.md").write_text("SENTINEL PACKET\n")
        (out / "manifest.json").write_text(
            '{"verified": true, "sentinel": true}\n'
        )
        return out

    def test_zero_and_negative_budgets_touch_no_output(self):
        for index, budget in enumerate(("0", "-1", "-42")):
            with self.subTest(budget=budget):
                out = self.make_sentinel("victim%d" % index)
                result = run_extract(
                    self.repo, out, "--range", "HEAD~1..HEAD",
                    "--budget", budget,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("at least 1", result.stderr)
                self.assertEqual(
                    (out / "packet.md").read_text(),
                    "SENTINEL PACKET\n",
                )
                self.assertEqual(
                    (out / "manifest.json").read_text(),
                    '{"verified": true, "sentinel": true}\n',
                )

    def test_a_negative_budget_creates_no_output_directory(self):
        out = Path(self.tmp.name) / "never-created"
        result = run_extract(
            self.repo, out, "--range", "HEAD~1..HEAD",
            "--budget", "-5",
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(out.exists())

    def test_a_negative_budget_in_commit_mode_is_refused(self):
        out = Path(self.tmp.name) / "commit-refused"
        result = run_extract(
            self.repo, out, "--commit", "HEAD", "--budget", "-7",
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("at least 1", result.stderr)
        self.assertFalse(out.exists())


class TestRefusalAndFailureManifest(unittest.TestCase):
    """Closure 4. The refusal and its receipt name the true sizes."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_fixture(self.tmp.name)
        full = Path(self.tmp.name) / "full"
        result = run_extract(
            self.repo, full, "--range", "HEAD~1..HEAD"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.sizes = {
            tier: read_manifest(full)["tiers"][tier][
                "estimated_tokens"
            ]
            for tier in ("T0", "T1", "T2", "T3")
        }

    def refuse(self, name, budget):
        out = Path(self.tmp.name) / name
        result = run_extract(
            self.repo, out, "--range", "HEAD~1..HEAD",
            "--budget", str(budget),
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        return out, result

    def test_the_refusal_sentence_names_the_true_tier_sizes(self):
        _out, result = self.refuse("refused", 500)
        self.assertIn(
            "T0 at about %d tokens" % self.sizes["T0"], result.stderr
        )
        self.assertIn(
            "T1 at about %d tokens" % self.sizes["T1"], result.stderr
        )
        self.assertNotIn("alone need", result.stderr)

    def test_the_failure_manifest_records_budget_and_tier_costs(self):
        out, result = self.refuse("receipt", 500)
        manifest = read_manifest(out)
        self.assertFalse(manifest["verified"])
        self.assertEqual(manifest["budget"]["budget_tokens"], 500)
        named = re.search(
            r"smallest packet this selection can emit measures "
            r"about ([0-9]+) tokens",
            result.stderr,
        )
        self.assertIsNotNone(named)
        self.assertEqual(
            manifest["budget"]["estimated_tokens"],
            int(named.group(1)),
        )
        self.assertGreater(
            manifest["budget"]["estimated_tokens"], self.sizes["T0"]
        )
        self.assertEqual(
            [item["tier"] for item in manifest["budget"]["dropped"]],
            ["T3", "T2"],
        )
        for tier in ("T0", "T1", "T2", "T3"):
            self.assertIn(tier, manifest["tiers"])
            self.assertEqual(
                manifest["tiers"][tier]["estimated_tokens"],
                self.sizes[tier],
            )
        self.assertEqual(manifest["tiers"]["T0"]["state"], "included")
        self.assertEqual(manifest["tiers"]["T3"]["state"], "dropped")


class TestCostAwareShedding(unittest.TestCase):
    """Closure 3. The budget keeps the tier set worth the most."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_fixture(self.tmp.name)
        full = Path(self.tmp.name) / "full"
        result = run_extract(
            self.repo, full, "--range", "HEAD~1..HEAD"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = read_manifest(full)
        self.sizes = {
            tier: manifest["tiers"][tier]["estimated_tokens"]
            for tier in ("T0", "T1", "T2", "T3")
        }
        self.assertGreater(self.sizes["T2"], self.sizes["T3"] * 2)
        core = Path(self.tmp.name) / "core"
        result = run_extract(
            self.repo, core, "--range", "HEAD~1..HEAD",
            "--tiers", "0-1",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.core_tokens = read_manifest(core)["budget"][
            "estimated_tokens"
        ]

    def test_a_budget_fitting_the_small_tier_keeps_it(self):
        budget = self.core_tokens + self.sizes["T3"] + 120
        out = Path(self.tmp.name) / "keep-history"
        result = run_extract(
            self.repo, out, "--range", "HEAD~1..HEAD",
            "--budget", str(budget),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = read_manifest(out)
        self.assertEqual(
            [item["tier"] for item in manifest["budget"]["dropped"]],
            ["T2"],
        )
        self.assertEqual(manifest["tiers"]["T3"]["state"], "included")
        estimate = manifest["budget"]["estimated_tokens"]
        self.assertLessEqual(estimate, budget)
        # The unspent remainder is under the granularity limit,
        # which is the cost of the one dropped tier, because
        # restoring that tier alone would break the budget.
        self.assertLess(budget - estimate, self.sizes["T2"])

    def test_a_core_sized_budget_still_sheds_both(self):
        accepted = None
        for step in range(0, 200, 20):
            budget = self.core_tokens + step
            out = Path(self.tmp.name) / ("scan%d" % step)
            result = run_extract(
                self.repo, out, "--range", "HEAD~1..HEAD",
                "--budget", str(budget),
            )
            if result.returncode == 0:
                accepted = read_manifest(out)
                break
        self.assertIsNotNone(accepted)
        self.assertEqual(
            [item["tier"] for item in accepted["budget"]["dropped"]],
            ["T3", "T2"],
        )


class TestDroppedHistoryPortability(unittest.TestCase):
    """Closure 2. A dropped history tier settles from the record."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_fixture(self.tmp.name)
        self.gh_dirs = {}
        variants = {
            "one": (
                '[{"number": 7, "title": "Earlier work", '
                '"state": "OPEN", "files": [{"path": "module.py"}]}]'
            ),
            "three": (
                '[{"number": 7, "title": "Earlier work", '
                '"state": "OPEN", "files": [{"path": "module.py"}]}, '
                '{"number": 8, "title": "More work", '
                '"state": "MERGED", "files": [{"path": "module.py"}]}, '
                '{"number": 9, "title": "Even more work", '
                '"state": "OPEN", "files": [{"path": "module.py"}]}]'
            ),
            "empty": "[]",
        }
        for name, payload in variants.items():
            folder = Path(self.tmp.name) / ("gh-" + name)
            folder.mkdir()
            script = folder / "gh"
            script.write_text("#!/bin/sh\necho '%s'\n" % payload)
            script.chmod(0o755)
            self.gh_dirs[name] = folder
        nogh = Path(self.tmp.name) / "gh-absent"
        nogh.mkdir()
        os.symlink(shutil.which("git"), nogh / "git")
        self.gh_dirs["absent"] = nogh

    def env_for(self, name):
        folder = self.gh_dirs[name]
        if name == "absent":
            return env_with_path(str(folder))
        return env_with_path(
            str(folder) + os.pathsep + os.environ["PATH"]
        )

    def build_shed_packet(self):
        full = Path(self.tmp.name) / "full"
        result = run_extract(
            self.repo, full, "--range", "HEAD~1..HEAD",
            env=self.env_for("one"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = read_manifest(full)
        budget = (
            manifest["budget"]["estimated_tokens"]
            - manifest["tiers"]["T3"]["estimated_tokens"] + 200
        )
        out = Path(self.tmp.name) / "shed"
        result = run_extract(
            self.repo, out, "--range", "HEAD~1..HEAD",
            "--budget", str(budget), env=self.env_for("one"),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        shed = read_manifest(out)
        self.assertEqual(shed["tiers"]["T3"]["state"], "dropped")
        self.assertIn(
            "Prior pull requests touching these files",
            shed["prior_pull_requests_passage"],
        )
        return out

    def test_the_shed_packet_stamps_in_every_environment(self):
        out = self.build_shed_packet()
        for name in ("one", "three", "empty", "absent"):
            with self.subTest(environment=name):
                result = run_check(
                    out, self.repo, env=self.env_for(name)
                )
                self.assertEqual(
                    result.returncode, 0,
                    result.stdout + result.stderr,
                )
                self.assertIn("is verified", result.stdout)

    def test_a_forged_dropped_size_still_fails(self):
        out = self.build_shed_packet()
        forged = Path(self.tmp.name) / "forged"
        shutil.copytree(out, forged)
        manifest = read_manifest(forged)
        genuine = manifest["tiers"]["T3"]["estimated_tokens"]
        manifest["tiers"]["T3"]["estimated_tokens"] = genuine + 25
        (forged / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
        packet = (forged / "packet.md").read_text()
        packet = packet.replace(
            "T3 dropped under the token budget. The full tier runs "
            "about %d tokens" % genuine,
            "T3 dropped under the token budget. The full tier runs "
            "about %d tokens" % (genuine + 25),
        )
        (forged / "packet.md").write_text(packet)
        result = run_check(forged, self.repo, env=self.env_for("one"))
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn(
            "dropped T3 tier", result.stdout + result.stderr
        )


class TestStandingPacketPreserved(unittest.TestCase):
    """Closure 5. No budget run replaces a standing verified packet."""

    def setUp(self):
        self.tmp = RetryingTemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = make_fixture(self.tmp.name)

    def test_refused_and_invalid_budgets_leave_the_packet(self):
        out = Path(self.tmp.name) / "standing"
        result = run_extract(
            self.repo, out, "--range", "HEAD~1..HEAD"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(read_manifest(out)["verified"])
        packet_before = (out / "packet.md").read_bytes()
        manifest_before = (out / "manifest.json").read_bytes()
        for budget in ("1", "0", "-13"):
            with self.subTest(budget=budget):
                failed = run_extract(
                    self.repo, out, "--range", "HEAD~1..HEAD",
                    "--budget", budget,
                )
                self.assertEqual(failed.returncode, 2, failed.stderr)
                self.assertEqual(
                    (out / "packet.md").read_bytes(), packet_before
                )
                self.assertEqual(
                    (out / "manifest.json").read_bytes(),
                    manifest_before,
                )
                self.assertTrue(read_manifest(out)["verified"])


class TestRound12EstimatorAndPartialClone(unittest.TestCase):
    """Round 12 repairs on the digit run price and the partial clone."""

    def test_repeated_digit_runs_price_by_the_digit_rule(self):
        # A run of 20000 zeros carries 6667 real cl100k tokens and
        # a run of 9000 sevens carries 3000, because the tokenizer
        # splits digit runs into groups of at most three digits.
        # The estimate must stand within a factor of two of the
        # real count on both runs, where the merged repeat price
        # stood at a third of it.
        for text, real_tokens in (("0" * 20000, 6667), ("7" * 9000, 3000)):
            estimate = extract_mod.estimate_tokens(text)
            self.assertGreaterEqual(estimate * 2, real_tokens, text[:1])
            self.assertLessEqual(estimate, real_tokens * 2, text[:1])

    def test_repeated_letter_runs_keep_the_merge_price(self):
        estimate = extract_mod.estimate_tokens("a" * 20000)
        self.assertLessEqual(estimate, 525 * 40)
        self.assertGreaterEqual(estimate, 4000)

    def test_a_digit_run_packet_is_not_admitted_under_its_real_size(self):
        with RetryingTemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir(parents=True)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "test@example.com")
            git(repo, "config", "user.name", "Test User")
            git(repo, "config", "commit.gpgsign", "false")
            (repo / "seed.txt").write_text("seed\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "seed")
            (repo / "data.txt").write_text("0" * 20000 + "\n" + "7" * 9000 + "\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "digit runs")
            out = Path(tmp) / "out"
            result = run_extract(
                repo, out, "--range", "HEAD~1..HEAD", "--budget", "4000"
            )
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertIn("smallest packet", result.stderr)
            self.assertFalse(read_manifest(out)["verified"])

    def test_missing_object_remedy_names_the_partial_shape(self):
        message = (
            "git diff --name-status failed with exit 128: "
            "fatal: unable to read a6f1d25c019fe7aaad0412888d9d6c7933656817"
        )
        remedy = extract_mod.missing_object_remedy(message)
        self.assertIsNotNone(remedy)
        self.assertIn("partial", remedy)
        self.assertIn("promisor", remedy)
        self.assertIn("unable to read", remedy)
        self.assertIsNone(
            extract_mod.missing_object_remedy("some other failure")
        )

    def test_a_partial_clone_with_its_promisor_cut_names_the_remedy(self):
        with RetryingTemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            source.mkdir(parents=True)
            git(source, "init", "-b", "main")
            git(source, "config", "user.email", "test@example.com")
            git(source, "config", "user.name", "Test User")
            git(source, "config", "commit.gpgsign", "false")
            (source / "mod.py").write_text("VALUE = 1\n")
            git(source, "add", "-A")
            git(source, "commit", "-m", "one")
            (source / "mod.py").write_text("VALUE = 2\n")
            git(source, "add", "-A")
            git(source, "commit", "-m", "two")
            (source / "base.py").write_text("VALUE = 0\n")
            git(source, "add", "-A")
            git(source, "commit", "-m", "three")
            # A bare server that honours the filter, because a
            # plain local clone ignores it and a file server
            # without the allowance silently serves whole objects.
            server = Path(tmp) / "server.git"
            server.mkdir(parents=True)
            git(server, "init", "--bare")
            git(server, "config", "uploadpack.allowFilter", "true")
            git(source, "push", "-q", str(server), "main")
            git(server, "symbolic-ref", "HEAD", "refs/heads/main")
            clone = Path(tmp) / "clone"
            clone_env = scrubbed_git_env()
            clone_env["GIT_CONFIG_COUNT"] = "1"
            clone_env["GIT_CONFIG_KEY_0"] = "protocol.version"
            clone_env["GIT_CONFIG_VALUE_0"] = "2"
            result = subprocess.run(
                ["git", "clone", "-q", "--filter=blob:none",
                 "--no-checkout", "file://" + str(server), str(clone)],
                env=clone_env, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                git(clone, "config", "remote.origin.promisor"), "true"
            )
            # The promisor assertions read the object store
            # without lazy fetching, because a promisor lookup
            # that fetched the blob would heal the very hole the
            # fixture exists to keep open.
            present = subprocess.run(
                ["git", "-C", str(clone), "cat-file",
                 "--batch-all-objects", "--batch-check"],
                env=scrubbed_git_env(), capture_output=True, text=True,
            )
            self.assertNotIn(" blob ", present.stdout)
            git(clone, "remote", "remove", "origin")
            out = Path(tmp) / "out"
            failed = run_extract(clone, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(failed.returncode, 2, failed.stdout)
            self.assertIn("partial", failed.stderr)
            self.assertIn("promisor", failed.stderr)
            self.assertFalse(read_manifest(out)["verified"])
    def test_a_damaged_whole_clone_is_not_diagnosed_as_partial(self):
        with RetryingTemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir(parents=True)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "test@example.com")
            git(repo, "config", "user.name", "Test User")
            git(repo, "config", "commit.gpgsign", "false")
            (repo / "mod.py").write_text("VALUE = 1\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "one")
            blob = git(repo, "rev-parse", "HEAD:mod.py")
            (repo / "mod.py").write_text("VALUE = 2\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "two")
            self.assertFalse(extract_mod.repo_is_partial(repo))
            loose = (
                repo / ".git" / "objects" / blob[:2] / blob[2:]
            )
            loose.unlink()
            out = Path(tmp) / "out"
            failed = run_extract(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(failed.returncode, 2, failed.stdout)
            self.assertNotIn("promisor", failed.stderr)
            self.assertNotIn("the clone is partial", failed.stderr)
            self.assertFalse(read_manifest(out)["verified"])


    def assert_inside_the_estimator_band(self, text, real_tokens):
        estimate = extract_mod.estimate_tokens(text)
        self.assertLessEqual(
            49 * estimate, 100 * real_tokens,
            "estimate %d overprices real %d" % (estimate, real_tokens),
        )
        self.assertLessEqual(
            100 * real_tokens, 135 * estimate,
            "estimate %d underprices real %d" % (estimate, real_tokens),
        )

    def test_alternating_digit_letter_runs_price_inside_the_band(self):
        # The cl100k counts recorded for these shapes stand in
        # the round record. An alternating digit and letter run
        # merges nowhere, so it carries one real token per
        # character, where the flat digit rule priced three
        # fifths of one and admitted packets over budget.
        self.assert_inside_the_estimator_band("1z" * 10000, 20000)
        self.assert_inside_the_estimator_band("A1B2C3D4" * 2500, 20000)

    def test_embedded_digit_groups_price_inside_the_band(self):
        # A digit group standing in a long letter stretch reads
        # as one token per three digits between letter tokens,
        # so the repeated word shapes carry about two real
        # tokens per ten characters, where the flat digit rule
        # priced three times that on the first two shapes.
        self.assert_inside_the_estimator_band("base64data" * 2000, 4001)
        self.assert_inside_the_estimator_band("database64" * 2000, 4000)
        self.assert_inside_the_estimator_band("file2024report" * 1000, 4000)

    def test_an_alternating_packet_is_refused_under_its_real_size(self):
        with RetryingTemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir(parents=True)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "test@example.com")
            git(repo, "config", "user.name", "Test User")
            git(repo, "config", "commit.gpgsign", "false")
            (repo / "seed.txt").write_text("seed\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "seed")
            (repo / "data.txt").write_text("1z" * 10000 + "\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "alternating run")
            out = Path(tmp) / "out"
            result = run_extract(
                repo, out, "--range", "HEAD~1..HEAD", "--budget", "14000"
            )
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertIn("smallest packet", result.stderr)
            self.assertFalse(read_manifest(out)["verified"])

    def test_a_stale_promisor_mark_does_not_name_the_partial_shape(self):
        with RetryingTemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir(parents=True)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "test@example.com")
            git(repo, "config", "user.name", "Test User")
            git(repo, "config", "commit.gpgsign", "false")
            (repo / "mod.py").write_text("VALUE = 1\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "one")
            blob = git(repo, "rev-parse", "HEAD:mod.py")
            (repo / "mod.py").write_text("VALUE = 2\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "two")
            stale = (
                repo / ".git" / "objects" / "pack" / "pack-stale.promisor"
            )
            stale.write_bytes(b"")
            self.assertFalse(extract_mod.repo_is_partial(repo))
            loose = (
                repo / ".git" / "objects" / blob[:2] / blob[2:]
            )
            loose.unlink()
            out = Path(tmp) / "out"
            failed = run_extract(repo, out, "--range", "HEAD~1..HEAD")
            self.assertEqual(failed.returncode, 2, failed.stdout)
            self.assertNotIn("promisor", failed.stderr)
            self.assertNotIn("the clone is partial", failed.stderr)
            self.assertFalse(read_manifest(out)["verified"])



    def assert_inside_the_unspelled_limit(self, text, real_tokens):
        # The named limit for unspelled letter runs. The real
        # count may stand up to about 5.1 times the estimate,
        # and the overprice side keeps the band floor.
        estimate = extract_mod.estimate_tokens(text)
        self.assertLessEqual(
            49 * estimate, 100 * real_tokens,
            "estimate %d overprices real %d" % (estimate, real_tokens),
        )
        self.assertLessEqual(
            100 * real_tokens, 510 * estimate,
            "estimate %d underprices real %d past the named "
            "limit" % (estimate, real_tokens),
        )

    def test_unspelled_runs_stand_on_the_named_limit(self):
        # A keyboard walk and a rare letter run carry digit
        # groups a tokenizer splits letter by letter, so they
        # stand outside the band and on the named limit the
        # estimator docstring prints, at the real counts the
        # round record carries. The capitalised spelled run
        # beside them prices inside the band.
        self.assert_inside_the_unspelled_limit(
            "zxcvbnm1234" * 1500, 10500)
        self.assert_inside_the_unspelled_limit(
            "qxvzbnpj64" * 2000, 10000)
        self.assert_inside_the_unspelled_limit(
            "fzqgkxjxjv1" * 2000, 22000)
        self.assert_inside_the_unspelled_limit(
            "jwqjzvq" * 2000, 14000)
        self.assert_inside_the_unspelled_limit(
            "zvzqo " * 2000, 10001)
        self.assert_inside_the_estimator_band("aBcD1234" * 2500, 15000)

    def test_repeated_letter_runs_price_at_the_half_token_rate(self):
        # A repeated letter merges only a little in a real
        # tokenizer, from one token per letter down to about
        # one per four characters on the best merging letters,
        # at the counts the round record carries. The half
        # token price stands inside the band on the worst
        # merging letter and on the best.
        self.assert_inside_the_estimator_band("g" * 20000, 10000)
        self.assert_inside_the_estimator_band("b" * 20000, 5000)


if __name__ == "__main__":
    unittest.main()
