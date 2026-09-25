from typing import List

from compliance.compliance_models import ComplianceDecision
from intelligence.intelligence_models import RouteIntelligence
from eligibility.eligibility_models import EligibilityDecision


def evaluate_eligibility(
    compliance: ComplianceDecision,
    intelligence: RouteIntelligence,
) -> EligibilityDecision:
    """
    Determine whether a candidate route is currently eligible.

    Eligibility is a deterministic gate.

    It does NOT:
      - select the best route
      - calculate optimization scores
      - make recommendations
      - invent missing data

    Important distinction:

      DATA_INCOMPLETE
          Required information is genuinely unavailable.

      INELIGIBLE
          The required information is known and shows that the
          route cannot currently be executed.
    """

    reasons: List[str] = []
    missing: List[str] = []

    # ------------------------------------------------------------
    # 1. HARD COMPLIANCE GATE
    # ------------------------------------------------------------

    if compliance.status == "INELIGIBLE":
        reasons.append(
            "At least one mandatory compliance rule failed."
        )

        return EligibilityDecision(
            route_id=compliance.route_id,
            status="INELIGIBLE",
            reasons=reasons,
            missing_information=compliance.missing_information,
            evidence_ids=[],
        )

    # Compliance data itself is incomplete.
    if compliance.status == "DATA_INCOMPLETE":
        missing.extend(compliance.missing_information)

    # ------------------------------------------------------------
    # 2. ROUTE AVAILABILITY
    # ------------------------------------------------------------

    if intelligence.availability.status == "UNKNOWN":
        missing.append("route availability")

    elif intelligence.availability.status == "KNOWN":
        # KNOWN at the corridor level is not sufficient.
        if not intelligence.availability.provider:
            missing.append("specific route provider")

        if not intelligence.availability.funding_method:
            missing.append("specific funding method")

        if not intelligence.availability.delivery_method:
            missing.append("specific delivery method")

    # ------------------------------------------------------------
    # 3. FX
    # ------------------------------------------------------------

    if intelligence.fx.status == "UNKNOWN":
        missing.append("transaction-specific FX rate")

    elif intelligence.fx.execution_rate is None:
        missing.append("transaction-specific FX execution rate")

    # ------------------------------------------------------------
    # 4. FEES
    # ------------------------------------------------------------

    if intelligence.fees.status == "UNKNOWN":
        missing.append("transaction-specific fees")

    elif intelligence.fees.transfer_fee is None:
        missing.append("transaction-specific transfer fee")

    # ------------------------------------------------------------
    # 5. SETTLEMENT
    # ------------------------------------------------------------

    if intelligence.settlement.status == "UNKNOWN":
        missing.append("transaction-specific settlement time")

    elif intelligence.settlement.estimated_delivery_time is None:
        missing.append("transaction-specific settlement estimate")

    # ------------------------------------------------------------
    # 6. DATA COMPLETENESS GATE
    # ------------------------------------------------------------

    # Remove duplicate missing fields while preserving order.
    missing = list(dict.fromkeys(missing))

    if missing:
        reasons.append(
            "The route cannot be considered eligible because "
            "required route-specific intelligence is incomplete."
        )

        return EligibilityDecision(
            route_id=compliance.route_id,
            status="DATA_INCOMPLETE",
            reasons=reasons,
            missing_information=missing,
            evidence_ids=[],
        )

    # ------------------------------------------------------------
    # 7. OPERATIONAL PAYMENT OPTION GATE
    # ------------------------------------------------------------

    # At least one provider payment option must actually be enabled.
    #
    # A quoted option with pricing is not enough. The option must
    # also be operationally available for this route/user context.

    if not intelligence.payment_options:
        reasons.append(
            "No provider payment option was returned for the route."
        )

        return EligibilityDecision(
            route_id=compliance.route_id,
            status="INELIGIBLE",
            reasons=reasons,
            missing_information=[],
            evidence_ids=[],
        )

    enabled_options = [
        option
        for option in intelligence.payment_options
        if option.enabled
    ]

    if not enabled_options:
        reasons.append(
            "No enabled provider payment option is currently "
            "available for this route."
        )

        for option in intelligence.payment_options:
            if option.disabled_reason_code:
                reasons.append(
                    f"{option.pay_in or 'UNKNOWN'} payment option disabled: "
                    f"{option.disabled_reason_code}"
                )
            elif option.disabled_reason_message:
                reasons.append(
                    f"{option.pay_in or 'UNKNOWN'} payment option disabled: "
                    f"{option.disabled_reason_message}"
                )

        return EligibilityDecision(
            route_id=compliance.route_id,
            status="INELIGIBLE",
            reasons=reasons,
            missing_information=[],
            evidence_ids=[],
        )

    # ------------------------------------------------------------
    # 8. ELIGIBLE
    # ------------------------------------------------------------

    reasons.append(
        "Compliance passed, required route intelligence is available, "
        "and at least one provider payment option is enabled."
    )

    return EligibilityDecision(
        route_id=compliance.route_id,
        status="ELIGIBLE",
        reasons=reasons,
        missing_information=[],
        evidence_ids=[],
    )