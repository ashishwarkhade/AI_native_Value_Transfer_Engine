from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ValueTransferIntent:
    """
    What the user wants to accomplish.

    The intent describes the value-transfer requirement.
    It does not prescribe how the transfer should happen.
    """

    intent_id: str
    from_country: str
    to_country: str
    amount: float
    source_currency: str
    destination_currency: str
    required_delivery_time: str


@dataclass(frozen=True)
class RouteEndpoint:
    country: str
    currency: str


@dataclass(frozen=True)
class CandidateRoute:
    """
    A possible value-transfer path discovered by Route Discovery.

    A candidate route is NOT yet:
      - compliant
      - eligible
      - optimized
      - recommended

    Those decisions belong to later stages of the engine.
    """

    route_id: str
    rail: str
    source: RouteEndpoint
    destination: RouteEndpoint
    funding_method: str
    transfer_path: List[str]
    delivery_method: str
    corridor_availability: str
    route_requirements: List[str] = field(default_factory=list)
