"""Data contracts for repository evidence and generated guides."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


class GuideError(ValueError):
    """Invalid input, repository evidence, or generated guide."""


def required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuideError("{} must be a nonempty string".format(label))
    return value.strip()


def strings(value: Any, label: str) -> List[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise GuideError("{} must be a list of nonempty strings".format(label))
    return [item.strip() for item in value]


@dataclass(frozen=True)
class Symbol:
    name: str
    kind: str
    line: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Symbol":
        if not isinstance(data, dict) or type(data.get("line")) is not int or data["line"] < 1:
            raise GuideError("Invalid symbol")
        return cls(required_text(data.get("name"), "symbol.name"),
                   required_text(data.get("kind"), "symbol.kind"), data["line"])


@dataclass(frozen=True)
class EvidenceFile:
    path: str
    role_hint: str
    lines: Dict[int, str]
    symbols: List[Symbol] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvidenceFile":
        if not isinstance(data, dict) or not isinstance(data.get("lines"), dict):
            raise GuideError("Invalid evidence file")
        path = required_text(data.get("path"), "evidence.path")
        if path.startswith("/") or ".." in path.split("/"):
            raise GuideError("Evidence paths must be repository-relative")
        lines = {}
        for key, value in data["lines"].items():
            try:
                number = int(key)
            except (TypeError, ValueError) as exc:
                raise GuideError("Evidence line numbers must be integers") from exc
            if number < 1 or not isinstance(value, str):
                raise GuideError("Invalid evidence line in {}".format(path))
            lines[number] = value
        return cls(path, required_text(data.get("role_hint"), "evidence.role_hint"),
                   lines, [Symbol.from_dict(item) for item in data.get("symbols", [])],
                   strings(data.get("imports", []), "evidence.imports"))

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Context:
    project: str
    task: str
    module: str
    files: List[EvidenceFile]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Context":
        if not isinstance(data, dict):
            raise GuideError("Context must be an object")
        files = data.get("files")
        if not isinstance(files, list) or not files:
            raise GuideError("Context must contain at least one evidence file")
        parsed = [EvidenceFile.from_dict(item) for item in files]
        paths = [item.path for item in parsed]
        if len(set(paths)) != len(paths):
            raise GuideError("Evidence paths must be unique")
        module = data.get("module", "")
        if not isinstance(module, str):
            raise GuideError("module must be a string")
        return cls(required_text(data.get("project"), "project"),
                   required_text(data.get("task"), "task"), module.strip(), parsed)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Claim:
    text: str
    citations: List[str]

    @classmethod
    def from_dict(cls, data: Dict[str, Any], label: str) -> "Claim":
        if not isinstance(data, dict):
            raise GuideError("{} must be an object".format(label))
        citations = strings(data.get("citations"), label + ".citations")
        if not citations:
            raise GuideError("{} requires at least one citation".format(label))
        return cls(required_text(data.get("text"), label + ".text"), citations)
