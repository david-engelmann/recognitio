"""The credential trio and the output lock limb.

Rounds 15, 32, and 247 of the 300 round programme for the
credential trio, and round 144 item RV4 for the lock limb.
A change carrying a dotenv file and a private key file built
a verified packet with every secret value verbatim, the file
names printed with no flag anywhere, and no credential
counterpart to the instruction file flag in the manifest.
Approval claims and a maintainer author name printed in the
same packet with no sentence marking packet content as
untrusted data on the main review surfaces and no caveat
that an author name is self asserted. The output lock keyed
through the machine temporary directory, so two runs handed
different temporary directories took different locks for the
same output and the second run sentence in the skill stood
unconditional over a lock that could not see the contention.

These tests rebuild each shape and require the repaired
behaviour, beside controls that carry no credential file and
must stay unflagged and unwarned.
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
EXTRACT = ROOT / ".agents" / "skills" / "recognitio" / "scripts" / "extract.py"
CHECK_PACKET = ROOT / "scripts" / "check_packet.py"

LOCATION_VARS = (
    "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR", "GIT_NAMESPACE",
)


def clean_env(extra=None):
    env = {
        key: value for key, value in os.environ.items()
        if key not in LOCATION_VARS
    }
    if extra:
        env.update(extra)
    return env


def git(repo, *args, env_extra=None):
    result = subprocess.run(
        ["git", "-C", str(repo)] + list(args),
        capture_output=True, text=True, env=clean_env(env_extra),
    )
    if result.returncode != 0:
        raise AssertionError(
            "git %s failed: %s" % (" ".join(args), result.stderr))
    return result.stdout.strip()


def load_extractor():
    spec = importlib.util.spec_from_file_location(
        "cred_lock_extract", EXTRACT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_repo(tmp, base_files, head_files, head_env=None):
    repo = Path(tmp) / "repo"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test User")
    git(repo, "config", "commit.gpgsign", "false")
    for name, content in base_files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "base")
    for name, content in head_files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "A change", env_extra=head_env)
    return repo


def run_extract(repo, out):
    return subprocess.run(
        [sys.executable, str(EXTRACT), "--repo", str(repo),
         "--range", "HEAD~1..HEAD", "--out", str(out)],
        capture_output=True, text=True, env=clean_env(),
    )


class TestCredentialTrio(unittest.TestCase):
    def build_packet(self, tmp, base_files, head_files, head_env=None):
        repo = make_repo(tmp, base_files, head_files, head_env)
        out = Path(tmp) / "out"
        run = run_extract(repo, out)
        self.assertEqual(run.returncode, 0, run.stderr)
        packet = (out / "packet.md").read_text()
        manifest = json.loads((out / "manifest.json").read_text())
        return repo, out, packet, manifest

    def test_secret_values_never_reach_a_verified_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    ".env": (
                        "AWS_ACCESS_KEY_ID="
                        + "AKIA" + "IOSFODNN7EXAMPLE" + "\n"
                        "DATABASE_URL=postgres://user:"
                        "canary-db-password@db.example.invalid/app\n"
                    ),
                    "key.pem": (
                        "-----BEGIN PRIVATE " + "KEY-----\n"
                        "canary-private-key-body\n"
                        "-----END PRIVATE " + "KEY-----\n"
                    ),
                    "a.py": (
                        "KEY = '" + "AKIA" + "IOSFODNN7EXAMPLE"
                        + "'\nx = 2\n"
                    ),
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {".env": True, "key.pem": True, "a.py": False},
            )
            for canary in (
                "AKIA" + "IOSFODNN7EXAMPLE",
                "canary-db-password",
                "canary-private-key-body",
                "PRIVATE " + "KEY-----",
            ):
                self.assertNotIn(canary, packet)
            self.assertIn("credential file", packet)
            self.assertIn("credential shaped files", packet)
            self.assertIn("[redacted credential]", packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)

    def test_a_token_shaped_value_in_a_commit_subject_is_masked(self):
        token = "ghp_" + "Ab3" * 12
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "test@example.invalid")
            git(repo, "config", "user.name", "Test User")
            git(repo, "config", "commit.gpgsign", "false")
            (repo / "a.py").write_text("x = 1\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "base")
            (repo / "a.py").write_text("x = 2\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "Add the feature " + token)
            out = Path(tmp) / "out"
            run = run_extract(repo, out)
            self.assertEqual(run.returncode, 0, run.stderr)
            packet = (out / "packet.md").read_text()
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertTrue(manifest["verified"])
            self.assertNotIn(token, packet)
            t0 = packet.split("## T1 The change")[0]
            self.assertIn("[redacted credential]", t0)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)

    def test_a_token_shaped_value_in_the_rereview_channel_is_masked(self):
        token = "ghp_" + "Cd5" * 12
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "test@example.invalid")
            git(repo, "config", "user.name", "Test User")
            git(repo, "config", "commit.gpgsign", "false")
            (repo / "a.py").write_text("x = 1\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "base")
            base = git(repo, "rev-parse", "HEAD")
            (repo / "a.py").write_text("x = 2\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "reviewed point")
            since = git(repo, "rev-parse", "HEAD")
            (repo / "a.py").write_text("x = 3\n")
            git(repo, "add", "-A")
            git(repo, "commit", "-m", "Follow up " + token)
            out = Path(tmp) / "out"
            run = subprocess.run(
                [sys.executable, str(EXTRACT), "--repo", str(repo),
                 "--range", "%s..HEAD" % base, "--since", since,
                 "--out", str(out)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            packet = (out / "packet.md").read_text()
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertTrue(manifest["verified"])
            self.assertIn("## Re-review", packet)
            self.assertNotIn(token, packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)

    def test_the_dotenv_family_spellings_are_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo, _out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    "prod.env": "SECRET=canary-prod-env-value\n",
                    ".envrc": "SECRET=canary-envrc-value\n",
                    ".ENV": "SECRET=canary-upper-env-value\n",
                    ".env.local": "SECRET=canary-local-value\n",
                    "KEY.PEM": "canary-pem-body\n",
                    "id_ed25519": "canary-ssh-body\n",
                    ".env.example": "SECRET=fill-me-in\n",
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    "prod.env": True,
                    ".envrc": True,
                    ".ENV": True,
                    ".env.local": True,
                    "KEY.PEM": True,
                    "id_ed25519": True,
                    ".env.example": False,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-prod-env-value",
                "canary-envrc-value",
                "canary-upper-env-value",
                "canary-local-value",
                "canary-pem-body",
                "canary-ssh-body",
            ):
                self.assertNotIn(canary, packet)
            self.assertIn("fill-me-in", packet)

    def test_the_ssh_key_names_are_flagged_in_any_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo, _out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    "ID_RSA": "canary-upper-rsa-body\n",
                    "keys/Id_Ed25519": "canary-mixed-ed-body\n",
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    "ID_RSA": True,
                    "keys/Id_Ed25519": True,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-upper-rsa-body",
                "canary-mixed-ed-body",
            ):
                self.assertNotIn(canary, packet)

    def test_the_standard_credential_file_names_are_flagged(self):
        # The filename channel beyond the priced set. The
        # netrc password file, the AWS shared credentials
        # file, the npm and PyPI credential files and the
        # OpenSSH security key names hold secrets whose usual
        # contents fall outside the masked value shapes, so
        # the flag and the withholding that follow from it are
        # the only defence those files have in a packet.
        with tempfile.TemporaryDirectory() as tmp:
            repo, out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    ".netrc": (
                        "machine api.example.invalid login user "
                        "password canary-netrc-password\n"
                    ),
                    "credentials": (
                        "[default]\naws_secret_access_key = "
                        "canary-aws-secret-value\n"
                    ),
                    ".npmrc": (
                        "//registry.example.invalid/:_authToken="
                        "canary-npm-token-value\n"
                    ),
                    ".pypirc": (
                        "[pypi]\npassword = "
                        "canary-pypirc-password\n"
                    ),
                    "id_ed25519_sk": "canary-sk-ed-body\n",
                    "id_ecdsa_sk": "canary-sk-ecdsa-body\n",
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    ".netrc": True,
                    "credentials": True,
                    ".npmrc": True,
                    ".pypirc": True,
                    "id_ed25519_sk": True,
                    "id_ecdsa_sk": True,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-netrc-password",
                "canary-aws-secret-value",
                "canary-npm-token-value",
                "canary-pypirc-password",
                "canary-sk-ed-body",
                "canary-sk-ecdsa-body",
            ):
                self.assertNotIn(canary, packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)

    def test_the_next_standard_credential_names_are_flagged(self):
        # The filename channel one spelling further out. The
        # PostgreSQL password file, the git credential store
        # and a PuTTY private key reached a verified packet
        # verbatim under the priced set, and the same family
        # carries the Windows netrc spelling, the credentials
        # stem under a data extension, the conventional cloud
        # key file names, the key material suffixes outside
        # the priced set, the editor backup spellings of
        # priced names, and the two stores recognised by the
        # shape of their whole path, whose
        # basenames are plain config names. Their contents
        # fall outside the masked value shapes beside the
        # PuTTY key body, so the flag is the defence.
        with tempfile.TemporaryDirectory() as tmp:
            repo, out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    ".pgpass": (
                        "host:5432:db:user:"
                        "canary-pgpass-password\n"
                    ),
                    ".git-credentials": (
                        "https://user:"
                        "canary-gitcred-password"
                        "@example.invalid\n"
                    ),
                    "id_rsa.ppk": "canary-ppk-body\n",
                    "_netrc": (
                        "machine api.example.invalid login user "
                        "password canary-winnetrc-password\n"
                    ),
                    "credentials.json": (
                        '{"secret": "canary-credjson-value"}\n'
                    ),
                    "service-account.json": (
                        '{"private_key": '
                        '"canary-service-account-value"}\n'
                    ),
                    ".netrc.bak": (
                        "machine api.example.invalid login user "
                        "password canary-backup-password\n"
                    ),
                    ".docker/config.json": (
                        '{"auths": {"example.invalid": '
                        '{"auth": "canary-docker-auth"}}}\n'
                    ),
                    ".kube/config": (
                        "users:\n- user:\n    token: "
                        "canary-kube-token\n"
                    ),
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    ".pgpass": True,
                    ".git-credentials": True,
                    "id_rsa.ppk": True,
                    "_netrc": True,
                    "credentials.json": True,
                    "service-account.json": True,
                    ".netrc.bak": True,
                    ".docker/config.json": True,
                    ".kube/config": True,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-pgpass-password",
                "canary-gitcred-password",
                "canary-ppk-body",
                "canary-winnetrc-password",
                "canary-credjson-value",
                "canary-service-account-value",
                "canary-backup-password",
                "canary-docker-auth",
                "canary-kube-token",
            ):
                self.assertNotIn(canary, packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)

    def test_every_enumerated_credential_name_is_planted(self):
        # The direct table over the judging function. Every
        # basename, suffix, stem extension, backup tail and
        # download shape the extractor enumerates stands
        # planted here beside its innocent controls, so a
        # typo in one set member or the loss of one branch,
        # the client_secret_ branch included, fails this test
        # by name.
        mod = load_extractor()
        flagged = (
            ".htpasswd", ".vault-token", ".boto", ".s3cfg",
            ".my.cnf", "keystore", "cookies.txt", "auth.json",
            "service_account.json", "service-account.json",
            "id_rsa", ".netrc", "_netrc", ".pgpass",
            ".git-credentials", ".npmrc", ".pypirc",
            "credentials", "keys/id_ed25519_sk",
            "a.jks", "a.p8", "a.kdbx", "a.ovpn", "a.gpg",
            "a.pem", "a.key", "a.p12", "a.pfx", "a.keystore",
            "a.ppk", "secring.gpg",
            "credentials.json", "credentials.yml",
            "credentials.yaml", "credentials.txt",
            "credentials.toml", "credentials.ini",
            "credentials.cfg", "credentials.csv",
            "client_secret_123456.json",
            "id_rsa.bak", ".netrc.bak", "credentials.bak",
            "id_rsa~", ".pgpass~",
            ".docker/config.json", ".kube/config",
            ".docker/config.json.bak", ".kube/config.bak",
            "application_default_credentials.json",
            "client_secrets.json", "kubeconfig",
            "secrets.json", "wg0.conf", "accessTokens.json",
            "my-firebase-adminsdk-ab12-cd34.json",
            "firebase-adminsdk.json",
            ".config/gh/hosts.yml",
            ".config/gh/hosts.yml.bak",
            ".env", ".envrc", "prod.env",
            "accessKeys.csv", "access_keys.csv",
            "secrets.yaml", "secrets.yml", "secrets.txt",
            "secrets.toml", "secret.json", "secret.yaml",
            "credentials.db", "credentials.xml",
            "tokens.json", "token.json", "access-token.json",
            "session.json", "terraform.tfstate",
            "service-account-key.json",
            "service_account_key.json",
            ".curlrc", ".wgetrc", "cookies.sqlite",
            "cookies.json", "pgpass", "netrc",
            "git-credentials", "wg1.conf", "client.conf",
            "openvpn.conf", "kubeconfig.yaml",
            ".kube/config.yaml", "a.kdb", ".vault-password",
            ".dockerconfigjson", "wp-config.php",
            "terraform.tfstate.backup", "npmrc",
            "vault-token", "Cookies", "pypirc", "curlrc",
            "wgetrc", "htpasswd", "boto", "s3cfg",
            "dockerconfig.json",
            "application-default-credentials.json",
            ".kube/config.json", ".config/gh/hosts.yaml",
            "access_token.json", "refresh_token.json",
            "refresh-token.json", "api_key.json",
            "api-key.json", "apikeys.json", "api_keys.json",
            "private_key.json", "terraform.tfvars",
            "secrets.tfvars", ".terraformrc", "token.csv",
            "tokens.csv", "tokens.yaml", "session.yaml",
            "sessions.json", "client_secret.json",
            "oauth.json", "keyfile.json",
            "service-account-key.yaml",
            "service_account_key.yaml",
        )
        unflagged = (
            "a.py", "credentials.md", "client_secret_x.txt",
            "keystore.txt", "credentials/README.md",
            "docs/credentials.md", "credentials.py",
            "mycredentials", "credentials2",
            "credentials/store.txt", "npmrc.txt",
            ".env.example", "id_rsa.pub", "config.json",
            "app/config.json", "secret_santa.md",
            "tokenizer.py", "wg0.md", "secrets.md",
            "auth.md", "known_hosts", ".ssh/config", "token",
            "firebase.json", "hosts.yml", "gh/hosts.yml",
            "kube/config", "docker/config.json",
            "session.py", "tokens.md", "client.md",
            "secret.md", "token.md",
        )
        for name in flagged:
            with self.subTest(name=name):
                self.assertTrue(
                    mod.is_credential_path(name), name)
        for name in unflagged:
            with self.subTest(name=name):
                self.assertFalse(
                    mod.is_credential_path(name), name)

    def test_the_lane5_standard_credential_names_are_flagged(self):
        # The next enumerated names at packet level. The
        # Google application default credentials file, the
        # OAuth client secrets file in its plural spelling,
        # the kubeconfig, the AWS credential download under
        # its csv extension, the secrets stem in its json
        # form, a WireGuard
        # client config, a priced store recognised by the
        # shape of its whole path under an
        # editor backup tail, the Firebase admin SDK download
        # shape, the Azure CLI token cache and the GitHub CLI
        # hosts store each carried a canary into a verified
        # packet under the lane 4 set.
        with tempfile.TemporaryDirectory() as tmp:
            repo, out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    "application_default_credentials.json": (
                        '{"client_secret": '
                        '"canary-adc-secret"}\n'
                    ),
                    "client_secrets.json": (
                        '{"client_secret": '
                        '"canary-client-secret"}\n'
                    ),
                    "kubeconfig": (
                        "users:\n- user:\n    token: "
                        "canary-kubeconfig-token\n"
                    ),
                    "credentials.csv": (
                        "user,secret\nuser,"
                        "canary-csv-secret\n"
                    ),
                    "secrets.json": (
                        '{"api_key": "canary-secrets-key"}\n'
                    ),
                    "wg0.conf": (
                        "PrivateKey = canary-wireguard-key\n"
                    ),
                    ".kube/config.bak": (
                        "users:\n- user:\n    token: "
                        "canary-kube-backup-token\n"
                    ),
                    "my-firebase-adminsdk-ab12-cd34.json": (
                        '{"private_key": '
                        '"canary-firebase-key"}\n'
                    ),
                    "accessTokens.json": (
                        '{"token": "canary-azure-token"}\n'
                    ),
                    ".config/gh/hosts.yml": (
                        "github.com:\n  oauth_token: "
                        "canary-gh-token\n"
                    ),
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    "application_default_credentials.json": True,
                    "client_secrets.json": True,
                    "kubeconfig": True,
                    "credentials.csv": True,
                    "secrets.json": True,
                    "wg0.conf": True,
                    ".kube/config.bak": True,
                    "my-firebase-adminsdk-ab12-cd34.json": True,
                    "accessTokens.json": True,
                    ".config/gh/hosts.yml": True,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-adc-secret", "canary-client-secret",
                "canary-kubeconfig-token", "canary-csv-secret",
                "canary-secrets-key", "canary-wireguard-key",
                "canary-kube-backup-token",
                "canary-firebase-key", "canary-azure-token",
                "canary-gh-token",
            ):
                self.assertNotIn(canary, packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)

    def test_the_lane6_standard_credential_names_are_flagged(self):
        # The packet proven names of the lane 5 review. The
        # AWS console credential download under its actual
        # download name, the secrets stem in a yaml form, a
        # token store, the terraform state file, the GCP
        # service account key download name and the curl rc
        # file each carried a canary into a verified packet
        # under the lane 5 set, so each stands planted here
        # at packet level beside the unit table.
        with tempfile.TemporaryDirectory() as tmp:
            repo, out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    "accessKeys.csv": (
                        "Access key ID,Secret access key\n"
                        "AKIAEXAMPLE,canary-accesskeys-secret\n"
                    ),
                    "secrets.yaml": (
                        "api_key: canary-secrets-yaml-value\n"
                    ),
                    "tokens.json": (
                        '{"refresh_token": '
                        '"canary-tokens-value"}\n'
                    ),
                    "terraform.tfstate": (
                        '{"password": "canary-tfstate-value"}\n'
                    ),
                    "service-account-key.json": (
                        '{"private_key_id": '
                        '"canary-sak-key-id"}\n'
                    ),
                    ".curlrc": (
                        "user = user:canary-curlrc-password\n"
                    ),
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    "accessKeys.csv": True,
                    "secrets.yaml": True,
                    "tokens.json": True,
                    "terraform.tfstate": True,
                    "service-account-key.json": True,
                    ".curlrc": True,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-accesskeys-secret",
                "canary-secrets-yaml-value",
                "canary-tokens-value",
                "canary-tfstate-value",
                "canary-sak-key-id",
                "canary-curlrc-password",
            ):
                self.assertNotIn(canary, packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)

    def test_the_lane7_standard_credential_names_are_flagged(self):
        # The packet proven names of the lane 6 review. The
        # Docker credential store under its mount name, the
        # WordPress configuration file, the terraform state
        # backup under the backup tail its tool writes, the
        # priced npmrc and vault token names in their bare
        # spellings and the Chrome cookie store under its
        # file name each carried a canary into a verified
        # packet under the lane 6 set, so each stands
        # planted here at packet level beside the unit
        # table, and the extractor comment beside them
        # states the netrc spelling count the code holds.
        with tempfile.TemporaryDirectory() as tmp:
            repo, out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    ".dockerconfigjson": (
                        '{"auths": {"registry": {"auth": '
                        '"canary-dockerconfig-auth"}}}\n'
                    ),
                    "wp-config.php": (
                        "<?php define('DB_PASSWORD', "
                        "'canary-wp-password');\n"
                    ),
                    "terraform.tfstate.backup": (
                        '{"password": '
                        '"canary-tfstate-backup-value"}\n'
                    ),
                    "npmrc": (
                        "//registry.npmjs.org/:_authToken="
                        "canary-npmrc-token\n"
                    ),
                    "vault-token": "canary-vault-token\n",
                    "Cookies": "canary-cookies-store\n",
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    ".dockerconfigjson": True,
                    "wp-config.php": True,
                    "terraform.tfstate.backup": True,
                    "npmrc": True,
                    "vault-token": True,
                    "Cookies": True,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-dockerconfig-auth",
                "canary-wp-password",
                "canary-tfstate-backup-value",
                "canary-npmrc-token",
                "canary-vault-token",
                "canary-cookies-store",
            ):
                self.assertNotIn(canary, packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)
        for rel in (
            ".agents/skills/recognitio/scripts/extract.py",
            ".comate/skills/recognitio/scripts/extract.py",
            ".cursor-plugin/skills/recognitio/scripts/extract.py",
            "agent-plugins-package/skills/recognitio/scripts/extract.py",
        ):
            text = " ".join((ROOT / rel).read_text().split())
            self.assertIn(
                "the netrc password file in its three "
                "spellings", text, rel)

    def test_the_lane8_standard_credential_names_are_flagged(self):
        # The lane 7 red team Minor standing. The Chrome
        # password and autofill stores, the terraform
        # variables and CLI credential files in their json
        # forms, the kubeconfig under a json tail and the
        # api key store in its separator free spelling each
        # carried a canary into a verified packet under the
        # lane 7 set, so each stands planted here at packet
        # level beside the unit spellings one step past the
        # lane 7 set and the innocent controls that must
        # stay unflagged.
        with tempfile.TemporaryDirectory() as tmp:
            repo, out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    "Login Data": "canary-login-data-value\n",
                    "Web Data": "canary-web-data-value\n",
                    "terraform.tfvars.json": (
                        '{"password": '
                        '"canary-tfvars-json-value"}\n'
                    ),
                    "credentials.tfrc.json": (
                        '{"token": "canary-tfrc-value"}\n'
                    ),
                    "kubeconfig.json": (
                        '{"token": "canary-kubeconfig-value"}\n'
                    ),
                    "apikey.json": (
                        '{"key": "canary-apikey-value"}\n'
                    ),
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    "Login Data": True,
                    "Web Data": True,
                    "terraform.tfvars.json": True,
                    "credentials.tfrc.json": True,
                    "kubeconfig.json": True,
                    "apikey.json": True,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-login-data-value",
                "canary-web-data-value",
                "canary-tfvars-json-value",
                "canary-tfrc-value",
                "canary-kubeconfig-value",
                "canary-apikey-value",
            ):
                self.assertNotIn(canary, packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)
        mod = load_extractor()
        flagged = (
            "service-account.yaml", "service_account.yaml",
            "service-account.yml", "service_account.yml",
            "service-account-key.yml",
            "service_account_key.yml", "privatekey.json",
            "private-key.json", "apikeys.yaml",
            "api_token.json", "api-token.json",
            "auth-token.json", "access_token.txt",
            "refresh_token.yaml", "token_cache.json",
            "access-token", "refresh-token", "cookies.db",
            "keystore.json", "passwd", "shadow",
            ".config/gh/hosts.json", "secrets.tfvars.json",
            "client_secrets.yaml", "login_data", "web_data",
        )
        for name in flagged:
            with self.subTest(name=name):
                self.assertTrue(
                    mod.is_credential_path(name), name)
        unflagged = (
            "kubeconfig.md", "service-account.md",
            "apikey.md", "login.md", "terraform.json",
            "data.json", "web.md", "tokenizer.json",
            "keystore.md", "passwd.md", "shadow.md",
            "hosts.json", "config.json",
        )
        for name in unflagged:
            with self.subTest(name=name):
                self.assertFalse(
                    mod.is_credential_path(name), name)

    def test_the_lane9_standard_credential_names_are_flagged(self):
        # The lane 8 red team Minor standing. The Firefox
        # password and key stores standing together in one
        # profile, the Chrome Local State file holding the
        # encryption key for its password store, the
        # browser password export, the auth token store in
        # its underscored spelling and the api key store
        # under a yaml tail each carried a canary into a
        # verified packet under the lane 8 set, so each
        # stands planted here at packet level beside the
        # unit spellings one step past the lane 8 set, the
        # terraform variables file under a project name by
        # its tfvars tail, and the innocent controls that
        # must stay unflagged.
        with tempfile.TemporaryDirectory() as tmp:
            repo, out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    "logins.json": (
                        '{"logins": [{"password": '
                        '"canary-logins-value"}]}\n'
                    ),
                    "key4.db": "canary-key4-value\n",
                    "auth_token.json": (
                        '{"token": "canary-auth-token-value"}\n'
                    ),
                    "api_key.yaml": (
                        "api_key: canary-api-key-value\n"
                    ),
                    "passwords.csv": (
                        "url,username,password\n"
                        "site,user,canary-passwords-value\n"
                    ),
                    "Local State": (
                        '{"os_crypt": {"encrypted_key": '
                        '"canary-local-state-value"}}\n'
                    ),
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    "logins.json": True,
                    "key4.db": True,
                    "auth_token.json": True,
                    "api_key.yaml": True,
                    "passwords.csv": True,
                    "Local State": True,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-logins-value", "canary-key4-value",
                "canary-auth-token-value",
                "canary-api-key-value",
                "canary-passwords-value",
                "canary-local-state-value",
            ):
                self.assertNotIn(canary, packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)
        mod = load_extractor()
        flagged = (
            "key3.db", "api-key.yaml", "apikey.yaml",
            "api_key.txt", "private_key.yaml",
            "private-key.yaml", "client_secret.yaml",
            "access-token.yaml", "gshadow",
            "cookies.sqlite3", "prod.tfvars",
        )
        for name in flagged:
            with self.subTest(name=name):
                self.assertTrue(
                    mod.is_credential_path(name), name)
        unflagged = (
            "kubeconfig.md", "service-account.md",
            "apikey.md", "login.md", "terraform.json",
            "data.json", "web.md", "tokenizer.json",
            "keystore.md", "passwd.md", "shadow.md",
            "hosts.json", "config.json", "variables.md",
            "notes.tfvars.txt",
        )
        for name in unflagged:
            with self.subTest(name=name):
                self.assertFalse(
                    mod.is_credential_path(name), name)

    def test_the_lane10_standard_credential_names_are_flagged(self):
        # The lane 9 red team credential Minor standing.
        # The standard names one step past the lane 9 set,
        # the service account key in its concatenated
        # spelling, the client secret store in its
        # hyphenated spelling and under a txt tail, the
        # access token store under a yaml tail in its
        # underscored spelling, the api key store under a
        # txt tail in its hyphenated spelling, the legacy
        # Firefox password store, and the terraform
        # variables file in its json form under the prod
        # name, each carried a canary into a verified
        # packet under the lane 9 set, so each stands
        # planted here at packet level beside the unit
        # spellings one step past them and the innocent
        # controls that must stay unflagged. The tail past
        # this enumeration stands under the declared
        # boundary of the family in the extractor comment,
        # a credential file under a name the set does not
        # hold standing outside the set.
        with tempfile.TemporaryDirectory() as tmp:
            repo, out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    "serviceaccount.json": (
                        '{"private_key": '
                        '"canary-serviceaccount-value"}\n'
                    ),
                    "client-secret.json": (
                        '{"secret": '
                        '"canary-client-secret-value"}\n'
                    ),
                    "access_token.yaml": (
                        "access_token: "
                        "canary-access-token-value\n"
                    ),
                    "api-key.txt": (
                        "canary-api-key-value\n"
                    ),
                    "client_secret.txt": (
                        "canary-client-secret-txt-value\n"
                    ),
                    "signons.sqlite": (
                        "canary-signons-value\n"
                    ),
                    "prod.tfvars.json": (
                        '{"password": '
                        '"canary-tfvars-json-value"}\n'
                    ),
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    "serviceaccount.json": True,
                    "client-secret.json": True,
                    "access_token.yaml": True,
                    "api-key.txt": True,
                    "client_secret.txt": True,
                    "signons.sqlite": True,
                    "prod.tfvars.json": True,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-serviceaccount-value",
                "canary-client-secret-value",
                "canary-access-token-value",
                "canary-api-key-value",
                "canary-client-secret-txt-value",
                "canary-signons-value",
                "canary-tfvars-json-value",
            ):
                self.assertNotIn(canary, packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)
        mod = load_extractor()
        flagged = (
            "apikey.txt", "private_key.txt", "api_key.yml",
            "access_token.yml", "refresh_token.yml",
            "login_data.json", "cert9.db",
        )
        for name in flagged:
            with self.subTest(name=name):
                self.assertTrue(
                    mod.is_credential_path(name), name)
        unflagged = (
            "kubeconfig.md", "service-account.md",
            "apikey.md", "login.md", "terraform.json",
            "data.json", "web.md", "tokenizer.json",
            "keystore.md", "passwd.md", "shadow.md",
            "hosts.json", "config.json", "variables.md",
            "notes.tfvars.txt", "my.tfvars.json",
        )
        for name in unflagged:
            with self.subTest(name=name):
                self.assertFalse(
                    mod.is_credential_path(name), name)

    def test_the_lane11_standard_credential_names_are_flagged(self):
        # The lane 10 red team credential Minor
        # standing. The standard names one step past
        # the lane 10 set, the service account key
        # under a txt tail in its underscored spelling,
        # the client secret store in its hyphenated
        # spelling under a yaml tail, the access token
        # store in its hyphenated spelling under a txt
        # tail, the refresh token store in its
        # hyphenated spelling under a yaml tail, the
        # private key store in its hyphenated spelling
        # under a txt tail, the service account key in
        # its concatenated spelling under a yaml tail,
        # and the legacy Firefox certificate store of
        # the generation before cert9.db, each carried
        # a canary into a verified packet under the
        # lane 10 set, so each stands planted here at
        # packet level beside the unit spellings one
        # step past them and the innocent controls that
        # must stay unflagged. The tail past this
        # enumeration stands under the declared
        # boundary of the family in the extractor
        # comment, a credential file under a name the
        # set does not hold standing outside the set.
        with tempfile.TemporaryDirectory() as tmp:
            repo, out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    "service_account.txt": (
                        "canary-service-account-txt-value\n"
                    ),
                    "client-secret.yaml": (
                        "secret: "
                        "canary-client-secret-yaml-value\n"
                    ),
                    "access-token.txt": (
                        "canary-access-token-txt-value\n"
                    ),
                    "refresh-token.yaml": (
                        "token: "
                        "canary-refresh-token-yaml-value\n"
                    ),
                    "private-key.txt": (
                        "canary-private-key-txt-value\n"
                    ),
                    "serviceaccount.yaml": (
                        "key: "
                        "canary-serviceaccount-yaml-value\n"
                    ),
                    "cert8.db": (
                        "canary-cert8-value\n"
                    ),
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    "service_account.txt": True,
                    "client-secret.yaml": True,
                    "access-token.txt": True,
                    "refresh-token.yaml": True,
                    "private-key.txt": True,
                    "serviceaccount.yaml": True,
                    "cert8.db": True,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-service-account-txt-value",
                "canary-client-secret-yaml-value",
                "canary-access-token-txt-value",
                "canary-refresh-token-yaml-value",
                "canary-private-key-txt-value",
                "canary-serviceaccount-yaml-value",
                "canary-cert8-value",
            ):
                self.assertNotIn(canary, packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)
        mod = load_extractor()
        flagged = (
            "service-account.txt", "client_secret.yml",
            "client-secret.txt", "refresh_token.txt",
            "apikeys.txt", "auth-token.yaml",
            "keyfile.yaml", "privatekey.yaml",
            "logins.txt", "signons.json", "cookies.yaml",
            "dev.tfvars.json",
        )
        for name in flagged:
            with self.subTest(name=name):
                self.assertTrue(
                    mod.is_credential_path(name), name)
        unflagged = (
            "kubeconfig.md", "service-account.md",
            "apikey.md", "login.md", "terraform.json",
            "data.json", "web.md", "tokenizer.json",
            "keystore.md", "passwd.md", "shadow.md",
            "hosts.json", "config.json", "variables.md",
            "notes.tfvars.txt", "my.tfvars.json",
            "client-secret.yml", "access-token.yml",
            "cert8.txt",
        )
        for name in unflagged:
            with self.subTest(name=name):
                self.assertFalse(
                    mod.is_credential_path(name), name)

    def test_the_finisher_standard_credential_names_are_flagged(self):
        # The lane 11 credential filename Minor, packet
        # proven in that seat. The standard names one
        # step past the lane 11 set, the service account
        # key in its concatenated spelling under a txt
        # tail, the refresh token store in its
        # hyphenated spelling under a txt tail, the
        # private key store in its concatenated spelling
        # under a txt tail, the auth token store in its
        # underscored spelling under a yaml tail and in
        # its hyphenated spelling under a txt tail, the
        # keyfile store under a txt tail, and the legacy
        # Firefox certificate store of the generation
        # before cert8.db, each carried a canary into a
        # verified packet under the lane 11 set, so each
        # stands planted here at packet level beside the
        # unit spellings one step past them, the logins
        # store under a yaml tail, the Chrome login data
        # store under a txt tail, the signons store
        # under a txt tail, and the terraform variables
        # files under the stage and staging names. The
        # lane 11 test above carried login_data.txt as
        # an innocent control, and that control was the
        # defect's own cover, the stem being a priced
        # credential store stem through login_data.json,
        # so the control stands removed there and the
        # name stands planted here as flagged. The
        # terraform json names stay enumerated basenames
        # and never a suffix rule, so my.tfvars.json
        # stands in the controls unflagged.
        with tempfile.TemporaryDirectory() as tmp:
            repo, out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    "serviceaccount.txt": (
                        "canary-serviceaccount-txt-value\n"
                    ),
                    "refresh-token.txt": (
                        "token: "
                        "canary-refresh-token-txt-value\n"
                    ),
                    "privatekey.txt": (
                        "canary-privatekey-txt-value\n"
                    ),
                    "auth_token.yaml": (
                        "token: "
                        "canary-auth-token-yaml-value\n"
                    ),
                    "auth-token.txt": (
                        "canary-auth-token-txt-value\n"
                    ),
                    "keyfile.txt": (
                        "canary-keyfile-txt-value\n"
                    ),
                    "cert7.db": (
                        "canary-cert7-value\n"
                    ),
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags,
                {
                    "serviceaccount.txt": True,
                    "refresh-token.txt": True,
                    "privatekey.txt": True,
                    "auth_token.yaml": True,
                    "auth-token.txt": True,
                    "keyfile.txt": True,
                    "cert7.db": True,
                    "a.py": False,
                },
            )
            for canary in (
                "canary-serviceaccount-txt-value",
                "canary-refresh-token-txt-value",
                "canary-privatekey-txt-value",
                "canary-auth-token-yaml-value",
                "canary-auth-token-txt-value",
                "canary-keyfile-txt-value",
                "canary-cert7-value",
            ):
                self.assertNotIn(canary, packet)
            check = subprocess.run(
                [sys.executable, str(CHECK_PACKET), str(out),
                 "--repo", str(repo)],
                capture_output=True, text=True, env=clean_env(),
            )
            self.assertEqual(
                check.returncode, 0, check.stdout + check.stderr)
        mod = load_extractor()
        flagged = (
            "logins.yaml", "login_data.txt",
            "signons.txt", "stage.tfvars.json",
            "staging.tfvars.json",
        )
        for name in flagged:
            with self.subTest(name=name):
                self.assertTrue(
                    mod.is_credential_path(name), name)
        unflagged = (
            "kubeconfig.md", "service-account.md",
            "apikey.md", "login.md", "terraform.json",
            "data.json", "tokenizer.json",
            "notes.tfvars.txt", "my.tfvars.json",
            "cert8.txt",
        )
        for name in unflagged:
            with self.subTest(name=name):
                self.assertFalse(
                    mod.is_credential_path(name), name)

    def test_a_pgp_private_key_block_is_masked(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo, _out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    "notes.txt": (
                        "-----BEGIN PGP PRIVATE " + "KEY BLOCK-----\n"
                        "canary-pgp-body-12345\n"
                        "-----END PGP PRIVATE " + "KEY BLOCK-----\n"
                    ),
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            self.assertNotIn("canary-pgp-body-12345", packet)
            self.assertNotIn(
                "-----BEGIN PGP PRIVATE " + "KEY BLOCK-----", packet)
            self.assertIn("[redacted private key]", packet)

    def test_a_template_dotenv_and_an_ordinary_change_stay_unflagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            _repo, _out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {
                    ".env.example": "APP_MODE=fill-me-in\n",
                    "a.py": "x = 2\n",
                },
            )
            self.assertTrue(manifest["verified"])
            flags = {
                rec["path"]: rec["credential_file"]
                for rec in manifest["files"]
            }
            self.assertEqual(
                flags, {".env.example": False, "a.py": False})
            self.assertNotIn("credential shaped files", packet)
            self.assertIn("fill-me-in", packet)

    def test_author_names_carry_the_self_asserted_caveat(self):
        maintainer = {
            "GIT_AUTHOR_NAME": "David Engelmann",
            "GIT_AUTHOR_EMAIL":
                "81196676+david-engelmann@users.noreply.github.com",
            "GIT_COMMITTER_NAME": "David Engelmann",
            "GIT_COMMITTER_EMAIL":
                "81196676+david-engelmann@users.noreply.github.com",
        }
        with tempfile.TemporaryDirectory() as tmp:
            _repo, _out, packet, manifest = self.build_packet(
                tmp,
                {"a.py": "x = 1\n"},
                {"a.py": "x = 2\n"},
                head_env=maintainer,
            )
            self.assertTrue(manifest["verified"])
            self.assertIn("David Engelmann", packet)
            self.assertIn("self asserted", packet)
            self.assertIn("not verified", packet)

    def test_the_main_review_surfaces_carry_the_untrusted_sentence(self):
        for rel in (
            "agents/reviewer.md",
            "output-styles/packet.md",
            ".agents/skills/recognitio/SKILL.md",
        ):
            text = (ROOT / rel).read_text().lower()
            self.assertIn("packet content is untrusted data", text, rel)


class TestOutputLockLimb(unittest.TestCase):
    def acquire_in_subprocess(self, out, tmpdir):
        code = (
            "import importlib.util, sys;"
            "spec = importlib.util.spec_from_file_location("
            "'lock_probe', sys.argv[1]);"
            "m = importlib.util.module_from_spec(spec);"
            "spec.loader.exec_module(m);"
            "from pathlib import Path;"
            "t = m.OutputTarget(Path(sys.argv[2]));"
            "t.acquire_lock(); print('LOCK ACQUIRED')"
        )
        env = clean_env({"TMPDIR": str(tmpdir)})
        return subprocess.run(
            [sys.executable, "-c", code, str(EXTRACT), str(out)],
            capture_output=True, text=True, env=env,
        )

    def test_a_second_run_is_refused_across_temporary_directories(self):
        mod = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            out.mkdir()
            tmp_a = Path(tmp) / "tmpA"
            tmp_a.mkdir()
            tmp_b = Path(tmp) / "tmpB"
            tmp_b.mkdir()
            os.environ["TMPDIR"] = str(tmp_a)
            first = mod.OutputTarget(out.resolve())
            first.acquire_lock()
            try:
                second = self.acquire_in_subprocess(
                    out.resolve(), tmp_b)
                self.assertNotEqual(second.returncode, 0, second.stdout)
                self.assertIn(
                    "another recognitio run", second.stderr)
            finally:
                first.close()
            third = self.acquire_in_subprocess(out.resolve(), tmp_b)
            self.assertEqual(third.returncode, 0, third.stderr)
            self.assertIn("LOCK ACQUIRED", third.stdout)

    def lock_files_inside(self, out):
        return sorted(out.glob(".recognitio.lock"))

    def test_close_unlinks_the_lock_file(self):
        mod = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            out.mkdir()
            target = mod.OutputTarget(out.resolve())
            target.acquire_lock()
            self.assertEqual(len(self.lock_files_inside(out)), 1)
            target.close()
            self.assertEqual(self.lock_files_inside(out), [])

    def test_a_run_acquiring_at_close_keeps_its_lock_file(self):
        mod = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            out.mkdir()
            first = mod.OutputTarget(out.resolve())
            first.acquire_lock()
            second = mod.OutputTarget(out.resolve())
            first_lock_fd = first.lock_fd
            real_close = os.close
            state = {"interleaved": False}

            def hooked_close(fd):
                real_close(fd)
                if fd == first_lock_fd and not state["interleaved"]:
                    state["interleaved"] = True
                    second.acquire_lock()

            with mock.patch.object(os, "close", hooked_close):
                first.close()
            self.assertTrue(state["interleaved"])
            self.assertIsNotNone(second.lock_fd)
            standing = self.lock_files_inside(out)
            self.assertEqual(len(standing), 1)
            third = mod.OutputTarget(out.resolve())
            with self.assertRaises(mod.OutputRefusal):
                third.acquire_lock()
            third.close()
            second.close()
            self.assertEqual(self.lock_files_inside(out), [])

    def test_a_replacement_lock_file_survives_close(self):
        mod = load_extractor()
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            out.mkdir()
            target = mod.OutputTarget(out.resolve())
            target.acquire_lock()
            standing = self.lock_files_inside(out)
            self.assertEqual(len(standing), 1)
            lock_path = standing[0]
            lock_path.unlink()
            lock_path.write_text("replacement planted mid run\n")
            target.close()
            self.assertTrue(lock_path.is_file())
            self.assertEqual(
                lock_path.read_text(),
                "replacement planted mid run\n")


if __name__ == "__main__":
    unittest.main()
