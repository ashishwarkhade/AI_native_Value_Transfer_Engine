import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai.model_interface import AIModel


class NebiusAI(AIModel):
    """
    Provider-neutral AIModel adapter for Nebius Token Factory.

    Nebius exposes an OpenAI-compatible chat-completions API.

    Environment:
        NEBIUS_API_KEY

    Example:
        model = NebiusAI(
            model_name="Qwen/Qwen3-235B-A22B-Instruct-2507"
        )

        response = model.generate(
            system_prompt="You are a helpful assistant.",
            user_prompt="Return JSON: {\"status\":\"OK\"}"
        )
    """

    DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1"

    def __init__(
        self,
        model_name: str = "Qwen/Qwen3-235B-A22B-Instruct-2507",
        *,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 300,
    ):
        import os

        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.api_key = api_key or os.environ.get("NEBIUS_API_KEY")

        if not self.api_key:
            raise ValueError(
                "NEBIUS_API_KEY is not set and no api_key was provided."
            )

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not isinstance(system_prompt, str):
            raise TypeError("system_prompt must be a string")

        if not isinstance(user_prompt, str):
            raise TypeError("user_prompt must be a string")

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "temperature": 0,
            "stream": False,
        }

        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")

        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Nebius HTTP error {exc.code}: {body}"
            ) from exc

        except URLError as exc:
            raise RuntimeError(
                f"Unable to connect to Nebius at {self.base_url}: {exc}"
            ) from exc

        try:
            result = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Nebius returned invalid JSON"
            ) from exc

        try:
            response_text = result["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"Nebius response did not contain "
                f"choices[0].message.content: {result}"
            ) from exc

        if not isinstance(response_text, str):
            raise RuntimeError(
                "Nebius response content was not a string"
            )

        if not response_text.strip():
            raise RuntimeError(
                "Nebius returned an empty model response"
            )

        return response_text
