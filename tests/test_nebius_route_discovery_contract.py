import os

from ai.nebius_ai import NebiusAI
from route_discovery.route_discovery_agent import RouteDiscoveryAgent
from intent.value_transfer_intent import ValueTransferIntent


MODEL = "Qwen/Qwen3-235B-A22B-Instruct-2507"


def main():
    if not os.environ.get("NEBIUS_API_KEY"):
        raise SystemExit("NEBIUS_API_KEY is not set")

    ai = NebiusAI(model_name=MODEL)
    agent = RouteDiscoveryAgent(model=ai)

    intent = ValueTransferIntent(
        intent_id="VTI-BRICS-BR-IN-NEBIUS-001",
        from_country="Brazil",
        to_country="India",
        amount=100000,
        source_currency="BRL",
        destination_currency="INR",
        required_delivery_time="24h",
    )

    routes = agent.discover(intent)

    if not isinstance(routes, list):
        raise TypeError(
            f"Expected RouteDiscoveryAgent.discover() to return list, "
            f"got {type(routes).__name__}"
        )

    print("=" * 80)
    print("MODEL:", MODEL)
    print("CORRIDOR: Brazil -> India")
    print("ROUTES DISCOVERED:", len(routes))

    for i, route in enumerate(routes, 1):
        print(
            f"Route {i}: "
            f"{route.rail} | "
            f"{route.funding_method} | "
            f"{route.delivery_method}"
        )

    print("=" * 80)
    print("NEBIUS QWEN3-235B ROUTE DISCOVERY CONTRACT: PASS")


if __name__ == "__main__":
    main()
