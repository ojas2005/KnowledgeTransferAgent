"""Data contracts for repository evidence and generated guides."""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


class GuideError(ValueError):
    """Invalid input, repository evidence, or generated guide."""
