import json
import unittest
from pathlib import Path

from knowledge_transfer_agent.guide import KnowledgeTransferAgent, model_context, validate_citations
from knowledge_transfer_agent.models import Guide, GuideError
from knowledge_transfer_agent.render import render_markdown
from knowledge_transfer_agent.scanner import RepositoryScanner


DEMO = Path(__file__).resolve().parents[1] / "examples" / "auth_demo"


def cited_line(context, path, contains):
    file = next(item for item in context.files if item.path == path)
    line = next(number for number, text in file.lines.items() if contains in text)
    return "{}:{}".format(path, line)


def sample_guide(context):
    route = cited_line(context, "app/routes.py", '"/login"')
    auth = cited_line(context, "app/auth.py", "def authenticate")
    setup = cited_line(context, "README.md", "uvicorn")
    claim = lambda text, citation: {"text": text, "citations": [citation]}
    return {
        "title": "Authentication onboarding", "task_summary": context.task,
        "module_overview": claim("The login endpoint delegates credential checks.", route),
        "relevant_files": [
            {"path": "app/routes.py", "responsibility": "HTTP endpoint",
             "task_relevance": "Start here for the request flow", "citations": [route]},
            {"path": "app/auth.py", "responsibility": "Credential check",
             "task_relevance": "Inspect authentication logic", "citations": [auth]},
        ],
        "flow": [claim("The route calls the credential checker.", route)],
        "api_dependencies": [claim("The app exposes POST /login.", route)],
        "database_relationships": [], "conventions": [],
        "local_setup": [claim("Run the app with uvicorn.", setup)],
        "first_steps": [claim("Read the authentication function.", auth)],
        "unknowns": ["No persistent database relationship is shown."],
    }


class FakeClient:
    def __init__(self, answer):
        self.answer = answer
        self.calls = []

    def structured(self, name, system, user, schema):
        self.calls.append((name, system, json.loads(user), schema))
        return self.answer


class GuideTests(unittest.TestCase):
    def setUp(self):
        self.context = RepositoryScanner(DEMO, max_files=8).scan(
            "Understand authentication before updating login errors", "app")

    def test_guide_is_task_specific_and_cited(self):
        fake = FakeClient(sample_guide(self.context))
        guide = KnowledgeTransferAgent(fake).generate(self.context)
        markdown = render_markdown(guide)
        self.assertIn("## First steps for this task", markdown)
        self.assertIn("app/routes.py#L", markdown)
        self.assertEqual(fake.calls[0][0], "onboarding_guide")
        self.assertEqual(fake.calls[0][2]["assigned_task"], self.context.task)
        self.assertIn("L", fake.calls[0][2]["files"][0]["excerpt"])

    def test_citation_must_be_supplied_line(self):
        raw = sample_guide(self.context)
        raw["flow"][0]["citations"] = ["app/routes.py:999"]
        with self.assertRaisesRegex(GuideError, "not supplied"):
            validate_citations(Guide.from_dict(raw), self.context)

    def test_file_note_must_cite_its_file(self):
        raw = sample_guide(self.context)
        raw["relevant_files"][0]["citations"] = raw["relevant_files"][1]["citations"]
        with self.assertRaisesRegex(GuideError, "cite its own file"):
            validate_citations(Guide.from_dict(raw), self.context)

    def test_model_context_uses_numbered_excerpts(self):
        payload = model_context(self.context)
        self.assertEqual(payload["module_focus"], "app")
        self.assertTrue(any("L1:" in item["excerpt"] for item in payload["files"]))


if __name__ == "__main__":
    unittest.main()
