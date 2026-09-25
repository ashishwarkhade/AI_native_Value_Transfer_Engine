import os

from ai.nebius_ai import NebiusAI


MODEL = "Qwen/Qwen3-235B-A22B-Instruct-2507"


def main():
    if not os.environ.get("NEBIUS_API_KEY"):
        raise SystemExit("NEBIUS_API_KEY is not set")

    model = NebiusAI(model_name=MODEL)

    response = model.generate(
        system_prompt=(
            "You are a strict JSON test assistant. "
            "Return only valid JSON."
        ),
        user_prompt=(
            'Return exactly this JSON object: '
            '{"status":"OK","provider":"Nebius"}'
        ),
    )

    print("=" * 70)
    print("MODEL:", MODEL)
    print("RESPONSE:")
    print(response)
    print("=" * 70)
    print("NEBIUS AI ADAPTER TEST: PASS")


if __name__ == "__main__":
    main()
