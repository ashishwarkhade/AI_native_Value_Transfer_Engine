from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class EligibilityDecision:
    route_id: str
    status: str
    reasons: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)
