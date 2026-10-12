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


def render_markdown(guide: Guide) -> str:
    lines = ["# " + guide.title, "", "## Your assigned task", "", guide.task_summary, "",
             "## Module overview", "",
             "{} {}".format(guide.module_overview.text, cite(guide.module_overview.citations)), "",
             "## Relevant files", ""]
    for note in guide.relevant_files:
        lines.append("- **{}** — {}. {} {}".format(note.path, note.responsibility,
                                                   note.task_relevance, cite(note.citations)))
    lines.append("")
    for title, claims in [
        ("How the flow works", guide.flow),
        ("API dependencies", guide.api_dependencies),
        ("Database relationships", guide.database_relationships),
        ("Important conventions", guide.conventions),
        ("Local setup", guide.local_setup),
        ("First steps for this task", guide.first_steps),
    ]:
        claims_section(lines, title, claims)
    lines.extend(["## Unknowns to confirm", ""])
    if guide.unknowns:
        lines.extend("- " + item for item in guide.unknowns)
    else:
        lines.append("- None identified from the selected evidence.")
    lines.append("")
    return "\n".join(lines)
