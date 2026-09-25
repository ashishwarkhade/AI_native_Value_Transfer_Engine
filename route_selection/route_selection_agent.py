import json
from typing import Dict, List

from ai.model_interface import AIModel, build_structured_context
from compliance.compliance_models import ComplianceDecision
from eligibility.eligibility_models import EligibilityDecision
from intelligence.intelligence_models import RouteIntelligence
from intent.value_transfer_intent import ValueTransferIntent
from models.contracts import CandidateRoute

from route_selection.route_selection_models import RouteSelectionDecision


class RouteSelectionAgent:
    """
    AI-led route selection stage.

    Receives the complete candidate-route universe together with the outputs
    produced by the preceding AI stages.

    This stage does not define compliance or eligibility and does not perform
    route discovery or route intelligence investigation.
    """

    def __init__(self, model: AIModel):
        self.model = model

    def select(
        self,
        intent: ValueTransferIntent,
        routes: List[CandidateRoute],
        intelligence: Dict[str, RouteIntelligence],
        compliance: Dict[str, ComplianceDecision],
        eligibility: Dict[str, EligibilityDecision],
    ) -> RouteSelectionDecision:

        route_ids = [route.route_id for route in routes]

        context = {
            "value_transfer_intent": intent,
            "candidate_routes": routes,
            "route_intelligence": intelligence,
            "compliance_decisions": compliance,
            "eligibility_decisions": eligibility,
        }

        system_prompt = (
            "You are the AI Route Selection component of a Value Transfer "
            "Engine.\n\n"
            "Your responsibility is route selection only.\n\n"
            "You receive the complete candidate route universe together with "
            "the outputs produced by preceding AI stages.\n\n"
            "Use those outputs as decision context. Do not redefine their "
            "meaning and do not introduce new compliance or eligibility "
            "criteria.\n\n"
            "Do not invent facts, prices, FX rates, fees, taxes, delivery "
            "times, provider capabilities, regulatory facts, or evidence.\n\n"
            "Do not perform new route discovery or route intelligence "
            "investigation.\n\n"
            "If the available information is insufficient to make a reliable "
            "selection, return DATA_INCOMPLETE.\n\n"
            "If the supplied route evaluations do not support selecting a "
            "route, return NO_SELECTION.\n\n"
            "Return JSON only."
        )

        user_prompt = (
            "Select the most appropriate route for the value-transfer "
            "intent using the complete route universe and all supplied "
            "preceding-stage outputs.\n\n"
            "Return exactly this JSON structure:\n"
            "{\n"
            '  "status": "SELECTED | NO_SELECTION | DATA_INCOMPLETE",\n'
            '  "selected_route_id": "route-id-or-null",\n'
            '  "considered_route_ids": ["route-id", "..."],\n'
            '  "reasons": ["reason", "..."],\n'
            '  "evidence_ids": ["evidence-id", "..."]\n'
            "}\n\n"
            "ROUTE SELECTION CONTEXT:\n"
            + build_structured_context(context)
        )

        raw_response = self.model.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return self._parse_response(raw_response, route_ids)

    @staticmethod
    def _parse_response(
        raw_response: str,
        available_route_ids: List[str],
    ) -> RouteSelectionDecision:

        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"AI route selection response is not valid JSON: {exc}"
            ) from exc

        status = data.get("status")
        selected_route_id = data.get("selected_route_id")
        considered_route_ids = data.get("considered_route_ids", [])
        reasons = data.get("reasons", [])
        evidence_ids = data.get("evidence_ids", [])

        if status not in {
            "SELECTED",
            "NO_SELECTION",
            "DATA_INCOMPLETE",
        }:
            raise ValueError(
                f"Invalid route selection status: {status!r}"
            )

        if not isinstance(considered_route_ids, list):
            raise ValueError("considered_route_ids must be a list")

        if not isinstance(reasons, list):
            raise ValueError("reasons must be a list")

        if not isinstance(evidence_ids, list):
            raise ValueError("evidence_ids must be a list")

        unknown_routes = [
            route_id
            for route_id in considered_route_ids
            if route_id not in available_route_ids
        ]

        if unknown_routes:
            raise ValueError(
                "AI referenced unknown route IDs: "
                f"{unknown_routes}"
            )

        if selected_route_id is not None:
            if selected_route_id not in available_route_ids:
                raise ValueError(
                    "AI selected an unknown route ID: "
                    f"{selected_route_id}"
                )

        if status == "SELECTED" and selected_route_id is None:
            raise ValueError(
                "SELECTED requires selected_route_id"
            )

        if status != "SELECTED" and selected_route_id is not None:
            raise ValueError(
                f"{status} must not contain selected_route_id"
            )

        return RouteSelectionDecision(
            status=status,
            selected_route_id=selected_route_id,
            considered_route_ids=considered_route_ids,
            reasons=reasons,
            evidence_ids=evidence_ids,
        )
