import argparse
import os
import unittest
from unittest.mock import patch

from src.assistant_echo import _resolve_state_file, main, reset_state, run


class AssistantEntrypointTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ.pop("ASSISTANTS_STATE_FILE", None)
        reset_state()

    def test_resolve_state_file_cli_has_priority(self) -> None:
        os.environ["ASSISTANTS_STATE_FILE"] = "from-env.json"
        self.assertEqual(_resolve_state_file("from-cli.json"), "from-cli.json")

    def test_resolve_state_file_uses_env_when_cli_missing(self) -> None:
        os.environ["ASSISTANTS_STATE_FILE"] = "from-env.json"
        self.assertEqual(_resolve_state_file(None), "from-env.json")

    def test_resolve_state_file_default_value(self) -> None:
        self.assertEqual(_resolve_state_file(None), ".assistant_todos.json")

    def test_run_version(self) -> None:
        args = argparse.Namespace(
            version=True,
            health=False,
            state_file=None,
            interactive=False,
            message="",
        )
        out: list[str] = []
        self.assertEqual(run(args, write_output=out.append), 0)
        self.assertEqual(out, ["assistants-cli 0.2.0"])

    def test_run_health(self) -> None:
        args = argparse.Namespace(
            version=False,
            health=True,
            state_file=None,
            interactive=False,
            message="",
        )
        out: list[str] = []
        self.assertEqual(run(args, write_output=out.append), 0)
        self.assertEqual(out, ["ok"])

    def test_run_message_response(self) -> None:
        args = argparse.Namespace(
            version=False,
            health=False,
            state_file="",
            interactive=False,
            message="hello",
        )
        out: list[str] = []
        self.assertEqual(run(args, write_output=out.append), 0)
        self.assertEqual(out, ["You said: hello"])

    def test_run_interactive_exit(self) -> None:
        args = argparse.Namespace(
            version=False,
            health=False,
            state_file="",
            interactive=True,
            message="",
        )
        values = iter(["/exit"])
        out: list[str] = []

        def fake_input(prompt: str) -> str:
            self.assertEqual(prompt, "> ")
            return next(values)

        self.assertEqual(run(args, read_input=fake_input, write_output=out.append), 0)
        self.assertEqual(out, ["Interactive mode. Type /exit to quit.", "Goodbye."])

    def test_run_interactive_eof(self) -> None:
        args = argparse.Namespace(
            version=False,
            health=False,
            state_file="",
            interactive=True,
            message="",
        )
        out: list[str] = []

        def fake_input(prompt: str) -> str:
            self.assertEqual(prompt, "> ")
            raise EOFError

        self.assertEqual(run(args, read_input=fake_input, write_output=out.append), 0)
        self.assertEqual(out, ["Interactive mode. Type /exit to quit.", "\nGoodbye."])

    def test_main_accepts_argv(self) -> None:
        with patch("src.assistant_echo.run", return_value=0) as mocked_run:
            self.assertEqual(main(["--version"]), 0)

        mocked_run.assert_called_once()
        parsed_args = mocked_run.call_args.args[0]
        self.assertTrue(parsed_args.version)
        self.assertFalse(parsed_args.health)


if __name__ == "__main__":
    unittest.main()
