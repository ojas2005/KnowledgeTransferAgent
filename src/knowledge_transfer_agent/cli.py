"""Commands for scanning repositories and generating onboarding guides."""

import argparse
import json
import os
import sys
from pathlib import Path

from .client import ModelError, OpenAIResponsesClient
from .guide import KnowledgeTransferAgent, validate_citations
from .models import Context, Guide, GuideError
from .render import render_json, render_markdown
from .scanner import RepositoryScanner


def parser():
    top = argparse.ArgumentParser(prog="knowledge-transfer",
                                  description="Generate task-specific onboarding from repository evidence")
    commands = top.add_subparsers(dest="command", required=True)

    scan = commands.add_parser("scan", help="Collect task-focused repository evidence offline")
    scan.add_argument("--repo", required=True, type=Path)
    scan.add_argument("--task", required=True)
    scan.add_argument("--module", default="", help="Optional module or path focus")
    scan.add_argument("--max-files", type=int, default=18)
    scan.add_argument("--max-chars", type=int, default=60000)
    scan.add_argument("--out", type=Path, help="Write context JSON")

    generate = commands.add_parser("generate", help="Generate a guide with an OpenAI model")
    source = generate.add_mutually_exclusive_group(required=True)
    source.add_argument("--repo", type=Path, help="Repository to scan")
    source.add_argument("--context", type=Path, help="Previously saved context JSON")
    generate.add_argument("--task", help="Assigned developer task; required with --repo")
    generate.add_argument("--module", default="", help="Optional module or path focus")
    generate.add_argument("--max-files", type=int, default=18)
    generate.add_argument("--max-chars", type=int, default=60000)
    generate.add_argument("--model", default=os.environ.get("OPENAI_MODEL", ""),
                          help="OpenAI model supporting Structured Outputs")
    generate.add_argument("--markdown", type=Path, help="Write Markdown guide")
    generate.add_argument("--json", type=Path, help="Write guide JSON")

    validate = commands.add_parser("validate", help="Validate saved citations without API calls")
    validate.add_argument("--context", required=True, type=Path)
    validate.add_argument("--guide", required=True, type=Path)
    validate.add_argument("--markdown", type=Path, help="Write Markdown guide")
    return top
