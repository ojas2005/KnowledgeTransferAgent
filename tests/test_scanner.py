import tempfile
import unittest
from pathlib import Path

from knowledge_transfer_agent.models import Context, GuideError
from knowledge_transfer_agent.scanner import RepositoryScanner, redact_line, task_terms


DEMO = Path(__file__).resolve().parents[1] / "examples" / "auth_demo"


class ScannerTests(unittest.TestCase):
    def test_obvious_literal_credentials_are_redacted(self):
        self.assertEqual(redact_line('API_KEY = "long-private-value"'),
                         'API_KEY = [REDACTED]')
        self.assertEqual(redact_line('password = "short"'), 'password = "short"')

    def test_task_focus_finds_auth_files_and_setup(self):
        context = RepositoryScanner(DEMO, max_files=8).scan(
            "Understand the authentication module", "app")
        paths = {file.path for file in context.files}
        self.assertIn("README.md", paths)
        self.assertIn("app/auth.py", paths)
        self.assertIn("app/routes.py", paths)
        self.assertEqual(context.task, "Understand the authentication module")
        self.assertIn("auth", task_terms(context.task))
        restored = Context.from_dict(context.to_dict())
        self.assertEqual(restored.files[0].lines, context.files[0].lines)

    def test_secret_and_symlink_files_are_excluded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("Setup the auth service.\n", encoding="utf-8")
            (root / "auth.py").write_text("def authenticate():\n    pass\n", encoding="utf-8")
            (root / ".env").write_text("API_KEY=secret\n", encoding="utf-8")
            (root / "linked.py").symlink_to(root / "auth.py")
            paths = {item.path for item in RepositoryScanner(root).scan("auth").files}
            self.assertNotIn(".env", paths)
            self.assertNotIn("linked.py", paths)

    def test_empty_repository_and_invalid_limits_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(GuideError, "No supported"):
                RepositoryScanner(Path(directory)).scan("Understand login")
            with self.assertRaisesRegex(GuideError, "limits"):
                RepositoryScanner(Path(directory), max_files=0)


if __name__ == "__main__":
    unittest.main()
