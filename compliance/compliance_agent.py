import json
from typing import Any, Dict, List, Optional

from ai.model_interface import AIModel, build_structured_context
from compliance.compliance_models import (
    ComplianceContext,
    ComplianceDecision,
    RuleResult,
)
from intelligence.intelligence_models import (
    Evidence,
    RouteIntelligence,
)
from models.contracts import CandidateRoute, ValueTransferIntent


SYSTEM_PROMPT = """
You are the AI Compliance Agent of a Value Transfer Engine.

Your responsibility is to evaluate the COMPLIANCE of a candidate
value-transfer route using applicable regulatory and compliance
evidence.

You are an AI compliance reasoning agent.

You are NOT:
- a route discovery agent
- a route intelligence agent
- an eligibility agent
- a route selection agent
- a recommendation agent

You must independently reason about the compliance context supplied
to you.

Your responsibilities include:

1. Identify the relevant jurisdictions.
2. Identify the regulatory/compliance requirements applicable to
   the transaction and route.
3. Evaluate the available evidence against those requirements.
4. Identify hard compliance failures.
5. Identify information that is required but not established.
6. Preserve evidence provenance.
7. Produce a structured compliance decision.

IMPORTANT PRINCIPLES:

- Never invent a law, regulation, regulatory threshold, license,
  authorization, requirement, exemption, or prohibition.
- Never treat a plausible assumption as regulatory fact.
- Never assume a provider is authorized merely because the route
  contains that provider.
- Never assume a payment rail is legally available merely because
  the technology exists.
- Never infer compliance from route availability.
- Never infer eligibility from compliance.
- Never recommend a route.
- Never select a route.
- Do not calculate commercial optimization.

Use only the supplied regulatory/compliance evidence and context.

If the evidence establishes a compliance failure:
    status = INELIGIBLE

If compliance cannot yet be established because required evidence or
information is missing:
    status = DATA_INCOMPLETE

If the supplied evidence establishes that the route satisfies the
applicable compliance requirements:
    status = ELIGIBLE

Every individual finding must identify the applicable jurisdiction
and explain the reasoning.

Preserve evidence IDs whenever evidence supports a finding.

Evidence IDs must refer only to evidence supplied in the
regulatory_and_compliance_evidence context.

If no regulatory/compliance evidence is supplied, return:
    "evidence": []

Do not create evidence records or evidence IDs yourself.

Return ONLY valid JSON:

{
  "status": "ELIGIBLE|INELIGIBLE|DATA_INCOMPLETE",
  "rule_results": [
    {
      "rule_id": "unique-finding-id",
      "jurisdiction": "jurisdiction",
      "status": "PASS|FAIL|UNKNOWN",
      "explanation": "reasoning"
    }
  ],
  "missing_information": [
    "missing item"
  ],
  "evidence": [
    "evidence-id"
  ]
}
"""


def build_compliance_context(
    intent: ValueTransferIntent,
    route: CandidateRoute,
    route_intelligence: RouteIntelligence,
    compliance_context: ComplianceContext,
    evidence: Optional[List[Evidence]] = None,
) -> Dict[str, Any]:
    """
    Build structured context for AI compliance reasoning.

    This function only packages information. It does not evaluate
    compliance and contains no compliance decision rules.
    """

    return {
        "intent": {
            "intent_id": intent.intent_id,
            "from_country": intent.from_country,
            "to_country": intent.to_country,
            "amount": intent.amount,
            "source_currency": intent.source_currency,
            "destination_currency": intent.destination_currency,
            "required_delivery_time": intent.required_delivery_time,
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
            "corridor_availability": route.corridor_availability,
            "route_requirements": route.route_requirements,
        },
        "route_intelligence": {
            "route_id": route_intelligence.route_id,
            "data_completeness": (
                route_intelligence.data_completeness
            ),
            "availability": {
                "status": route_intelligence.availability.status,
                "provider": (
                    route_intelligence.availability.provider
                ),
                "funding_method": (
                    route_intelligence.availability.funding_method
                ),
                "delivery_method": (
                    route_intelligence.availability.delivery_method
                ),
            },
            "fx": {
                "status": route_intelligence.fx.status,
                "reference_rate": (
                    route_intelligence.fx.reference_rate
                ),
                "execution_rate": (
                    route_intelligence.fx.execution_rate
                ),
            },
            "fees": {
                "status": route_intelligence.fees.status,
                "transfer_fee": (
                    route_intelligence.fees.transfer_fee
                ),
                "tax": route_intelligence.fees.tax,
            },
            "settlement": {
                "status": (
                    route_intelligence.settlement.status
                ),
                "estimated_delivery_time": (
                    route_intelligence
                    .settlement
                    .estimated_delivery_time
                ),
                "settlement_method": (
                    route_intelligence
                    .settlement
                    .settlement_method
                ),
            },
        },
        "transaction_compliance_context": {
            "sender_type": compliance_context.sender_type,
            "sender_residency": (
                compliance_context.sender_residency
            ),
            "transfer_purpose": (
                compliance_context.transfer_purpose
            ),
            "recipient_type": compliance_context.recipient_type,
            "recipient_relationship": (
                compliance_context.recipient_relationship
            ),
            "sender_owns_destination_account": (
                compliance_context
                .sender_owns_destination_account
            ),
            "annual_lrs_used_usd": (
                compliance_context.annual_lrs_used_usd
            ),
            "estimated_transaction_usd": (
                compliance_context.estimated_transaction_usd
            ),
            "sender_pan_available": (
                compliance_context.sender_pan_available
            ),
            "sender_kyc_available": (
                compliance_context.sender_kyc_available
            ),
            "india_authorized_channel": (
                compliance_context.india_authorized_channel
            ),
            "brazil_authorized_channel": (
                compliance_context.brazil_authorized_channel
            ),
            "required_documentation_available": (
                compliance_context
                .required_documentation_available
            ),
        },
        "regulatory_and_compliance_evidence": [
            {
                "evidence_id": item.evidence_id,
                "source_name": item.source_name,
                "source_type": item.source_type,
                "source_url": item.source_url,
                "observation": item.observation,
                "jurisdiction": item.jurisdiction,
                "observed_at": item.observed_at,
            }
            for item in (evidence or [])
        ],
    }


class ComplianceAgent:
    """
    AI-led Compliance Agent.

    No compliance decision rules are executed here.

    The model receives:
      - transfer intent
      - candidate route
      - route intelligence
      - transaction context
      - regulatory/compliance evidence

    The model produces a ComplianceDecision.
    """

    def __init__(self, model: AIModel):
        self.model = model

    def evaluate(
        self,
        intent: ValueTransferIntent,
        route: CandidateRoute,
        route_intelligence: RouteIntelligence,
        compliance_context: ComplianceContext,
        evidence: Optional[List[Evidence]] = None,
    ) -> ComplianceDecision:
        """
        Ask the AI to evaluate compliance for one candidate route.
        """

        supplied_evidence = list(evidence or [])

        context = build_compliance_context(
            intent=intent,
            route=route,
            route_intelligence=route_intelligence,
            compliance_context=compliance_context,
            evidence=supplied_evidence,
        )

        user_prompt = (
            "Evaluate the compliance of this candidate route.\n\n"
            "Reason only from the supplied transaction context "
            "and regulatory/compliance evidence.\n\n"
            "Do not invent regulatory facts.\n"
            "Do not create evidence IDs.\n"
            "If no regulatory/compliance evidence is supplied, "
            "return an empty evidence list.\n"
            "Do not determine commercial eligibility.\n"
            "Do not recommend the route.\n\n"
            "Structured compliance context:\n"
            f"{build_structured_context(context)}"
        )

        response = self.model.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        return self._parse_response(
            route=route,
            response=response,
            supplied_evidence=supplied_evidence,
        )

    @staticmethod
    def _normalize_json_response(response: str) -> str:
        """
        Normalize harmless presentation wrappers around JSON.

        Models may return valid JSON inside a Markdown code fence.
        The VTE contract remains JSON.
        """

        if not isinstance(response, str):
            raise ValueError(
                "AI Compliance Agent response must be a string."
            )

        normalized = response.strip()

        if normalized.startswith("```") and normalized.endswith("```"):
            lines = normalized.splitlines()

            if len(lines) >= 3:
                first_line = lines[0].strip().lower()

                if first_line in {"```", "```json"}:
                    normalized = "\n".join(lines[1:-1]).strip()

        return normalized

    @staticmethod
    def _parse_response(
        route: CandidateRoute,
        response: str,
        supplied_evidence: Optional[List[Evidence]] = None,
    ) -> ComplianceDecision:
        """
        Convert AI JSON into the ComplianceDecision contract.

        Evidence provenance is restricted to evidence supplied to the
        Compliance Agent.
        """

        normalized_response = ComplianceAgent._normalize_json_response(
            response
        )

        try:
            data = json.loads(normalized_response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "AI Compliance Agent returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "AI Compliance Agent response must be a JSON object."
            )

        status = str(data.get("status", ""))

        if status not in {
            "ELIGIBLE",
            "INELIGIBLE",
            "DATA_INCOMPLETE",
        }:
            raise ValueError(
                "AI Compliance Agent status must be "
                "ELIGIBLE, INELIGIBLE, or DATA_INCOMPLETE."
            )

        rule_results_data = data.get("rule_results", [])

        if not isinstance(rule_results_data, list):
            raise ValueError(
                "AI Compliance Agent 'rule_results' "
                "must be a list."
            )

        missing_information = data.get(
            "missing_information",
            [],
        )

        if not isinstance(missing_information, list):
            raise ValueError(
                "AI Compliance Agent 'missing_information' "
                "must be a list."
            )

        evidence_ids = data.get("evidence", [])

        if not isinstance(evidence_ids, list):
            raise ValueError(
                "AI Compliance Agent 'evidence' "
                "must be a list."
            )

        supplied_evidence_ids = {
            item.evidence_id
            for item in (supplied_evidence or [])
        }

        invalid_evidence_ids = [
            str(item)
            for item in evidence_ids
            if str(item) not in supplied_evidence_ids
        ]

        if invalid_evidence_ids:
            raise ValueError(
                "AI Compliance Agent returned evidence IDs that were "
                "not supplied to the agent: "
                f"{invalid_evidence_ids}"
            )

        rule_results: List[RuleResult] = []

        for index, item in enumerate(
            rule_results_data,
            start=1,
        ):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Compliance finding {index} "
                    "must be a JSON object."
                )

            required_fields = [
                "rule_id",
                "jurisdiction",
                "status",
                "explanation",
            ]

            missing = [
                field
                for field in required_fields
                if field not in item
            ]

            if missing:
                raise ValueError(
                    f"Compliance finding {index} "
                    f"is missing required fields: {missing}"
                )

            finding_status = str(item["status"])

            if finding_status not in {
                "PASS",
                "FAIL",
                "UNKNOWN",
            }:
                raise ValueError(
                    f"Compliance finding {index} has invalid "
                    f"status: {finding_status}"
                )

            rule_results.append(
                RuleResult(
                    rule_id=str(item["rule_id"]),
                    jurisdiction=str(
                        item["jurisdiction"]
                    ),
                    status=finding_status,
                    explanation=str(
                        item["explanation"]
                    ),
                )
            )

        return ComplianceDecision(
            route_id=route.route_id,
            status=status,
            rule_results=rule_results,
            missing_information=[
                str(item)
                for item in missing_information
            ],
            evidence=[
                str(item)
                for item in evidence_ids
            ],
        )
