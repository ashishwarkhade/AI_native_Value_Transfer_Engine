from typing import Callable, Optional

from ai.model_interface import AIModel


class RealAI(AIModel):
    """
    Provider-neutral AIModel adapter.

    The adapter does not contain route, compliance, eligibility,
    selection, or recommendation logic.

    A callable is injected that performs the actual model invocation:

        callable(system_prompt, user_prompt) -> str

    This keeps the application agents independent of any specific
    AI provider or SDK.
    """

    def __init__(
        self,
        generate_fn: Callable[[str, str], str],
        *,
        model_name: Optional[str] = None,
    ):
        if not callable(generate_fn):
            raise TypeError("generate_fn must be callable")

        self._generate_fn = generate_fn
        self.model_name = model_name

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not isinstance(system_prompt, str):
            raise TypeError("system_prompt must be a string")

        if not isinstance(user_prompt, str):
            raise TypeError("user_prompt must be a string")

        response = self._generate_fn(
            system_prompt,
            user_prompt,
        )

        if not isinstance(response, str):
            raise TypeError(
                "The injected AI generator must return a string"
            )

        if not response.strip():
            raise ValueError(
                "The injected AI generator returned an empty response"
            )

        return response
