import unittest

from src.assistant_echo import reset_state, respond


class AssistantEchoTests(unittest.TestCase):
    def setUp(self) -> None:
        reset_state()

    def test_empty_input(self) -> None:
        self.assertEqual(respond("   "), "Please provide a message.")

    def test_help_command(self) -> None:
        self.assertEqual(
            respond("/help"),
            "Usage: text | /todo <item> | /todo list | /todo done <id> | /upper <text> | /lower <text> | /reverse <text>.",
        )

    def test_todo_command(self) -> None:
        self.assertEqual(respond("/todo buy milk"), "TODO #1 captured: buy milk")

    def test_todo_requires_text(self) -> None:
        self.assertEqual(
            respond("/todo   "),
            "Please provide todo text after '/todo'.",
        )

    def test_todo_list_empty(self) -> None:
        self.assertEqual(respond("/todo list"), "No TODO items.")

    def test_todo_list_with_items(self) -> None:
        respond("/todo buy milk")
        respond("/todo write tests")
        self.assertEqual(
            respond("/todo list"),
            "[ ] 1. buy milk\n[ ] 2. write tests",
        )

    def test_todo_done_marks_item(self) -> None:
        respond("/todo buy milk")
        self.assertEqual(respond("/todo done 1"), "TODO #1 marked done.")
        self.assertEqual(respond("/todo list"), "[x] 1. buy milk")

    def test_todo_done_requires_id(self) -> None:
        self.assertEqual(
            respond("/todo done"),
            "Please provide a todo id after '/todo done'.",
        )

    def test_todo_done_id_must_be_integer(self) -> None:
        self.assertEqual(
            respond("/todo done abc"),
            "Todo id must be a positive integer.",
        )

    def test_todo_done_missing_item(self) -> None:
        self.assertEqual(respond("/todo done 2"), "TODO #2 not found.")

    def test_todo_done_already_done(self) -> None:
        respond("/todo buy milk")
        respond("/todo done 1")
        self.assertEqual(respond("/todo done 1"), "TODO #1 is already done.")

    def test_echo_response(self) -> None:
        self.assertEqual(respond("hello"), "You said: hello")

    def test_upper_command(self) -> None:
        self.assertEqual(respond("/upper hello world"), "HELLO WORLD")

    def test_upper_requires_text(self) -> None:
        self.assertEqual(respond("/upper"), "Please provide text after '/upper'.")

    def test_lower_command(self) -> None:
        self.assertEqual(respond("/lower HeLLo"), "hello")

    def test_lower_requires_text(self) -> None:
        self.assertEqual(respond("/lower   "), "Please provide text after '/lower'.")

    def test_reverse_command(self) -> None:
        self.assertEqual(respond("/reverse abc123"), "321cba")

    def test_reverse_requires_text(self) -> None:
        self.assertEqual(
            respond("/reverse"),
            "Please provide text after '/reverse'.",
        )

    def test_unknown_command(self) -> None:
        self.assertEqual(
            respond("/unknown feature"),
            "Unknown command: /unknown. Try /help.",
        )

if __name__ == "__main__":
    unittest.main()
