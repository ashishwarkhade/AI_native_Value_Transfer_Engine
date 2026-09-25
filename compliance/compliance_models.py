from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ComplianceContext:
    """
    Facts required to evaluate a value-transfer route.

    These are not part of the core ValueTransferIntent.
    They are contextual facts required by the rules engine.
    """

    sender_type: str
    sender_residency: str
    transfer_purpose: str
    recipient_type: str
    recipient_relationship: str
    sender_owns_destination_account: bool

    annual_lrs_used_usd: float
    estimated_transaction_usd: float

    sender_pan_available: bool
    sender_kyc_available: bool

    india_authorized_channel: bool
    brazil_authorized_channel: bool

    required_documentation_available: bool


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    jurisdiction: str
    status: str
    explanation: str


@dataclass(frozen=True)
class ComplianceDecision:
    route_id: str
    status: str
    rule_results: List[RuleResult] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
