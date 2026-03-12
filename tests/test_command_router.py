import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.command_router import configure_state_file, reset_state, respond


class CommandRouterPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        configure_state_file(None)
        reset_state()

    def test_todo_persists_with_state_file(self) -> None:
        with TemporaryDirectory() as tmpdir:
            state_file = str(Path(tmpdir) / "todos.json")
            configure_state_file(state_file)

            self.assertEqual(respond("/todo buy milk"), "TODO #1 captured: buy milk")

            reset_state()
            self.assertEqual(respond("/todo list"), "[ ] 1. buy milk")

    def test_todo_done_persists_with_state_file(self) -> None:
        with TemporaryDirectory() as tmpdir:
            state_file = str(Path(tmpdir) / "todos.json")
            configure_state_file(state_file)

            respond("/todo buy milk")
            self.assertEqual(respond("/todo done 1"), "TODO #1 marked done.")

            reset_state()
            self.assertEqual(respond("/todo list"), "[x] 1. buy milk")

    def test_corrupt_state_file_is_ignored(self) -> None:
        with TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "todos.json"
            state_path.write_text("{not-json", encoding="utf-8")
            configure_state_file(str(state_path))

            self.assertEqual(respond("/todo list"), "No TODO items.")

    def test_non_list_state_payload_is_ignored(self) -> None:
        with TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "todos.json"
            state_path.write_text('{"id": 1, "text": "bad-shape"}', encoding="utf-8")
            configure_state_file(str(state_path))

            self.assertEqual(respond("/todo list"), "No TODO items.")


if __name__ == "__main__":
    unittest.main()
