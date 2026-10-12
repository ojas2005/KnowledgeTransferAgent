"""Render a validated onboarding guide as Markdown or JSON."""

import json
from urllib.parse import quote

from .models import Claim, Guide


def citation_link(citation: str) -> str:
    path, line = citation.rsplit(":", 1)
    return "[{}:{}]({}#L{})".format(path, line, quote(path, safe="/"), line)


def cite(citations) -> str:
    return " ".join(citation_link(item) for item in citations)


def claims_section(lines, title: str, claims) -> None:
    lines.extend(["## " + title, ""])
    if claims:
        for claim in claims:
            lines.append("- {} {}".format(claim.text, cite(claim.citations)))
    else:
        lines.append("No evidence found in the selected files. See Unknowns.")
    lines.append("")
