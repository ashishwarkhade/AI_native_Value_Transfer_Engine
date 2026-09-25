import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai.model_interface import AIModel


class OllamaAI(AIModel):
    """
    AIModel implementation backed by a local Ollama HTTP server.

    The application agents remain unaware of Ollama.
    They interact only with the AIModel interface.
    """

    def __init__(
        self,
        model_name: str = "qwen3:4b",
        base_url: str = "http://127.0.0.1:11434",
        timeout: int = 300,
    ):
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not isinstance(system_prompt, str):
            raise TypeError("system_prompt must be a string")

        if not isinstance(user_prompt, str):
            raise TypeError("user_prompt must be a string")

        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": 0,
            },
        }

        request = Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")

        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Ollama HTTP error {exc.code}: {body}"
            ) from exc

        except URLError as exc:
            raise RuntimeError(
                f"Unable to connect to Ollama at {self.base_url}: {exc}"
            ) from exc

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Ollama returned invalid JSON"
            ) from exc

        response_text = result.get("response")

        if not isinstance(response_text, str):
            raise RuntimeError(
                "Ollama response did not contain a string 'response' field"
            )

        if not response_text.strip():
            raise RuntimeError(
                "Ollama returned an empty model response"
            )

        return response_text
