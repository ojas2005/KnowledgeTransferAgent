"""Small OpenAI Responses API client for a strict JSON guide."""

import json
import os
import time
from typing import Any, Callable, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ModelError(RuntimeError):
    """The model request failed or returned unusable output."""


def output_text(response: Dict[str, Any]) -> str:
    if response.get("status") != "completed":
        raise ModelError("Model response did not complete: {}".format(response.get("status", "unknown")))
    parts = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "refusal":
                raise ModelError("Model refused the guide request")
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                parts.append(content["text"])
    if not parts:
        raise ModelError("Model response contained no guide text")
    return "".join(parts)
