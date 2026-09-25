from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class RecommendationDecision:
    """
    Output of the AI Recommendation stage.

    The recommendation communicates the selected-route decision and its
    supporting reasoning to the user.

    This model does not perform route discovery, intelligence investigation,
    compliance evaluation, eligibility determination, or route selection.
    """

    status: str
    selected_route_id: Optional[str] = None
    recommendation: str = ""
    reasons: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
