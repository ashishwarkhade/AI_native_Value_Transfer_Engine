from intent.value_transfer_intent import create_india_brazil_intent
from route_discovery.route_discovery import discover_routes


def main():
    intent = create_india_brazil_intent()

    print("\n=== VALUE TRANSFER INTENT ===")
    print(intent)

    routes = discover_routes(intent)

    print("\n=== CANDIDATE ROUTES ===")

    for route in routes:
        print(f"\nRoute ID: {route.route_id}")
        print(f"Rail: {route.rail}")
        print(f"Source: {route.source}")
        print(f"Destination: {route.destination}")
        print(f"Funding: {route.funding_method}")
        print(f"Path: {' -> '.join(route.transfer_path)}")
        print(f"Delivery: {route.delivery_method}")
        print(f"Availability: {route.corridor_availability}")

    # First vertical pass currently contains one real,
    # provider-backed India -> Brazil route.
    assert len(routes) == 1

    route = routes[0]

    assert route.route_id == "R-IN-BR-WISE-001"
    assert route.rail == "BANKING"
    assert route.source.country == "India"
    assert route.source.currency == "INR"
    assert route.destination.country == "Brazil"
    assert route.destination.currency == "BRL"
    assert route.corridor_availability == "CORRIDOR_VERIFIED"

    print("\nPASS: Intent -> Route Discovery")


if __name__ == "__main__":
    main()
