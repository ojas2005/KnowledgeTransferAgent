"""Bounded repository discovery and task-focused evidence selection."""

import os
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .models import Context, EvidenceFile, GuideError
from .symbols import hints, role_hint


SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", ".next",
             "coverage", "vendor", "target", "out", ".idea", ".vscode", "__pycache__"}
EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".rs", ".rb",
              ".php", ".cs", ".sql", ".prisma", ".md", ".json", ".toml", ".yaml",
              ".yml", ".sh", ".txt"}
SPECIAL_NAMES = {"Dockerfile", "Makefile", ".env.example"}
SETUP_NAMES = {"README.md", "README.rst", "package.json", "pyproject.toml",
               "requirements.txt", "go.mod", "Cargo.toml", "Makefile", "Dockerfile"}
SENSITIVE_NAMES = {".env", ".npmrc", ".pypirc", "id_rsa", "id_ed25519", "credentials.json",
                   "secrets.json", "service-account.json"}
STOPWORDS = {"a", "an", "and", "the", "to", "for", "of", "in", "on", "with", "new", "developer",
             "understand", "help", "implement", "module", "feature", "project", "work", "task"}
SYNONYMS = {
    "authentication": {"auth", "login", "oauth", "session", "token"},
    "database": {"db", "model", "schema", "migration"},
    "api": {"route", "endpoint", "controller"},
    "payments": {"payment", "billing", "checkout"},
}
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(\b(?:api[_-]?key|secret|password|token|access[_-]?key)\b\s*[:=]\s*)"
    r"([\"']?)([^\s,;#\"']{8,})([\"']?)"
)


def redact_line(line: str) -> str:
    """Keep useful source context without sending obvious literal credentials."""
    return SECRET_ASSIGNMENT.sub(lambda match: match.group(1) + "[REDACTED]", line)


def task_terms(task: str, module: str = "") -> Set[str]:
    terms = {term.lower() for term in re.findall(r"[A-Za-z][A-Za-z0-9_]+", task + " " + module)}
    terms -= STOPWORDS
    expanded = set(terms)
    for term in terms:
        expanded.update(SYNONYMS.get(term, set()))
    return expanded


def eligible(path: Path, root: Path, max_bytes: int) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    relative = path.relative_to(root)
    if any(part in SKIP_DIRS for part in relative.parts[:-1]):
        return False
    if path.name in SENSITIVE_NAMES or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
        return False
    if path.name.startswith(".env") and path.name != ".env.example":
        return False
    if path.suffix.lower() not in EXTENSIONS and path.name not in SPECIAL_NAMES:
        return False
    try:
        return path.stat().st_size <= max_bytes
    except OSError:
        return False
