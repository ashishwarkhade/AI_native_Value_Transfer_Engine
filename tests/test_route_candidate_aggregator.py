import json

from ai.model_interface import AIModel
from intent.value_transfer_intent import (
    create_india_brazil_intent,
)
from route_discovery.route_candidate_aggregator import (
    aggregate_candidate_routes,
)
from route_discovery.route_discovery_agent import (
    RouteDiscoveryAgent,
)


class MockRouteDiscoveryModel(AIModel):
    """
    Temporary AI model used to test route discovery aggregation.

    No deterministic route source is used.

    The model represents AI discovery of multiple plausible
    candidate routes. A provider such as Wise may be discovered
    by AI, but is not seeded by the architecture.
    """

    def __init__(self, routes):
        self.routes = routes

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        return json.dumps(
            {
                "routes": self.routes,
            }
        )


def build_ai_discovery_model_one():
    return MockRouteDiscoveryModel(
        [
            {
                "route_id": "R-IN-BR-BANKING-001",
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
                    "CROSS_BORDER_FX_PROVIDER",
                    "BRAZIL_LOCAL_BANKING",
                    "BRL",
                ],
                "delivery_method": (
                    "BRAZIL_LOCAL_BANK_ACCOUNT"
                ),
                "corridor_availability": (
                    "CANDIDATE_DISCOVERED"
                ),
                "route_requirements": [],
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
                    "BRAZIL_INSTANT_PAYMENT",
                    "BRL",
                ],
                "delivery_method": (
                    "BRAZIL_INSTANT_PAYMENT"
                ),
                "corridor_availability": (
                    "CANDIDATE_DISCOVERED"
                ),
                "route_requirements": [],
            },
        ]
    )


def build_ai_discovery_model_two():
    return MockRouteDiscoveryModel(
        [
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
                    "BRAZIL_INSTANT_PAYMENT",
                    "BRL",
                ],
                "delivery_method": (
                    "BRAZIL_INSTANT_PAYMENT"
                ),
                "corridor_availability": (
                    "CANDIDATE_DISCOVERED"
                ),
                "route_requirements": [],
            },
            {
                "route_id": "R-IN-BR-DIGITAL-ASSET-001",
                "rail": "DIGITAL_ASSET",
                "source_country": "India",
                "source_currency": "INR",
                "destination_country": "Brazil",
                "destination_currency": "BRL",
                "funding_method": (
                    "INDIA_BANK_ACCOUNT"
                ),
                "transfer_path": [
                    "INR",
                    "INDIA_BANK_ACCOUNT",
                    "DIGITAL_ASSET_RAIL",
                    "BRAZILIAN_OFF_RAMP",
                    "BRL",
                ],
                "delivery_method": (
                    "BRAZIL_LOCAL_BANK_ACCOUNT"
                ),
                "corridor_availability": (
                    "CANDIDATE_DISCOVERED"
                ),
                "route_requirements": [],
            },
        ]
    )


def main():
    print("\n=== AI ROUTE CANDIDATE AGGREGATOR ===")

    intent = create_india_brazil_intent()

    # ------------------------------------------------------------
    # AI discovery source 1
    # ------------------------------------------------------------

    agent_one = RouteDiscoveryAgent(
        build_ai_discovery_model_one()
    )

    ai_routes_one = agent_one.discover(intent)

    print("\nAI discovery source 1:")

    for route in ai_routes_one:
        print(
            f"  - {route.route_id} "
            f"[{route.rail}]"
        )

    # ------------------------------------------------------------
    # AI discovery source 2
    # ------------------------------------------------------------

    agent_two = RouteDiscoveryAgent(
        build_ai_discovery_model_two()
    )

    ai_routes_two = agent_two.discover(intent)

    print("\nAI discovery source 2:")

    for route in ai_routes_two:
        print(
            f"  - {route.route_id} "
            f"[{route.rail}]"
        )

    # ------------------------------------------------------------
    # Aggregate AI-discovered candidates only.
    # ------------------------------------------------------------

    routes = aggregate_candidate_routes(
        ai_routes_one,
        ai_routes_two,
    )

    print("\nAggregated candidate universe:")

    for route in routes:
        print(
            f"  - {route.route_id} "
            f"[{route.rail}]"
        )

    # ------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------

    assert len(ai_routes_one) == 2
    assert len(ai_routes_two) == 2

    # One route is intentionally discovered by both AI sources.
    # The aggregator must deduplicate it.
    assert len(routes) == 3

    route_ids = [
        route.route_id
        for route in routes
    ]

    assert route_ids == [
        "R-IN-BR-BANKING-001",
        "R-IN-BR-INSTANT-001",
        "R-IN-BR-DIGITAL-ASSET-001",
    ]

    # Every candidate must preserve the user's requested corridor.
    for route in routes:
        assert route.source.country == "India"
        assert route.source.currency == "INR"
        assert route.destination.country == "Brazil"
        assert route.destination.currency == "BRL"

    # Candidate routes remain discovery-only.
    for route in routes:
        assert (
            route.corridor_availability
            == "CANDIDATE_DISCOVERED"
        )

    print(
        "\nPASS: AI Discovery Sources "
        "-> Deduplicated Candidate Route Universe"
    )


if __name__ == "__main__":
    main()