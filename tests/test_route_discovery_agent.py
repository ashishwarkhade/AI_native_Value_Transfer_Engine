import json

from ai.model_interface import AIModel
from intent.value_transfer_intent import (
    create_india_brazil_intent,
)
from route_discovery.route_discovery_agent import (
    RouteDiscoveryAgent,
)


class MockRouteDiscoveryModel(AIModel):
    """
    Temporary mock AI model.

    This simulates an AI discovering multiple candidate routes
    for the India -> Brazil intent.

    No route is declared compliant or eligible here.
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        assert "VTI-IN-BR-001" in user_prompt
        assert "India" in user_prompt
        assert "Brazil" in user_prompt
        assert "100000" in user_prompt
        assert "INR" in user_prompt
        assert "BRL" in user_prompt

        return json.dumps(
            {
                "routes": [
                    {
                        "route_id": "R-IN-BR-WISE-001",
                        "rail": "BANKING",
                        "source_country": "India",
                        "source_currency": "INR",
                        "destination_country": "Brazil",
                        "destination_currency": "BRL",
                        "funding_method": (
                            "PERSONAL_INDIAN_BANK_ACCOUNT_OR_UPI"
                        ),
                        "transfer_path": [
                            "INR",
                            "INDIA_BANK_ACCOUNT_OR_UPI",
                            "WISE",
                            "FX",
                            "BRAZIL_LOCAL_BANKING",
                            "BRL",
                        ],
                        "delivery_method": (
                            "BRAZIL_LOCAL_BANK_ACCOUNT"
                        ),
                        "corridor_availability": (
                            "CANDIDATE_DISCOVERED"
                        ),
                        "route_requirements": [
                            "INDIAN_TAX_RESIDENT",
                            "INDIAN_PAN",
                            "PERSONAL_INDIAN_BANK_ACCOUNT",
                            "RECIPIENT_BRAZIL_BANK_DETAILS",
                        ],
                    },
                    {
                        "route_id": "R-IN-BR-ALT-001",
                        "rail": "BANKING",
                        "source_country": "India",
                        "source_currency": "INR",
                        "destination_country": "Brazil",
                        "destination_currency": "BRL",
                        "funding_method": (
                            "PERSONAL_INDIAN_BANK_ACCOUNT"
                        ),
                        "transfer_path": [
                            "INR",
                            "INDIA_BANK",
                            "AUTHORIZED_FX_PROVIDER",
                            "FX",
                            "BRAZIL_LOCAL_BANKING",
                            "BRL",
                        ],
                        "delivery_method": (
                            "BRAZIL_LOCAL_BANK_ACCOUNT"
                        ),
                        "corridor_availability": (
                            "CANDIDATE_DISCOVERED"
                        ),
                        "route_requirements": [
                            "INDIA_FX_PROVIDER_SUPPORT",
                            "INDIAN_KYC",
                            "RECIPIENT_BRAZIL_BANK_DETAILS",
                        ],
                    },
                    {
                        "route_id": "R-IN-BR-INSTANT-001",
                        "rail": "INSTANT_PAYMENT",
                        "source_country": "India",
                        "source_currency": "INR",
                        "destination_country": "Brazil",
                        "destination_currency": "BRL",
                        "funding_method": (
                            "INDIA_INSTANT_PAYMENT"
                        ),
                        "transfer_path": [
                            "INR",
                            "INDIA_INSTANT_PAYMENT",
                            "CROSS_BORDER_PAYMENT_PARTNER",
                            "FX",
                            "BRAZIL_INSTANT_PAYMENT",
                            "BRL",
                        ],
                        "delivery_method": (
                            "BRAZIL_INSTANT_PAYMENT"
                        ),
                        "corridor_availability": (
                            "CANDIDATE_DISCOVERED"
                        ),
                        "route_requirements": [
                            "CORRIDOR_PARTNER_SUPPORT",
                            "INDIAN_KYC",
                            "BRAZIL_RECIPIENT_REQUIREMENTS",
                        ],
                    },
                ]
            }
        )


def main():
    print("\n=== AI ROUTE DISCOVERY AGENT ===")

    intent = create_india_brazil_intent()

    model = MockRouteDiscoveryModel()

    agent = RouteDiscoveryAgent(model)

    routes = agent.discover(intent)

    print("\nDiscovered Candidate Routes:")

    for route in routes:
        print(f"\nRoute: {route.route_id}")
        print(f"  Rail: {route.rail}")
        print(
            f"  Funding: "
            f"{route.funding_method}"
        )
        print(
            f"  Delivery: "
            f"{route.delivery_method}"
        )
        print(
            f"  Availability: "
            f"{route.corridor_availability}"
        )

        print("  Path:")

        for step in route.transfer_path:
            print(f"    -> {step}")

    # ------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------

    assert len(routes) == 3

    route_ids = {
        route.route_id
        for route in routes
    }

    assert "R-IN-BR-WISE-001" in route_ids
    assert "R-IN-BR-ALT-001" in route_ids
    assert "R-IN-BR-INSTANT-001" in route_ids

    for route in routes:
        assert route.source.country == "India"
        assert route.source.currency == "INR"
        assert route.destination.country == "Brazil"
        assert route.destination.currency == "BRL"

        # Discovery only.
        assert (
            route.corridor_availability
            == "CANDIDATE_DISCOVERED"
        )

    print(
        "\nPASS: Value Transfer Intent -> "
        "AI Route Discovery Agent"
    )


if __name__ == "__main__":
    main()
