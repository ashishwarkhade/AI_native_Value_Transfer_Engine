from abc import ABC, abstractmethod
from typing import Any, Dict


class AIModel(ABC):
    """
    Provider-neutral interface for an AI model.

    The Value Transfer Engine should depend on this interface,
    not on a specific model provider.
    """

    @abstractmethod
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """
        Generate a model response from system and user prompts.
        """
        raise NotImplementedError


def build_structured_context(data: Dict[str, Any]) -> str:
    """
    Convert structured engine data into a deterministic JSON
    representation suitable for an AI agent prompt.
    """

    import json

    return json.dumps(
        data,
        indent=2,
        sort_keys=True,
        default=str,
    )