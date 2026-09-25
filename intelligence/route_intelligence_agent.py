import json
from typing import Any, Dict, List, Optional

from ai.model_interface import AIModel, build_structured_context
from intelligence.intelligence_models import (
    AvailabilityIntelligence,
    Evidence,
    FeeIntelligence,
    FXIntelligence,
    PaymentOptionIntelligence,
    RouteIntelligence,
    SettlementIntelligence,
)
from models.contracts import CandidateRoute, ValueTransferIntent


SYSTEM_PROMPT = """
You are the Route Intelligence Agent of a Value Transfer Engine.

Your responsibility is to INVESTIGATE a candidate value-transfer
route and normalize the available intelligence about that route.

You are NOT the route discovery agent.

You receive:
- the user's value-transfer intent
- one candidate route
- available evidence and observations

You must investigate and reason about:

- route/provider availability
- funding / pay-in capability
- delivery / pay-out capability
- payment options
- FX information
- transfer fees
- taxes
- other identifiable costs
- settlement / delivery timing
- route requirements
- evidence provenance

IMPORTANT:

1. A candidate route is NOT automatically available.
2. A plausible provider capability is NOT automatically a verified fact.
3. Do not invent prices, FX rates, fees, taxes, delivery times,
   provider capabilities, regulatory facts, or payment options.
4. If required information is not established by the supplied
   evidence, represent it as UNKNOWN or INCOMPLETE.
5. Preserve evidence provenance.
6. Evidence must correspond to evidence supplied in the investigation
   context. Do not create new external evidence records.
7. Candidate-route fields and user-intent fields are context, not
   external evidence.
8. Distinguish observed facts from derived calculations.
9. Do not evaluate legal compliance.
10. Do not determine final route eligibility.
11. Do not recommend a route.
12. Do not assume any particular provider or payment rail.

Your output must contain normalized route intelligence.

Use these status values where applicable:

KNOWN
UNKNOWN
NOT_APPLICABLE

For overall data completeness use:

COMPLETE
INCOMPLETE

Return ONLY valid JSON using this structure:

{
  "availability": {
    "status": "KNOWN|UNKNOWN|NOT_APPLICABLE",
    "provider": null,
    "source_country": null,
    "destination_country": null,
    "source_currency": null,
    "destination_currency": null,
    "funding_method": null,
    "delivery_method": null,
    "explanation": ""
  },
  "fx": {
    "status": "KNOWN|UNKNOWN|NOT_APPLICABLE",
    "reference_rate": null,
    "reference_rate_source": null,
    "reference_rate_type": null,
    "execution_rate": null,
    "execution_rate_source": null,
    "base_currency": null,
    "quote_currency": null,
    "explanation": ""
  },
  "fees": {
    "status": "KNOWN|UNKNOWN|NOT_APPLICABLE",
    "transfer_fee": null,
    "tax": null,
    "fx_spread": null,
    "network_fee": null,
    "other_fee": null,
    "currency": null,
    "published_example_amount": null,
    "published_example_fee": null,
    "published_example_currency": null,
    "explanation": ""
  },
  "settlement": {
    "status": "KNOWN|UNKNOWN|NOT_APPLICABLE",
    "estimated_delivery_time": null,
    "settlement_method": null,
    "explanation": ""
  },
  "payment_options": [
    {
      "pay_in": null,
      "pay_out": null,
      "enabled": false,
      "disabled_reason_code": null,
      "disabled_reason_message": null,
      "source_amount": null,
      "target_amount": null,
      "execution_rate": null,
      "transfer_fee": null,
      "tax": null,
      "total_fee": null,
      "fee_currency": null,
      "estimated_delivery": null,
      "formatted_estimated_delivery": null,
      "fee_percentage": null,
      "explanation": ""
    }
  ],
  "data_completeness": "COMPLETE|INCOMPLETE",
  "evidence": []
}
"""


def build_route_intelligence_context(
    intent: ValueTransferIntent,
    route: CandidateRoute,
    evidence: Optional[List[Evidence]] = None,
) -> Dict[str, Any]:
    """
    Build structured investigation context.

    Evidence is supplied to the agent rather than embedded into the
    architecture as a provider-specific assumption.
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
        "available_evidence": [
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


class RouteIntelligenceAgent:
    """
    Provider-neutral AI Route Intelligence Agent.

    The agent investigates one candidate route at a time.

    The AI model is injected through AIModel so the intelligence
    architecture is independent of a particular model provider.
    """

    def __init__(self, model: AIModel):
        self.model = model

    def investigate(
        self,
        intent: ValueTransferIntent,
        route: CandidateRoute,
        evidence: Optional[List[Evidence]] = None,
    ) -> RouteIntelligence:
        """
        Investigate and normalize intelligence for one candidate route.
        """

        supplied_evidence = list(evidence or [])

        context = build_route_intelligence_context(
            intent=intent,
            route=route,
            evidence=supplied_evidence,
        )

        user_prompt = (
            "Investigate the following candidate route.\n\n"
            "Use only the supplied evidence and observations. "
            "Do not invent missing information.\n\n"
            "Candidate-route fields and intent fields provide context "
            "but are not external evidence.\n\n"
            "If no evidence is supplied, do not create evidence records. "
            "Return an empty evidence array.\n\n"
            "The result is route intelligence only. "
            "Do not determine compliance, eligibility, "
            "or recommendation.\n\n"
            "Structured investigation context:\n"
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
        Normalize harmless presentation wrappers around a JSON response.

        Models may return valid JSON inside a Markdown code fence:

            ```json
            {...}
            ```

        The VTE contract remains JSON. This method only removes the
        surrounding presentation wrapper before JSON parsing.
        """

        if not isinstance(response, str):
            raise ValueError(
                "Route Intelligence Agent response must be a string."
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
    ) -> RouteIntelligence:
        """
        Convert the AI response into the RouteIntelligence contract.

        Evidence provenance is controlled by the supplied investigation
        evidence. The AI response cannot manufacture new provenance.
        """

        normalized_response = RouteIntelligenceAgent._normalize_json_response(
            response
        )

        try:
            data = json.loads(normalized_response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Route Intelligence Agent returned invalid JSON."
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "Route Intelligence Agent response must be a JSON object."
            )

        availability = data.get("availability")
        fx = data.get("fx")
        fees = data.get("fees")
        settlement = data.get("settlement")
        payment_options = data.get("payment_options")
        data_completeness = data.get("data_completeness")

        if not isinstance(availability, dict):
            raise ValueError(
                "Route Intelligence Agent 'availability' must be an object."
            )

        if not isinstance(fx, dict):
            raise ValueError(
                "Route Intelligence Agent 'fx' must be an object."
            )

        if not isinstance(fees, dict):
            raise ValueError(
                "Route Intelligence Agent 'fees' must be an object."
            )

        if not isinstance(settlement, dict):
            raise ValueError(
                "Route Intelligence Agent 'settlement' must be an object."
            )

        if not isinstance(payment_options, list):
            raise ValueError(
                "Route Intelligence Agent 'payment_options' must be a list."
            )

        if data_completeness not in {"COMPLETE", "INCOMPLETE"}:
            raise ValueError(
                "Route Intelligence Agent 'data_completeness' must be "
                "'COMPLETE' or 'INCOMPLETE'."
            )

        parsed_payment_options: List[PaymentOptionIntelligence] = []

        for index, item in enumerate(payment_options, start=1):
            if not isinstance(item, dict):
                raise ValueError(
                    f"Payment option {index} must be a JSON object."
                )

            parsed_payment_options.append(
                PaymentOptionIntelligence(
                    pay_in=item.get("pay_in"),
                    pay_out=item.get("pay_out"),
                    enabled=bool(item.get("enabled", False)),
                    disabled_reason_code=item.get("disabled_reason_code"),
                    disabled_reason_message=item.get(
                        "disabled_reason_message"
                    ),
                    source_amount=_optional_float(
                        item.get("source_amount")
                    ),
                    target_amount=_optional_float(
                        item.get("target_amount")
                    ),
                    execution_rate=_optional_float(
                        item.get("execution_rate")
                    ),
                    transfer_fee=_optional_float(
                        item.get("transfer_fee")
                    ),
                    tax=_optional_float(item.get("tax")),
                    total_fee=_optional_float(item.get("total_fee")),
                    fee_currency=item.get("fee_currency"),
                    estimated_delivery=item.get("estimated_delivery"),
                    formatted_estimated_delivery=item.get(
                        "formatted_estimated_delivery"
                    ),
                    fee_percentage=_optional_float(
                        item.get("fee_percentage")
                    ),
                    explanation=str(item.get("explanation", "")),
                )
            )

        parsed_evidence = list(supplied_evidence or [])

        return RouteIntelligence(
            route_id=route.route_id,
            availability=AvailabilityIntelligence(
                status=str(availability.get("status")),
                provider=availability.get("provider"),
                source_country=availability.get("source_country"),
                destination_country=availability.get(
                    "destination_country"
                ),
                source_currency=availability.get("source_currency"),
                destination_currency=availability.get(
                    "destination_currency"
                ),
                funding_method=availability.get("funding_method"),
                delivery_method=availability.get("delivery_method"),
                explanation=str(
                    availability.get("explanation", "")
                ),
            ),
            fx=FXIntelligence(
                status=str(fx.get("status")),
                reference_rate=_optional_float(
                    fx.get("reference_rate")
                ),
                reference_rate_source=fx.get(
                    "reference_rate_source"
                ),
                reference_rate_type=fx.get(
                    "reference_rate_type"
                ),
                execution_rate=_optional_float(
                    fx.get("execution_rate")
                ),
                execution_rate_source=fx.get(
                    "execution_rate_source"
                ),
                base_currency=fx.get("base_currency"),
                quote_currency=fx.get("quote_currency"),
                explanation=str(fx.get("explanation", "")),
            ),
            fees=FeeIntelligence(
                status=str(fees.get("status")),
                transfer_fee=_optional_float(
                    fees.get("transfer_fee")
                ),
                tax=_optional_float(fees.get("tax")),
                fx_spread=_optional_float(
                    fees.get("fx_spread")
                ),
                network_fee=_optional_float(
                    fees.get("network_fee")
                ),
                other_fee=_optional_float(
                    fees.get("other_fee")
                ),
                currency=fees.get("currency"),
                published_example_amount=_optional_float(
                    fees.get("published_example_amount")
                ),
                published_example_fee=_optional_float(
                    fees.get("published_example_fee")
                ),
                published_example_currency=fees.get(
                    "published_example_currency"
                ),
                explanation=str(fees.get("explanation", "")),
            ),
            settlement=SettlementIntelligence(
                status=str(settlement.get("status")),
                estimated_delivery_time=settlement.get(
                    "estimated_delivery_time"
                ),
                settlement_method=settlement.get(
                    "settlement_method"
                ),
                explanation=str(
                    settlement.get("explanation", "")
                ),
            ),
            data_completeness=data_completeness,
            payment_options=parsed_payment_options,
            evidence=parsed_evidence,
        )


def _optional_float(value: Any) -> Optional[float]:
    """
    Convert numeric values to float while preserving unknown/null values.

    This also tolerates models returning numeric values as JSON strings,
    while rejecting arbitrary non-numeric text.
    """

    if value is None:
        return None

    if isinstance(value, bool):
        raise ValueError(
            "Numeric Route Intelligence field cannot be boolean."
        )

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid numeric Route Intelligence value: {value!r}"
        ) from exc
