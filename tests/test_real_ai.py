from ai.real_ai import RealAI


def main():
    calls = []

    def fake_model(system_prompt: str, user_prompt: str) -> str:
        calls.append((system_prompt, user_prompt))
        return '{"status":"OK"}'

    ai = RealAI(
        fake_model,
        model_name="test-model",
    )

    response = ai.generate(
        "system prompt",
        "user prompt",
    )

    assert response == '{"status":"OK"}'
    assert ai.model_name == "test-model"

    assert calls == [
        (
            "system prompt",
            "user prompt",
        )
    ]

    print("REAL AI ADAPTER TEST: PASS")


if __name__ == "__main__":
    main()
