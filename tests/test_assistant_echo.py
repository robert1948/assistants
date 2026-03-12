import unittest

from src.assistant_echo import respond


class AssistantEchoTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(respond("   "), "Please provide a message.")

    def test_help_command(self) -> None:
        self.assertEqual(
            respond("/help"),
            "Usage: provide text or '/todo <item>' for simple capture.",
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


if __name__ == "__main__":
    unittest.main()
