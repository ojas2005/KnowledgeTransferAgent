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
