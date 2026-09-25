from typing import List

from models.contracts import CandidateRoute, RouteEndpoint, ValueTransferIntent


def discover_routes(intent: ValueTransferIntent) -> List[CandidateRoute]:
    """
    Discover candidate routes for the value-transfer intent.

    Discovery identifies possible mechanisms.
    It does not determine final eligibility or recommendation.
    """

    if (
        intent.from_country != "India"
        or intent.to_country != "Brazil"
    ):
        return []

    source = RouteEndpoint(
        country=intent.from_country,
        currency=intent.source_currency,
    )

    destination = RouteEndpoint(
        country=intent.to_country,
        currency=intent.destination_currency,
    )

    return [
        CandidateRoute(
            route_id="R-IN-BR-WISE-001",
            rail="BANKING",
            source=source,
            destination=destination,
            funding_method="PERSONAL_INDIAN_BANK_ACCOUNT_OR_UPI",
            transfer_path=[
                "INR",
                "INDIA_BANK_ACCOUNT_OR_UPI",
                "WISE",
                "FX",
                "BRAZIL_LOCAL_BANKING",
                "BRL",
            ],
            delivery_method="BRAZIL_LOCAL_BANK_ACCOUNT",
            corridor_availability="CORRIDOR_VERIFIED",
            route_requirements=[
                "INDIAN_TAX_RESIDENT",
                "INDIAN_PAN",
                "AADHAAR_VERIFICATION",
                "VIDEO_VERIFICATION",
                "PERSONAL_INDIAN_BANK_ACCOUNT_OR_UPI",
                "RECIPIENT_BRAZIL_BANK_DETAILS",
            ],
        ),
    ]
