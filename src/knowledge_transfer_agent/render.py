"""Render a validated onboarding guide as Markdown or JSON."""

import json
from urllib.parse import quote

from .models import Claim, Guide


def citation_link(citation: str) -> str:
    path, line = citation.rsplit(":", 1)
    return "[{}:{}]({}#L{})".format(path, line, quote(path, safe="/"), line)
