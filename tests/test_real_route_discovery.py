from ai.ollama_ai import OllamaAI
from intent.value_transfer_intent import ValueTransferIntent
from route_discovery.route_discovery_agent import RouteDiscoveryAgent


def main():
    intent = ValueTransferIntent(
        intent_id="VTI-IN-BR-REAL-001",
        from_country="India",
        to_country="Brazil",
        amount=100000,
        source_currency="INR",
        destination_currency="BRL",
        required_delivery_time="24h",
    )

    ai = OllamaAI(
        model_name="qwen3:4b",
    )

    agent = RouteDiscoveryAgent(ai)

    routes = agent.discover(intent)

    print()
    print("=" * 72)
    print("REAL AI ROUTE DISCOVERY")
    print("=" * 72)

    print(f"Intent: {intent.intent_id}")
    print(f"Corridor: {intent.from_country} -> {intent.to_country}")
    print(
        f"Value: {intent.amount} "
        f"{intent.source_currency} -> {intent.destination_currency}"
    )
    print(f"Required delivery: {intent.required_delivery_time}")
    print()

    print(f"Candidate routes discovered: {len(routes)}")
    print()

    for route in routes:
        print("-" * 72)
        print("Route ID:", route.route_id)
        print("Rail:", route.rail)
        print(
            "Source:",
            route.source.country,
            route.source.currency,
        )
        print(
            "Destination:",
            route.destination.country,
            route.destination.currency,
        )
        print("Funding:", route.funding_method)
        print("Transfer path:", " -> ".join(route.transfer_path))
        print("Delivery:", route.delivery_method)
        print("Availability:", route.corridor_availability)
        print("Requirements:", route.route_requirements)

    print()
    print("=" * 72)
    print("REAL AI ROUTE DISCOVERY TEST: PASS")
    print("=" * 72)


if __name__ == "__main__":
    main()
