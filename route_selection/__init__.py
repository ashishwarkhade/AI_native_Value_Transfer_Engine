from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class RouteSelectionDecision:
    """
    Output of the AI Route Selection stage.

    This model records what the AI selected and the reasoning/evidence
    associated with that selection.

    The selection stage does not define the meaning of eligibility or
    compliance. Those are outputs supplied by preceding AI stages.
    """

    status: str
    selected_route_id: Optional[str] = None
    considered_route_ids: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)