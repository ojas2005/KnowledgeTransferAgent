"""Cheap static hints for files likely to matter to a new developer."""

import ast
import re
from pathlib import Path
from typing import List, Tuple

from .models import Symbol


HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def python_hints(text: str) -> Tuple[List[Symbol], List[str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return [], []
    symbols = []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(("." * node.level) + (node.module or ""))
        elif isinstance(node, ast.ClassDef):
            symbols.append(Symbol(node.name, "class", node.lineno))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            symbols.append(Symbol(node.name, "function", node.lineno))
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                    continue
                method = decorator.func.attr.lower()
                if method not in HTTP_METHODS or not decorator.args:
                    continue
                try:
                    route = ast.literal_eval(decorator.args[0])
                except (ValueError, TypeError, SyntaxError):
                    continue
                if isinstance(route, str):
                    symbols.append(Symbol("{} {}".format(method.upper(), route), "route", decorator.lineno))
        elif isinstance(node, ast.Call) and isinstance(node.func, (ast.Name, ast.Attribute)):
            if getattr(node.func, "id", getattr(node.func, "attr", "")) == "ForeignKey" and node.args:
                try:
                    target = ast.literal_eval(node.args[0])
                except (ValueError, TypeError, SyntaxError):
                    continue
                if isinstance(target, str):
                    symbols.append(Symbol(target, "foreign-key", node.lineno))
    return sorted(symbols, key=lambda item: item.line), sorted(set(imports))
