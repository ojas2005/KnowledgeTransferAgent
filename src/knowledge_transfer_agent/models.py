"""Data contracts for repository evidence and generated guides."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


class GuideError(ValueError):
    """Invalid input, repository evidence, or generated guide."""


def required_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise GuideError("{} must be a nonempty string".format(label))
    return value.strip()
