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


class RepositoryScanner:
    def __init__(self, root: Path, max_files: int = 18, max_chars: int = 60000,
                 max_file_bytes: int = 200000):
        self.root = Path(root).resolve()
        self.max_files = max_files
        self.max_chars = max_chars
        self.max_file_bytes = max_file_bytes
        if not self.root.is_dir():
            raise GuideError("Repository directory does not exist: {}".format(self.root))
        if max_files < 1 or max_chars < 1000 or max_file_bytes < 1000:
            raise GuideError("Scanner limits must be positive and large enough for source excerpts")

    def scan(self, task: str, module: str = "") -> Context:
        if not isinstance(task, str) or not task.strip():
            raise GuideError("Assigned task must be nonempty")
        terms = task_terms(task, module)
        candidates: List[Tuple[int, str, Path, str]] = []
        for path in iter_files(self.root, self.max_file_bytes):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "\x00" in text:
                continue
            relative = path.relative_to(self.root).as_posix()
            candidates.append((score_file(Path(relative), text, terms, module), relative, path, text))
        if not candidates:
            raise GuideError("No supported source or documentation files found")
        setup = sorted((item for item in candidates if Path(item[1]).name in SETUP_NAMES),
                       key=lambda item: (-item[0], item[1]))[:3]
        rest = sorted(candidates, key=lambda item: (-item[0], item[1]))
        chosen = []
        used_paths = set()
        for item in setup + rest:
            if item[1] not in used_paths:
                chosen.append(item)
                used_paths.add(item[1])
            if len(chosen) >= self.max_files:
                break
        remaining = self.max_chars
        files = []
        for _, relative, path, text in chosen:
            symbols, imports = hints(Path(relative), text)
            budget = min(6000, remaining)
            if budget < 300:
                break
            lines = selected_lines(text, terms, symbols, Path(relative), budget)
            if not lines:
                continue
            remaining -= sum(len(line) + 20 for line in lines.values())
            files.append(EvidenceFile(relative, role_hint(Path(relative)), lines, symbols[:40], imports[:30]))
        if not files:
            raise GuideError("No readable evidence remained after applying limits")
        return Context(self.root.name, task.strip(), module.strip(), files)
