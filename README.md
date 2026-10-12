# Knowledge Transfer Agent

Create a developer onboarding guide for a **specific assigned task** from a repository. The agent scans likely files, extracts bounded line-numbered evidence, asks an OpenAI model for a structured guide, and rejects citations that do not point to the supplied evidence.

A guide covers the module overview, relevant files, execution flow, API dependencies, database relationships, conventions, local setup, and first steps for the task. Sections without evidence stay empty and are called out as unknowns.

## Quick start

Requires Python 3.9+ and an OpenAI API key for guide generation. Scanning and validation work offline.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
export OPENAI_API_KEY=your_key
export OPENAI_MODEL=your_structured_outputs_model
knowledge-transfer generate \
  --repo /path/to/project \
  --task "Help a new developer update login error handling" \
  --module app/auth \
  --markdown /path/to/project/ONBOARDING.md \
  --json guide.json
```

The Markdown file is best saved in the repository root: source links in the guide are relative to that root. `--module` can be a module name or path fragment; it increases the ranking of related files.

To inspect what would be sent to the model first:

```bash
knowledge-transfer scan \
  --repo /path/to/project \
  --task "Update login error handling" \
  --module app/auth \
  --out context.json
knowledge-transfer generate --context context.json --markdown ONBOARDING.md
knowledge-transfer validate --context context.json --guide guide.json
```

`generate --context` still needs `OPENAI_API_KEY` and `OPENAI_MODEL` (or `--model`). `validate` checks a saved guide without an API call. To keep the machine-readable result, pass `--json` when generating. The tool exits with a nonzero status and an error message for invalid evidence, model failures, or unsupported citations.

## Worked example

The [`auth_demo`](examples/auth_demo/README.md) directory contains a small authentication service. Its [scan context](examples/auth_context.json), [guide JSON](examples/auth_guide.json), and [onboarding guide](examples/auth_demo/ONBOARDING.md) show the full output format. The guide is a checked example built from the offline context; it is not presented as a live model result.

Regenerate the evidence and validate the example:

```bash
knowledge-transfer scan \
  --repo examples/auth_demo \
  --task "Help a new developer update login error handling in the authentication module" \
  --module app \
  --out examples/auth_context.json
knowledge-transfer validate \
  --context examples/auth_context.json \
  --guide examples/auth_guide.json \
  --markdown examples/auth_demo/ONBOARDING.md
```

## How it works

1. The scanner walks supported source and documentation files, skipping dependencies, build output, symlinks, common credential files, and large files.
2. Task words, module focus, setup files, and source hints rank the files. Python AST and lightweight JavaScript, TypeScript, Prisma, and SQL patterns provide symbol hints. Selected excerpts retain original line numbers.
3. The guide generator sends only the selected context to the Responses API using a strict JSON schema. Its request sets `store: false`.
4. The validator requires every guide claim to cite a supplied `path:line` and every file note to cite its own file. Markdown rendering links those citations to source lines.

The scanner defaults to at most 18 files, 60,000 excerpt characters, and 200 KB per file. Use `--max-files` and `--max-chars` to adjust the first two limits. Source snippets are truncated to 500 characters per line. Obvious literal credentials are redacted, but this is a best-effort filter. Review `context.json` before using a private or sensitive repository. Do not include secrets in tasks or source sent to the model.

This is an orientation aid, not a full static analyzer. Dynamic imports, generated code, runtime configuration, and behavior outside the selected files may be missed. Citations prove the model referenced supplied lines; they do not prove every inference is correct. Confirm important details in the source before changing code.

