import json
from typing import Dict, List

from ai.model_interface import AIModel, build_structured_context
from compliance.compliance_models import ComplianceDecision
from eligibility.eligibility_models import EligibilityDecision
from intelligence.intelligence_models import RouteIntelligence
from intent.value_transfer_intent import ValueTransferIntent
from models.contracts import CandidateRoute
from route_selection.route_selection_models import RouteSelectionDecision

from recommendation.recommendation_models import RecommendationDecision


class RecommendationAgent:
    """
    AI-led user recommendation stage.

    This stage communicates the result of the preceding AI decision process.

    It does not discover routes, investigate intelligence, evaluate
    compliance, determine eligibility, or select a route.
    """

    def __init__(self, model: AIModel):
        self.model = model

    def recommend(
        self,
        intent: ValueTransferIntent,
        routes: List[CandidateRoute],
        intelligence: Dict[str, RouteIntelligence],
        compliance: Dict[str, ComplianceDecision],
        eligibility: Dict[str, EligibilityDecision],
        selection: RouteSelectionDecision,
    ) -> RecommendationDecision:

        context = {
            "value_transfer_intent": intent,
            "candidate_routes": routes,
            "route_intelligence": intelligence,
            "compliance_decisions": compliance,
            "eligibility_decisions": eligibility,
            "route_selection": selection,
        }

        system_prompt = (
            "You are the AI Recommendation component of a Value Transfer "
            "Engine.\n\n"
            "Your responsibility is ONLY to communicate the result of the "
            "preceding AI route-selection process to the user.\n\n"
            "The route-selection decision has already been made. Do not "
            "select a different route.\n\n"
            "Use the supplied route selection, route intelligence, "
            "compliance outputs, eligibility outputs, intent, and evidence "
            "as the basis for the recommendation.\n\n"
            "Do not invent facts, prices, FX rates, fees, taxes, delivery "
            "times, provider capabilities, regulatory facts, or evidence.\n\n"
            "Clearly disclose material limitations or unresolved information "
            "when present.\n\n"
            "Do not perform new route discovery, intelligence investigation, "
            "compliance evaluation, eligibility determination, or route "
            "selection.\n\n"
            "Return JSON only."
        )

        user_prompt = (
            "Prepare a user-facing recommendation based on the supplied "
            "route-selection result.\n\n"
            "The recommendation must communicate the selected route, why "
            "the preceding AI decision selected it, supporting evidence, "
            "and material limitations.\n\n"
            "If the selection result does not contain a selected route, "
            "communicate that outcome rather than selecting another route.\n\n"
            "Return exactly this JSON structure:\n"
            "{\n"
            '  "status": "RECOMMEND | NO_RECOMMENDATION | DATA_INCOMPLETE",\n'
            '  "selected_route_id": "route-id-or-null",\n'
            '  "recommendation": "user-facing recommendation",\n'
            '  "reasons": ["reason", "..."],\n'
            '  "limitations": ["limitation", "..."],\n'
            '  "evidence_ids": ["evidence-id", "..."]\n'
            "}\n\n"
            "RECOMMENDATION CONTEXT:\n"
            + build_structured_context(context)
        )

        raw_response = self.model.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        return self._parse_response(
            raw_response=raw_response,
            available_route_ids=[
                route.route_id for route in routes
            ],
            selection=selection,
        )

    @staticmethod
    def _parse_response(
        raw_response: str,
        available_route_ids: List[str],
        selection: RouteSelectionDecision,
    ) -> RecommendationDecision:

        try:
            data = json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"AI recommendation response is not valid JSON: {exc}"
            ) from exc

        status = data.get("status")
        selected_route_id = data.get("selected_route_id")
        recommendation = data.get("recommendation", "")
        reasons = data.get("reasons", [])
        limitations = data.get("limitations", [])
        evidence_ids = data.get("evidence_ids", [])

        if status not in {
            "RECOMMEND",
            "NO_RECOMMENDATION",
            "DATA_INCOMPLETE",
        }:
            raise ValueError(
                f"Invalid recommendation status: {status!r}"
            )

        if not isinstance(recommendation, str):
            raise ValueError(
                "recommendation must be a string"
            )

        if not isinstance(reasons, list):
            raise ValueError(
                "reasons must be a list"
            )

        if not isinstance(limitations, list):
            raise ValueError(
                "limitations must be a list"
            )

        if not isinstance(evidence_ids, list):
            raise ValueError(
                "evidence_ids must be a list"
            )

        if selected_route_id is not None:
            if selected_route_id not in available_route_ids:
                raise ValueError(
                    "Recommendation referenced unknown route ID: "
                    f"{selected_route_id}"
                )

        # Recommendation may communicate the selected route, but it must
        # not silently replace the route chosen by the Selection stage.
        if selection.selected_route_id is not None:
            if selected_route_id != selection.selected_route_id:
                raise ValueError(
                    "Recommendation selected route does not match the "
                    "Route Selection decision."
                )
        else:
            if selected_route_id is not None:
                raise ValueError(
                    "Recommendation cannot introduce a route when the "
                    "selection stage did not select one."
                )

        if status == "RECOMMEND" and selected_route_id is None:
            raise ValueError(
                "RECOMMEND requires selected_route_id"
            )

        if status != "RECOMMEND" and selected_route_id is not None:
            raise ValueError(
                f"{status} must not contain selected_route_id"
            )

        return RecommendationDecision(
            status=status,
            selected_route_id=selected_route_id,
            recommendation=recommendation,
            reasons=reasons,
            limitations=limitations,
            evidence_ids=evidence_ids,
        )
