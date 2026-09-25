from ai.ollama_ai import OllamaAI


def main():
    ai = OllamaAI(
        model_name="qwen3:4b",
    )

    response = ai.generate(
        system_prompt=(
            "You are a test assistant. "
            "Return exactly the requested JSON."
        ),
        user_prompt=(
            'Return exactly this JSON object: {"status":"OK"}'
        ),
    )

    print("MODEL:", ai.model_name)
    print("RESPONSE:", response)

    assert isinstance(response, str)
    assert response.strip()

    print("OLLAMA AI ADAPTER TEST: PASS")


if __name__ == "__main__":
    main()
