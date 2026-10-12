import io
import json
import unittest
from urllib.error import HTTPError

from knowledge_transfer_agent.client import ModelError, OpenAIResponsesClient, output_text


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class ClientTests(unittest.TestCase):
    def test_structured_request_and_output(self):
        seen = {}

        def opener(request, timeout):
            seen["payload"] = json.loads(request.data)
            seen["timeout"] = timeout
            self.assertEqual(request.full_url, "https://api.openai.com/v1/responses")
            data = {"status": "completed", "output": [{"type": "message", "content": [
                {"type": "output_text", "text": '{"answer":"ok"}'}]}]}
            return Response(json.dumps(data).encode())

        client = OpenAIResponsesClient("test-model", "test-key", opener=opener)
        self.assertEqual(client.structured("guide", "rules", "context", {"type": "object"}),
                         {"answer": "ok"})
        self.assertFalse(seen["payload"]["store"])
        self.assertTrue(seen["payload"]["text"]["format"]["strict"])
        self.assertEqual(seen["timeout"], 90)

    def test_refusal_and_incomplete_response(self):
        with self.assertRaisesRegex(ModelError, "refused"):
            output_text({"status": "completed", "output": [{"type": "message", "content": [
                {"type": "refusal", "refusal": "No"}]}]})
        with self.assertRaisesRegex(ModelError, "did not complete"):
            output_text({"status": "incomplete", "output": []})

    def test_http_error_is_reported(self):
        def opener(*_args, **_kwargs):
            raise HTTPError("https://api.openai.com/v1/responses", 401, "Unauthorized", {},
                            io.BytesIO(b'{"error":"invalid key"}'))

        client = OpenAIResponsesClient("test-model", "test-key", opener=opener)
        with self.assertRaisesRegex(ModelError, "HTTP 401"):
            client.structured("guide", "rules", "context", {"type": "object"})


if __name__ == "__main__":
    unittest.main()
