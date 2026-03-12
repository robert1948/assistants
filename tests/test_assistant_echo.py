import unittest

from src.assistant_echo import respond


class AssistantEchoTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(respond("   "), "Please provide a message.")

    def test_help_command(self) -> None:
        self.assertEqual(
            respond("/help"),
            "Usage: text | /todo <item> | /upper <text> | /lower <text> | /reverse <text>.",
        )

    def test_todo_command(self) -> None:
        self.assertEqual(respond("/todo buy milk"), "TODO captured: buy milk")

    def test_todo_requires_text(self) -> None:
        self.assertEqual(
            respond("/todo   "),
            "Please provide todo text after '/todo'.",
        )

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
