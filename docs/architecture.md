# Architecture

The CLI has three paths:

```text
repository -> RepositoryScanner -> Context -> KnowledgeTransferAgent -> Guide -> Markdown/JSON
                                      saved context --------^          |
                                      saved guide -> citation check ---+
```

`models.py` owns serializable contracts. `scanner.py` ranks eligible files and selects numbered excerpts. `symbols.py` provides conservative static hints; it does not execute repository code. `client.py` handles the Responses API request and failure states. `guide.py` defines the structured guide schema and validates citations. `render.py` produces output.

The model sees a reduced context: task, module focus, paths, role hints, symbols, imports, and numbered excerpts. Repository content is explicitly treated as untrusted input in the developer instruction. The validator only accepts citations to lines in that reduced context, making guide claims inspectable. A developer still needs to verify interpretations against the full source.

Scanning excludes known dependency and build directories, symlinked files, common secret filenames, and key file extensions. It also masks common literal credential assignments in selected excerpts. These checks are deliberately conservative and cannot guarantee that all sensitive content has been removed. Scan output is available for review before generation.
