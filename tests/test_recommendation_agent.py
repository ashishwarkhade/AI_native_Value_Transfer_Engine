import json

from ai.model_interface import AIModel
from compliance.compliance_models import ComplianceDecision
from eligibility.eligibility_models import EligibilityDecision
from intelligence.intelligence_models import (
    AvailabilityIntelligence,
    Evidence,
    FeeIntelligence,
    FXIntelligence,
    RouteIntelligence,
    SettlementIntelligence,
)
from intent.value_transfer_intent import ValueTransferIntent
from models.contracts import CandidateRoute, RouteEndpoint
from route_selection.route_selection_models import RouteSelectionDecision

from recommendation.recommendation_agent import RecommendationAgent


class MockRecommendationAI(AIModel):

    def __init__(self, response):
        self.response = response
        self.last_user_prompt = None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.last_user_prompt = user_prompt
        return json.dumps(self.response)


def build_intent():
    return ValueTransferIntent(
        intent_id="VTI-IN-BR-001",
        from_country="India",
        to_country="Brazil",
        amount=100000,
        source_currency="INR",
        destination_currency="BRL",
        required_delivery_time="24h",
    )


def build_route(route_id):
    return CandidateRoute(
        route_id=route_id,
        rail="BANKING",
        source=RouteEndpoint(
            country="India",
            currency="INR",
        ),
        destination=RouteEndpoint(
            country="Brazil",
            currency="BRL",
        ),
        funding_method="India bank account",
        transfer_path=[
            "India",
            "provider",
            "FX",
            "Brazil",
        ],
        delivery_method="Brazil bank account",
        corridor_availability="AI-investigated",
        route_requirements=[],
    )


def build_intelligence(route_id):
    return RouteIntelligence(
        route_id=route_id,
        availability=AvailabilityIntelligence(
            status="KNOWN",
            provider="Example Provider",
            source_country="India",
            destination_country="Brazil",
            source_currency="INR",
            destination_currency="BRL",
            funding_method="India bank account",
            delivery_method="Brazil bank account",
            explanation="Test evidence.",
        ),
        fx=FXIntelligence(
            status="KNOWN",
            execution_rate=0.054,
            execution_rate_source="Test FX Source",
            base_currency="INR",
            quote_currency="BRL",
            explanation="Test evidence.",
        ),
        fees=FeeIntelligence(
            status="KNOWN",
            transfer_fee=100.0,
            currency="INR",
            explanation="Test evidence.",
        ),
        settlement=SettlementIntelligence(
            status="KNOWN",
            estimated_delivery_time="8h",
            settlement_method="Test settlement",
            explanation="Test evidence.",
        ),
        data_completeness="COMPLETE",
        evidence=[
            Evidence(
                evidence_id=f"EVIDENCE-{route_id}",
                source_name="Test Source",
                source_type="test",
                source_url="https://example.test",
                observation="Test evidence.",
            )
        ],
    )


def build_compliance(route_id):
    return ComplianceDecision(
        route_id=route_id,
        status="EVALUATED",
        rule_results=[],
        missing_information=[],
        evidence=[f"EVIDENCE-{route_id}"],
    )


def build_eligibility(route_id):
    return EligibilityDecision(
        route_id=route_id,
        status="ELIGIBLE",
        reasons=["Supplied AI eligibility result."],
        missing_information=[],
        evidence_ids=[f"EVIDENCE-{route_id}"],
    )


def test_recommendation_communicates_selected_route():

    routes = [
        build_route("R-A"),
        build_route("R-B"),
    ]

    intelligence = {
        "R-A": build_intelligence("R-A"),
        "R-B": build_intelligence("R-B"),
    }

    compliance = {
        "R-A": build_compliance("R-A"),
        "R-B": build_compliance("R-B"),
    }

    eligibility = {
        "R-A": build_eligibility("R-A"),
        "R-B": build_eligibility("R-B"),
    }

    selection = RouteSelectionDecision(
        status="SELECTED",
        selected_route_id="R-B",
        considered_route_ids=[
            "R-A",
            "R-B",
        ],
        reasons=[
            "AI selection chose R-B."
        ],
        evidence_ids=[
            "EVIDENCE-R-B",
        ],
    )

    ai = MockRecommendationAI(
        {
            "status": "RECOMMEND",
            "selected_route_id": "R-B",
            "recommendation": (
                "Based on the supplied evidence, R-B is the selected "
                "route for this value-transfer intent."
            ),
            "reasons": [
                "The route-selection stage selected R-B."
            ],
            "limitations": [
                "Final execution remains subject to live provider conditions."
            ],
            "evidence_ids": [
                "EVIDENCE-R-B",
            ],
        }
    )

    agent = RecommendationAgent(ai)

    decision = agent.recommend(
        intent=build_intent(),
        routes=routes,
        intelligence=intelligence,
        compliance=compliance,
        eligibility=eligibility,
        selection=selection,
    )

    assert decision.status == "RECOMMEND"
    assert decision.selected_route_id == "R-B"

    assert "R-A" in ai.last_user_prompt
    assert "R-B" in ai.last_user_prompt
    assert "VTI-IN-BR-001" in ai.last_user_prompt
    assert "EVIDENCE-R-B" in ai.last_user_prompt


def test_recommendation_cannot_replace_selected_route():

    routes = [
        build_route("R-A"),
        build_route("R-B"),
    ]

    selection = RouteSelectionDecision(
        status="SELECTED",
        selected_route_id="R-B",
        considered_route_ids=[
            "R-A",
            "R-B",
        ],
    )

    ai = MockRecommendationAI(
        {
            "status": "RECOMMEND",
            "selected_route_id": "R-A",
            "recommendation": "Incorrect alternate route.",
            "reasons": [],
            "limitations": [],
            "evidence_ids": [],
        }
    )

    agent = RecommendationAgent(ai)

    try:
        agent.recommend(
            intent=build_intent(),
            routes=routes,
            intelligence={
                "R-A": build_intelligence("R-A"),
                "R-B": build_intelligence("R-B"),
            },
            compliance={
                "R-A": build_compliance("R-A"),
                "R-B": build_compliance("R-B"),
            },
            eligibility={
                "R-A": build_eligibility("R-A"),
                "R-B": build_eligibility("R-B"),
            },
            selection=selection,
        )
    except ValueError as exc:
        assert "does not match" in str(exc)
    else:
        raise AssertionError(
            "Recommendation incorrectly replaced the selected route."
        )
