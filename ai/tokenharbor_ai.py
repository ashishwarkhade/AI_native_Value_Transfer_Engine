import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ai.model_interface import AIModel


class TokenHarborAI(AIModel):
    """
    Token Harbor OpenAI-compatible AIModel adapter.

    The API key is read from the TOKENHARBOR_API_KEY
    environment variable.

    The adapter returns only the assistant's `content` field
    to the VTE AI agents. Provider-specific fields such as
    reasoning_content remain outside the VTE model contract.
    """

    def __init__(
        self,
        model_name: str = "qwen3.8-flash",
        base_url: str = "https://tokenharbor.ai/v1",
        timeout: int = 300,
    ):
        import os

        api_key = os.getenv("TOKENHARBOR_API_KEY")

        if not api_key:
            raise RuntimeError(
                "TOKENHARBOR_API_KEY environment variable is not set."
            )

        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key

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
        }

        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
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
                f"Token Harbor HTTP error {exc.code}: {body}"
            ) from exc

        except URLError as exc:
            raise RuntimeError(
                f"Unable to connect to Token Harbor at {self.base_url}: {exc}"
            ) from exc

        try:
            result = json.loads(raw)

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Token Harbor returned invalid JSON"
            ) from exc

        try:
            content = result["choices"][0]["message"]["content"]

        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                "Token Harbor response did not contain "
                "choices[0].message.content"
            ) from exc

        if not isinstance(content, str):
            raise RuntimeError(
                "Token Harbor assistant content was not a string"
            )

        if not content.strip():
            raise RuntimeError(
                "Token Harbor returned an empty assistant response"
            )

        return content
