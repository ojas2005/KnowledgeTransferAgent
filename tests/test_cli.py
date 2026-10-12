import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from knowledge_transfer_agent.cli import main
from knowledge_transfer_agent.models import Guide
from knowledge_transfer_agent.scanner import RepositoryScanner
from test_guide import sample_guide


DEMO = Path(__file__).resolve().parents[1] / "examples" / "auth_demo"


class CliTests(unittest.TestCase):
    def test_scan_and_validate_work_offline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context_path = root / "context.json"
            guide_path = root / "guide.json"
            markdown_path = root / "guide.md"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "--repo", str(DEMO), "--task",
                                       "Update login errors", "--module", "app",
                                       "--out", str(context_path)]), 0)
            saved = json.loads(context_path.read_text())
            self.assertEqual(saved["task"], "Update login errors")
            context = RepositoryScanner(DEMO).scan("Update login errors", "app")
            guide_path.write_text(json.dumps(Guide.from_dict(sample_guide(context)).to_dict()))
            self.assertEqual(main(["validate", "--context", str(context_path),
                                   "--guide", str(guide_path), "--markdown",
                                   str(markdown_path)]), 0)
            self.assertIn("## Relevant files", markdown_path.read_text())

    def test_generate_requires_task_for_repository(self):
        with contextlib.redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(["generate", "--repo", str(DEMO)]), 1)
        self.assertIn("--task is required", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
