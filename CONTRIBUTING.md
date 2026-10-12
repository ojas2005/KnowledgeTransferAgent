# Contributing

Keep scanning bounded, deterministic, and safe for an unfamiliar repository. Add focused tests for changes to file selection, citation validation, rendering, or the model response parser. Do not add real credentials or private repository content to fixtures.

Run the test suite before proposing a change:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

For a new language hint, prefer a small parser or conservative pattern and include an example showing where the hint helps task selection. Keep generated claims tied to numbered evidence lines.
