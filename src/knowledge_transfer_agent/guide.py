"""Evidence-grounded onboarding guide generation and citation checks."""

import json
from typing import Any, Dict, Protocol

from .models import Context, Guide, GuideError


class StructuredClient(Protocol):
    def structured(self, name: str, system: str, user: str,
                   schema: Dict[str, Any]) -> Dict[str, Any]:
        ...


CLAIM_SCHEMA = {
    "type": "object",
    "properties": {"text": {"type": "string"},
                   "citations": {"type": "array", "items": {"type": "string"}}},
    "required": ["text", "citations"],
    "additionalProperties": False,
}

FILE_SCHEMA = {
    "type": "object",
    "properties": {
        "path": {"type": "string"},
        "responsibility": {"type": "string"},
        "task_relevance": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["path", "responsibility", "task_relevance", "citations"],
    "additionalProperties": False,
}

GUIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "task_summary": {"type": "string"},
        "module_overview": CLAIM_SCHEMA,
        "relevant_files": {"type": "array", "items": FILE_SCHEMA},
        "flow": {"type": "array", "items": CLAIM_SCHEMA},
        "api_dependencies": {"type": "array", "items": CLAIM_SCHEMA},
        "database_relationships": {"type": "array", "items": CLAIM_SCHEMA},
        "conventions": {"type": "array", "items": CLAIM_SCHEMA},
        "local_setup": {"type": "array", "items": CLAIM_SCHEMA},
        "first_steps": {"type": "array", "items": CLAIM_SCHEMA},
        "unknowns": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "task_summary", "module_overview", "relevant_files", "flow",
                 "api_dependencies", "database_relationships", "conventions", "local_setup",
                 "first_steps", "unknowns"],
    "additionalProperties": False,
}
