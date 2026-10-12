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


class OpenAIResponsesClient:
    def __init__(self, model: str, api_key: Optional[str] = None, timeout: int = 90,
                 opener: Optional[Callable] = None):
        self.model = model.strip()
        self.api_key = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
        self.timeout = timeout
        self.opener = opener or urlopen
        if not self.model:
            raise ModelError("A model is required (--model or OPENAI_MODEL)")
        if not self.api_key:
            raise ModelError("OPENAI_API_KEY is required to generate a guide")

    def structured(self, name: str, system: str, user: str,
                   schema: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "store": False,
            "input": [{"role": "developer", "content": system},
                      {"role": "user", "content": user}],
            "text": {"format": {"type": "json_schema", "name": name,
                                "strict": True, "schema": schema}},
        }
        request = Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": "Bearer " + self.api_key,
                     "Content-Type": "application/json"},
            method="POST",
        )
        for attempt in range(3):
            try:
                with self.opener(request, timeout=self.timeout) as result:
                    response = json.load(result)
                break
            except HTTPError as exc:
                if exc.code in {429, 500, 502, 503, 504} and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                detail = exc.read().decode("utf-8", errors="replace")[:300]
                raise ModelError("OpenAI request failed (HTTP {}): {}".format(exc.code, detail)) from exc
            except URLError as exc:
                raise ModelError("OpenAI request failed: {}".format(exc.reason)) from exc
            except (OSError, ValueError) as exc:
                raise ModelError("Invalid OpenAI response: {}".format(exc)) from exc
        try:
            data = json.loads(output_text(response))
        except json.JSONDecodeError as exc:
            raise ModelError("Model returned invalid guide JSON") from exc
        if not isinstance(data, dict):
            raise ModelError("Model guide output must be a JSON object")
        return data
