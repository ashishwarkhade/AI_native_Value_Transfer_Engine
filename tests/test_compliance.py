from compliance.compliance_rules import evaluate_route
from compliance.first_pass_context import (
    create_india_brazil_first_pass_context,
)
from intent.value_transfer_intent import create_india_brazil_intent
from route_discovery.route_discovery import discover_routes


def main():
    intent = create_india_brazil_intent()

    routes = discover_routes(intent)

    context = create_india_brazil_first_pass_context()

    print("\n=== COMPLIANCE CONTEXT ===")
    print(context)

    print("\n=== COMPLIANCE EVALUATION ===")

    decisions = []

    for route in routes:
        decision = evaluate_route(route, context)
        decisions.append(decision)

        print(f"\nRoute: {decision.route_id}")
        print(f"Status: {decision.status}")

        for result in decision.rule_results:
            print(
                f"  [{result.status}] "
                f"{result.rule_id}: "
                f"{result.explanation}"
            )

        if decision.missing_information:
            print("  Missing information:")
            for item in decision.missing_information:
                print(f"    - {item}")

    assert len(decisions) == 2

    print("\nPASS: Candidate Routes -> Compliance Evaluation")


if __name__ == "__main__":
    main()
