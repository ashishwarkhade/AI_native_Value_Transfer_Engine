import json
from typing import Any, Dict

from ai.model_interface import AIModel, build_structured_context
from compliance.compliance_models import ComplianceDecision
from eligibility.eligibility_models import EligibilityDecision
from intelligence.intelligence_models import RouteIntelligence
from models.contracts import CandidateRoute, ValueTransferIntent


SYSTEM_PROMPT = """
You are the AI Eligibility Agent of a Value Transfer Engine.

Your responsibility is to determine whether ONE candidate route is
currently eligible for the user's stated value-transfer intent.

The previous stages have already produced:

1. Value Transfer Intent
2. Candidate Route
3. AI Route Intelligence
4. AI Compliance Evaluation

You must reason from those outputs.

You are the FINAL eligibility decision agent for the individual route.

You must NOT:
- discover routes
- investigate new routes
- invent missing facts
- invent regulatory permissions
- override an explicit compliance failure
- treat a candidate route as verified merely because it was discovered
- treat incomplete intelligence as complete
- treat a disabled payment option as enabled
- recommend a route
- compare this route with other routes
- optimize between routes
- select the best route

IMPORTANT DISTINCTION:

Candidate Route
    !=
Verified Intelligence
    !=
Compliance
    !=
Eligibility
    !=
Recommendation

Possible status values are exactly:

ELIGIBLE
INELIGIBLE
DATA_INCOMPLETE

DECISION PRINCIPLES:

1. If AI Compliance status is INELIGIBLE:
       Eligibility must be INELIGIBLE.

2. If AI Compliance status is DATA_INCOMPLETE:
       Eligibility must not be ELIGIBLE unless the supplied
       information independently establishes that the unresolved
       compliance information is irrelevant to this route.
       Otherwise return DATA_INCOMPLETE.

3. If required route intelligence is missing or incomplete:
       return DATA_INCOMPLETE unless the missing information is
       demonstrably irrelevant to determining whether the route
       can currently be used.

4. If the route has provider payment options and all relevant
   options are disabled:
       return INELIGIBLE when the evidence establishes that no
       currently usable option exists.

5. Do not infer that a route is operationally usable from the
   existence of a provider or payment rail alone.

6. ELIGIBLE means the supplied evidence establishes that the route
   can currently be used for the stated intent.

7. If information needed to distinguish ELIGIBLE from INELIGIBLE
   is genuinely missing:
       return DATA_INCOMPLETE.

8. Preserve evidence IDs supporting the decision.

The output is a route-level eligibility decision only.

Return ONLY valid JSON:

{
  "status": "ELIGIBLE | INELIGIBLE | DATA_INCOMPLETE",
  "reasons": [
    "reason 1",
    "reason 2"
  ],
  "missing_information": [
    "item 1"
  ],
  "evidence_ids": [
    "evidence-id-1"
  ]
}
"""


def _payment_option_to_dict(
    option,
) -> Dict[str, Any]:
    """
    Convert payment-option intelligence into structured data.
    """

    return {
        "pay_in": option.pay_in,
        "pay_out": option.pay_out,
        "enabled": option.enabled,
        "disabled_reason_code": (
            option.disabled_reason_code
        ),
        "disabled_reason_message": (
            option.disabled_reason_message
        ),
        "source_amount": option.source_amount,
        "target_amount": option.target_amount,
        "execution_rate": option.execution_rate,
        "transfer_fee": option.transfer_fee,
        "tax": option.tax,
        "total_fee": option.total_fee,
        "fee_currency": option.fee_currency,
        "estimated_delivery": option.estimated_delivery,
        "formatted_estimated_delivery": (
            option.formatted_estimated_delivery
        ),
        "fee_percentage": option.fee_percentage,
        "explanation": option.explanation,
    }


def _rule_result_to_dict(
    rule_result,
) -> Dict[str, Any]:
    """
    Convert an AI compliance finding into structured data.
    """

    return {
        "rule_id": rule_result.rule_id,
        "jurisdiction": rule_result.jurisdiction,
        "status": rule_result.status,
        "explanation": rule_result.explanation,
    }


def build_eligibility_context(
    intent: ValueTransferIntent,
    route: CandidateRoute,
    compliance: ComplianceDecision,
    intelligence: RouteIntelligence,
) -> Dict[str, Any]:
    """
    Build structured context for AI eligibility reasoning.

    No eligibility decision is made here.
    """

    return {
        "intent": {
            "intent_id": intent.intent_id,
            "from_country": intent.from_country,
            "to_country": intent.to_country,
            "amount": intent.amount,
            "source_currency": intent.source_currency,
            "destination_currency": intent.destination_currency,
            "required_delivery_time": (
                intent.required_delivery_time
            ),
        },

        "candidate_route": {
            "route_id": route.route_id,
            "rail": route.rail,
            "source": {
                "country": route.source.country,
                "currency": route.source.currency,
            },
            "destination": {
                "country": route.destination.country,
                "currency": route.destination.currency,
            },
            "funding_method": route.funding_method,
            "transfer_path": route.transfer_path,
            "delivery_method": route.delivery_method,
            "corridor_availability": (
                route.corridor_availability
            ),
            "route_requirements": (
                route.route_requirements
            ),
        },

        "ai_compliance": {
            "route_id": compliance.route_id,
            "status": compliance.status,
            "rule_results": [
                _rule_result_to_dict(result)
                for result in compliance.rule_results
            ],
            "missing_information": (
                compliance.missing_information
            ),
            "evidence": compliance.evidence,
        },

        "ai_route_intelligence": {
            "route_id": intelligence.route_id,
            "data_completeness": (
                intelligence.data_completeness
            ),

            "availability": {
                "status": (
                    intelligence.availability.status
                ),
                "provider": (
                    intelligence.availability.provider
                ),
                "source_country": (
                    intelligence
                    .availability
                    .source_country
                ),
                "destination_country": (
                    intelligence
                    .availability
                    .destination_country
                ),
                "source_currency": (
                    intelligence
                    .availability
                    .source_currency
                ),
                "destination_currency": (
                    intelligence
                    .availability
                    .destination_currency
                ),
                "funding_method": (
                    intelligence
                    .availability
                    .funding_method
                ),
                "delivery_method": (
                    intelligence
                    .availability
                    .delivery_method
                ),
                "explanation": (
                    intelligence
                    .availability
                    .explanation
                ),
            },

            "fx": {
                "status": intelligence.fx.status,
                "reference_rate": (
                    intelligence.fx.reference_rate
                ),
                "reference_rate_source": (
                    intelligence
                    .fx
                    .reference_rate_source
                ),
                "reference_rate_type": (
                    intelligence
                    .fx
                    .reference_rate_type
                ),
                "execution_rate": (
                    intelligence.fx.execution_rate
                ),
                "execution_rate_source": (
                    intelligence
                    .fx
                    .execution_rate_source
                ),
                "base_currency": (
                    intelligence.fx.base_currency
                ),
                "quote_currency": (
                    intelligence.fx.quote_currency
                ),
                "explanation": (
                    intelligence.fx.explanation
                ),
            },

            "fees": {
                "status": intelligence.fees.status,
                "transfer_fee": (
                    intelligence.fees.transfer_fee
                ),
                "tax": intelligence.fees.tax,
                "fx_spread": (
                    intelligence.fees.fx_spread
                ),
                "network_fee": (
                    intelligence.fees.network_fee
                ),
                "other_fee": (
                    intelligence.fees.other_fee
                ),
                "currency": (
                    intelligence.fees.currency
                ),
                "published_example_amount": (
                    intelligence
                    .fees
                    .published_example_amount
                ),
                "published_example_fee": (
                    intelligence
                    .fees
                    .published_example_fee
                ),
                "published_example_currency": (
                    intelligence
                    .fees
                    .published_example_currency
                ),
                "explanation": (
                    intelligence
                    .fees
                    .explanation
                ),
            },

            "settlement": {
                "status": (
                    intelligence
                    .settlement
                    .status
                ),
                "estimated_delivery_time": (
                    intelligence
                    .settlement
                    .estimated_delivery_time
                ),
                "settlement_method": (
                    intelligence
                    .settlement
                    .settlement_method
                ),
                "explanation": (
                    intelligence
                    .settlement
                    .explanation
                ),
            },

            "payment_options": [
                _payment_option_to_dict(option)
                for option in intelligence.payment_options
            ],

            "evidence": [
                {
                    "evidence_id": evidence.evidence_id,
                    "source_name": evidence.source_name,
                    "source_type": evidence.source_type,
                    "source_url": evidence.source_url,
                    "observation": evidence.observation,
                    "jurisdiction": evidence.jurisdiction,
                    "observed_at": evidence.observed_at,
                }
                for evidence in intelligence.evidence
            ],
        },
    }


class EligibilityAgent:
    """
    AI-led Eligibility Agent.

    This class contains no deterministic eligibility rules.

    The AI model receives the outputs of:
      - Route Discovery
      - Route Intelligence
      - AI Compliance

    and determines the eligibility state for one route.
    """

    def __init__(self, model: AIModel):
        self.model = model

    def evaluate(
        self,
        intent: ValueTransferIntent,
        route: CandidateRoute,
        compliance: ComplianceDecision,
        intelligence: RouteIntelligence,
    ) -> EligibilityDecision:
        """
        Ask the AI model to determine route eligibility.
        """

        context = build_eligibility_context(
            intent=intent,
            route=route,
            compliance=compliance,
            intelligence=intelligence,
        )

        user_prompt = (
            "Determine the current eligibility of this "
            "candidate route.\n\n"
            "The route has already been discovered.\n"
            "Route intelligence has already been investigated.\n"
            "Compliance has already been evaluated by the "
            "AI Compliance Agent.\n\n"
            "Do not discover or recommend routes.\n"
            "Do not invent missing information.\n\n"
            "Structured eligibility context:\n"
            f"{build_structured_context(context)}"
        )

        response = self.model.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        return self._parse_response(
            route_id=route.route_id,
            response=response,
        )

    @staticmethod
    def _parse_response(
        route_id: str,
        response: str,
    ) -> EligibilityDecision:
        """
        Convert the AI response into EligibilityDecision.
        """

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "AI Eligibility Agent returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "AI Eligibility Agent response must be "
                "a JSON object."
            )

        status = data.get("status")

        if status not in {
            "ELIGIBLE",
            "INELIGIBLE",
            "DATA_INCOMPLETE",
        }:
            raise ValueError(
                "AI Eligibility Agent returned invalid status: "
                f"{status!r}"
            )

        reasons = data.get("reasons", [])
        missing_information = data.get(
            "missing_information",
            [],
        )
        evidence_ids = data.get(
            "evidence_ids",
            [],
        )

        if not isinstance(reasons, list):
            raise ValueError(
                "AI Eligibility Agent 'reasons' "
                "must be a list."
            )

        if not isinstance(
            missing_information,
            list,
        ):
            raise ValueError(
                "AI Eligibility Agent "
                "'missing_information' must be a list."
            )

        if not isinstance(evidence_ids, list):
            raise ValueError(
                "AI Eligibility Agent 'evidence_ids' "
                "must be a list."
            )

        return EligibilityDecision(
            route_id=route_id,
            status=status,
            reasons=[
                str(item)
                for item in reasons
            ],
            missing_information=[
                str(item)
                for item in missing_information
            ],
            evidence_ids=[
                str(item)
                for item in evidence_ids
            ],
        )
