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


def iter_files(root: Path, max_bytes: int) -> Iterable[Path]:
    for folder, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(name for name in directories
                                if name not in SKIP_DIRS and not (Path(folder) / name).is_symlink())
        for name in sorted(filenames):
            path = Path(folder) / name
            if eligible(path, root, max_bytes):
                yield path


def score_file(path: Path, text: str, terms: Set[str], module: str) -> int:
    relative = path.as_posix().lower()
    lower = text.lower()
    score = 0
    for term in terms:
        if term in relative:
            score += 12
        score += min(lower.count(term), 5) * 2
    if module and module.lower() in relative:
        score += 25
    if path.name in SETUP_NAMES:
        score += 8
    if "test" in relative or "spec" in relative:
        score += 2
    return score


def selected_lines(text: str, terms: Set[str], symbols, path: Path,
                   max_chars: int) -> Dict[int, str]:
    lines = text.splitlines()
    candidates: List[int] = []
    seen = set()

    def add(index: int) -> None:
        if 0 <= index < len(lines) and index not in seen:
            seen.add(index)
            candidates.append(index)

    for index, line in enumerate(lines):
        lower = line.lower()
        if any(term in lower for term in terms):
            for nearby in range(index - 2, index + 3):
                add(nearby)
    for symbol in symbols:
        for nearby in range(symbol.line - 2, symbol.line + 2):
            add(nearby)
    header = 55 if path.name in SETUP_NAMES or path.suffix == ".md" else 18
    for index in range(min(header, len(lines))):
        add(index)
    selected: Dict[int, str] = {}
    used = 0
    for index in candidates:
        line = redact_line(lines[index][:500])
        cost = len(line) + 20
        if used + cost > max_chars:
            continue
        selected[index + 1] = line
        used += cost
    return dict(sorted(selected.items()))
