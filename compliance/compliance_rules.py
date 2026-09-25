from typing import List

from compliance.compliance_models import (
    ComplianceContext,
    ComplianceDecision,
    RuleResult,
)
from models.contracts import CandidateRoute


LRS_LIMIT_USD = 250000.0


def evaluate_route(
    route: CandidateRoute,
    context: ComplianceContext,
) -> ComplianceDecision:
    """
    Deterministic compliance evaluation for the first India -> Brazil pass.

    The rules engine does not optimize routes.
    It only determines whether the route can be considered eligible.
    """

    results: List[RuleResult] = []
    missing: List[str] = []

    # ------------------------------------------------------------
    # INDIA RULES
    # ------------------------------------------------------------

    if context.sender_type != "RESIDENT_INDIVIDUAL":
        results.append(
            RuleResult(
                rule_id="IN-LRS-001",
                jurisdiction="INDIA",
                status="INELIGIBLE",
                explanation=(
                    "The first-pass scenario is restricted to a resident "
                    "individual using the LRS framework."
                ),
            )
        )
    else:
        results.append(
            RuleResult(
                rule_id="IN-LRS-001",
                jurisdiction="INDIA",
                status="PASS",
                explanation="Sender is a resident individual.",
            )
        )

    if context.sender_residency != "INDIA":
        results.append(
            RuleResult(
                rule_id="IN-LRS-002",
                jurisdiction="INDIA",
                status="INELIGIBLE",
                explanation="Sender residency is not India.",
            )
        )
    else:
        results.append(
            RuleResult(
                rule_id="IN-LRS-002",
                jurisdiction="INDIA",
                status="PASS",
                explanation="Sender is resident in India.",
            )
        )

    if context.transfer_purpose not in {
        "PRIVATE_VISIT",
        "BUSINESS_TRAVEL",
        "EDUCATION",
        "MEDICAL",
        "EMPLOYMENT",
        "EMIGRATION",
        "GIFT",
        "DONATION",
        "PERMITTED_CAPITAL_ACCOUNT",
    }:
        results.append(
            RuleResult(
                rule_id="IN-LRS-003",
                jurisdiction="INDIA",
                status="INELIGIBLE",
                explanation="Transfer purpose is not recognized as a permitted first-pass purpose.",
            )
        )
    else:
        results.append(
            RuleResult(
                rule_id="IN-LRS-003",
                jurisdiction="INDIA",
                status="PASS",
                explanation="Transfer purpose is within the permitted LRS purpose set used by this engine.",
            )
        )

    total_lrs_usage = (
        context.annual_lrs_used_usd
        + context.estimated_transaction_usd
    )

    if total_lrs_usage > LRS_LIMIT_USD:
        results.append(
            RuleResult(
                rule_id="IN-LRS-004",
                jurisdiction="INDIA",
                status="INELIGIBLE",
                explanation=(
                    f"Estimated annual LRS usage of USD {total_lrs_usage:,.2f} "
                    f"exceeds the USD {LRS_LIMIT_USD:,.0f} limit."
                ),
            )
        )
    else:
        results.append(
            RuleResult(
                rule_id="IN-LRS-004",
                jurisdiction="INDIA",
                status="PASS",
                explanation=(
                    f"Estimated annual LRS usage of USD {total_lrs_usage:,.2f} "
                    f"is within the USD {LRS_LIMIT_USD:,.0f} limit."
                ),
            )
        )

    if not context.sender_pan_available:
        missing.append("sender PAN")

    if not context.sender_kyc_available:
        missing.append("sender KYC")

    if not context.india_authorized_channel:
        results.append(
            RuleResult(
                rule_id="IN-LRS-005",
                jurisdiction="INDIA",
                status="INELIGIBLE",
                explanation=(
                    "The proposed route does not identify an authorized "
                    "India-side foreign-exchange/remittance channel."
                ),
            )
        )
    else:
        results.append(
            RuleResult(
                rule_id="IN-LRS-005",
                jurisdiction="INDIA",
                status="PASS",
                explanation="India-side authorized channel is identified.",
            )
        )

    # ------------------------------------------------------------
    # BRAZIL RULES
    # ------------------------------------------------------------

    if not context.brazil_authorized_channel:
        results.append(
            RuleResult(
                rule_id="BR-FX-001",
                jurisdiction="BRAZIL",
                status="INELIGIBLE",
                explanation=(
                    "Brazil-side channel is not identified as an institution "
                    "authorized to operate in the foreign-exchange market."
                ),
            )
        )
    else:
        results.append(
            RuleResult(
                rule_id="BR-FX-001",
                jurisdiction="BRAZIL",
                status="PASS",
                explanation="Brazil-side authorized FX channel is identified.",
            )
        )

    if not context.sender_owns_destination_account:
        results.append(
            RuleResult(
                rule_id="BR-RECIPIENT-001",
                jurisdiction="BRAZIL",
                status="INELIGIBLE",
                explanation=(
                    "This first-pass scenario requires the destination account "
                    "to be owned or controlled by the sender."
                ),
            )
        )
    else:
        results.append(
            RuleResult(
                rule_id="BR-RECIPIENT-001",
                jurisdiction="BRAZIL",
                status="PASS",
                explanation="Destination account is owned or controlled by sender.",
            )
        )

    if not context.required_documentation_available:
        missing.append("required transfer documentation")

    # ------------------------------------------------------------
    # FINAL STATUS
    # ------------------------------------------------------------

    if any(r.status == "INELIGIBLE" for r in results):
        status = "INELIGIBLE"
    elif missing:
        status = "DATA_INCOMPLETE"
    else:
        status = "ELIGIBLE"

    return ComplianceDecision(
        route_id=route.route_id,
        status=status,
        rule_results=results,
        missing_information=missing,
        evidence=[
            "RBI Master Direction - Liberalised Remittance Scheme",
            "Banco Central do Brasil - foreign exchange/remittance guidance",
        ],
    )
