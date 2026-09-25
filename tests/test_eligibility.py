from compliance.compliance_rules import evaluate_route
from compliance.first_pass_context import (
    create_india_brazil_first_pass_context,
)
from eligibility.eligibility_engine import evaluate_eligibility
from intent.value_transfer_intent import create_india_brazil_intent
from intelligence.route_intelligence import collect_route_intelligence
from route_discovery.route_discovery import discover_routes


def main():
    intent = create_india_brazil_intent()

    routes = discover_routes(intent)

    context = create_india_brazil_first_pass_context()

    print("\n=== ELIGIBILITY EVALUATION ===")

    decisions = []

    for route in routes:
        compliance = evaluate_route(route, context)
        intelligence = collect_route_intelligence(route)

        eligibility = evaluate_eligibility(
            compliance,
            intelligence,
        )

        decisions.append(eligibility)

        print(f"\nRoute: {eligibility.route_id}")
        print(f"Status: {eligibility.status}")

        print("\nReasons:")

        for reason in eligibility.reasons:
            print(f"  - {reason}")

        if eligibility.missing_information:
            print("\nMissing information:")

            for item in eligibility.missing_information:
                print(f"  - {item}")

    # ------------------------------------------------------------
    # First-pass design currently contains one real route.
    # ------------------------------------------------------------

    assert len(decisions) == 1

    decision = decisions[0]

    assert decision.route_id == "R-IN-BR-WISE-001"

    # ------------------------------------------------------------
    # Current expected result
    # ------------------------------------------------------------

    # Transaction-specific FX, fees and settlement data are now
    # known. The route is therefore NOT DATA_INCOMPLETE.
    #
    # However, Wise returned payment options and both are explicitly
    # disabled. Therefore there is no operational payment path for
    # this route in the current quote context.
    assert decision.status == "INELIGIBLE"

    # Known operational unavailability must not be represented
    # as missing information.
    assert decision.missing_information == []

    # The deterministic reason must identify the actual gate.
    assert any(
        "No enabled provider payment option" in reason
        for reason in decision.reasons
    )

    # Both currently returned Wise options are disabled, so the
    # decision should preserve their disabled reason codes.
    assert any(
        "error.payInmethod.disabled" in reason
        for reason in decision.reasons
    )

    print("\nPASS: Compliance + Intelligence -> Eligibility")


if __name__ == "__main__":
    main()