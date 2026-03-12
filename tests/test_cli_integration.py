import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class CliIntegrationTests(unittest.TestCase):
    def _run_cli(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        return subprocess.run(
            [sys.executable, "-m", "src.assistant_echo", *args],
            capture_output=True,
            text=True,
            check=False,
            env=merged_env,
        )

    def test_health_flag(self) -> None:
        result = self._run_cli("--health")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "ok")

    def test_version_flag(self) -> None:
        result = self._run_cli("--version")
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.strip().startswith("assistants-cli "))

    def test_env_state_file_is_used(self) -> None:
        with TemporaryDirectory() as tmpdir:
            state_path = str(Path(tmpdir) / "from-env.json")
            env = {"ASSISTANTS_STATE_FILE": state_path}

            create = self._run_cli("/todo buy milk", env=env)
            self.assertEqual(create.returncode, 0)
            self.assertEqual(create.stdout.strip(), "TODO #1 captured: buy milk")

            listing = self._run_cli("/todo list", env=env)
            self.assertEqual(listing.returncode, 0)
            self.assertEqual(listing.stdout.strip(), "[ ] 1. buy milk")

    def test_cli_state_file_overrides_env(self) -> None:
        with TemporaryDirectory() as tmpdir:
            env_path = str(Path(tmpdir) / "from-env.json")
            cli_path = str(Path(tmpdir) / "from-cli.json")
            env = {"ASSISTANTS_STATE_FILE": env_path}

            result = self._run_cli("--state-file", cli_path, "/todo buy eggs", env=env)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "TODO #1 captured: buy eggs")

            env_list = self._run_cli("/todo list", env=env)
            self.assertEqual(env_list.returncode, 0)
            self.assertEqual(env_list.stdout.strip(), "No TODO items.")

            cli_list = self._run_cli("--state-file", cli_path, "/todo list", env=env)
            self.assertEqual(cli_list.returncode, 0)
            self.assertEqual(cli_list.stdout.strip(), "[ ] 1. buy eggs")


if __name__ == "__main__":
    unittest.main()
