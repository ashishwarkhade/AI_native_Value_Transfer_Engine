from typing import Iterable, List

from models.contracts import CandidateRoute


def aggregate_candidate_routes(
    *route_sources: Iterable[CandidateRoute],
) -> List[CandidateRoute]:
    """
    Combine candidate routes produced by AI discovery sources.

    The aggregator is intentionally discovery-source neutral.

    Possible sources include:
      - multiple AI Route Discovery Agents
      - specialized AI discovery agents
      - future external discovery adapters

    The aggregator does NOT:
      - discover routes itself
      - assume any provider
      - seed any route
      - verify availability
      - evaluate intelligence
      - evaluate compliance
      - evaluate eligibility
      - optimize routes
      - recommend routes

    It only:
      1. combines discovered candidates
      2. removes duplicate route IDs
      3. preserves first-seen ordering
    """

    aggregated: List[CandidateRoute] = []
    seen_route_ids = set()

    for source in route_sources:
        for route in source:
            if route.route_id in seen_route_ids:
                continue

            seen_route_ids.add(route.route_id)
            aggregated.append(route)

    return aggregated