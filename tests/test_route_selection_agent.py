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

from route_selection.route_selection_agent import RouteSelectionAgent


class MockSelectionAI(AIModel):

    def __init__(self, response):
        self.response = response
        self.last_system_prompt = None
        self.last_user_prompt = None

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.last_system_prompt = system_prompt
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


def build_route(route_id, rail="banking"):
    return CandidateRoute(
        route_id=route_id,
        rail=rail,
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
            "cross-border provider",
            "Brazil",
        ],
        delivery_method="Brazil bank account",
        corridor_availability="AI-investigated",
        route_requirements=[],
    )


def build_intelligence(
    route_id,
    provider="Example Provider",
    execution_rate=0.054,
    transfer_fee=100.0,
    delivery_time="12h",
):
    return RouteIntelligence(
        route_id=route_id,
        availability=AvailabilityIntelligence(
            status="KNOWN",
            provider=provider,
            source_country="India",
            destination_country="Brazil",
            source_currency="INR",
            destination_currency="BRL",
            funding_method="India bank account",
            delivery_method="Brazil bank account",
            explanation="Supplied by test evidence.",
        ),
        fx=FXIntelligence(
            status="KNOWN",
            reference_rate=execution_rate,
            reference_rate_source="Example FX Source",
            reference_rate_type="reference",
            execution_rate=execution_rate,
            execution_rate_source="Example FX Source",
            base_currency="INR",
            quote_currency="BRL",
            explanation="Supplied by test evidence.",
        ),
        fees=FeeIntelligence(
            status="KNOWN",
            transfer_fee=transfer_fee,
            tax=10.0,
            fx_spread=20.0,
            currency="INR",
            explanation="Supplied by test evidence.",
        ),
        settlement=SettlementIntelligence(
            status="KNOWN",
            estimated_delivery_time=delivery_time,
            settlement_method="bank settlement",
            explanation="Supplied by test evidence.",
        ),
        data_completeness="COMPLETE",
        payment_options=[],
        evidence=[
            Evidence(
                evidence_id=f"EVIDENCE-{route_id}",
                source_name="Example Source",
                source_type="test",
                source_url="https://example.test",
                observation="Test evidence for route selection.",
            )
        ],
    )


def build_compliance(route_id, status):
    return ComplianceDecision(
        route_id=route_id,
        status=status,
        rule_results=[],
        missing_information=[],
        evidence=[f"EVIDENCE-{route_id}"],
    )


def build_eligibility(route_id, status):
    return EligibilityDecision(
        route_id=route_id,
        status=status,
        reasons=[
            f"Supplied AI eligibility result: {status}"
        ],
        missing_information=[],
        evidence_ids=[f"EVIDENCE-{route_id}"],
    )


def test_route_selection_receives_complete_decision_context():

    routes = [
        build_route("R-A"),
        build_route("R-B", rail="instant_payment"),
        build_route("R-C"),
        build_route("R-D"),
    ]

    intelligence = {
        "R-A": build_intelligence(
            "R-A",
            provider="Provider A",
            execution_rate=0.053,
            transfer_fee=500.0,
            delivery_time="18h",
        ),
        "R-B": build_intelligence(
            "R-B",
            provider="Provider B",
            execution_rate=0.054,
            transfer_fee=100.0,
            delivery_time="8h",
        ),
        "R-C": build_intelligence(
            "R-C",
            provider="Provider C",
            execution_rate=0.055,
            transfer_fee=50.0,
            delivery_time="6h",
        ),
        "R-D": build_intelligence(
            "R-D",
            provider="Provider D",
            execution_rate=0.056,
            transfer_fee=25.0,
            delivery_time="4h",
        ),
    }

    compliance = {
        route.route_id: build_compliance(
            route.route_id,
            "EVALUATED",
        )
        for route in routes
    }

    eligibility = {
        "R-A": build_eligibility("R-A", "ELIGIBLE"),
        "R-B": build_eligibility("R-B", "ELIGIBLE"),
        "R-C": build_eligibility("R-C", "INELIGIBLE"),
        "R-D": build_eligibility("R-D", "DATA_INCOMPLETE"),
    }

    ai = MockSelectionAI(
        {
            "status": "SELECTED",
            "selected_route_id": "R-B",
            "considered_route_ids": [
                "R-A",
                "R-B",
                "R-C",
                "R-D",
            ],
            "reasons": [
                "The supplied evidence supports selecting R-B."
            ],
            "evidence_ids": [
                "EVIDENCE-R-B",
            ],
        }
    )

    agent = RouteSelectionAgent(ai)

    decision = agent.select(
        intent=build_intent(),
        routes=routes,
        intelligence=intelligence,
        compliance=compliance,
        eligibility=eligibility,
    )

    assert decision.status == "SELECTED"
    assert decision.selected_route_id == "R-B"

    assert decision.considered_route_ids == [
        "R-A",
        "R-B",
        "R-C",
        "R-D",
    ]

    # Complete route universe is supplied to the AI.
    for route_id in ["R-A", "R-B", "R-C", "R-D"]:
        assert route_id in ai.last_user_prompt

    # The intent is supplied to the AI.
    assert "VTI-IN-BR-001" in ai.last_user_prompt
    assert "India" in ai.last_user_prompt
    assert "Brazil" in ai.last_user_prompt
    assert "100000" in ai.last_user_prompt
    assert "INR" in ai.last_user_prompt
    assert "BRL" in ai.last_user_prompt
    assert "24h" in ai.last_user_prompt

    # Route intelligence is supplied to the AI.
    assert "Provider A" in ai.last_user_prompt
    assert "Provider B" in ai.last_user_prompt
    assert "Provider C" in ai.last_user_prompt
    assert "Provider D" in ai.last_user_prompt

    assert "0.053" in ai.last_user_prompt
    assert "0.054" in ai.last_user_prompt
    assert "500.0" in ai.last_user_prompt
    assert "100.0" in ai.last_user_prompt
    assert "18h" in ai.last_user_prompt
    assert "8h" in ai.last_user_prompt

    # Previous AI-stage outputs are supplied as context.
    assert '"R-A"' in ai.last_user_prompt
    assert '"R-B"' in ai.last_user_prompt
    assert '"R-C"' in ai.last_user_prompt
    assert '"R-D"' in ai.last_user_prompt

    assert "ELIGIBLE" in ai.last_user_prompt
    assert "INELIGIBLE" in ai.last_user_prompt
    assert "DATA_INCOMPLETE" in ai.last_user_prompt


def test_route_selection_can_return_no_selection():

    routes = [
        build_route("R-A"),
        build_route("R-B"),
    ]

    intelligence = {
        "R-A": build_intelligence("R-A"),
        "R-B": build_intelligence("R-B"),
    }

    compliance = {
        "R-A": build_compliance("R-A", "EVALUATED"),
        "R-B": build_compliance("R-B", "EVALUATED"),
    }

    eligibility = {
        "R-A": build_eligibility("R-A", "INELIGIBLE"),
        "R-B": build_eligibility("R-B", "DATA_INCOMPLETE"),
    }

    ai = MockSelectionAI(
        {
            "status": "NO_SELECTION",
            "selected_route_id": None,
            "considered_route_ids": [
                "R-A",
                "R-B",
            ],
            "reasons": [
                "The supplied evaluations do not support a selection."
            ],
            "evidence_ids": [],
        }
    )

    agent = RouteSelectionAgent(ai)

    decision = agent.select(
        intent=build_intent(),
        routes=routes,
        intelligence=intelligence,
        compliance=compliance,
        eligibility=eligibility,
    )

    assert decision.status == "NO_SELECTION"
    assert decision.selected_route_id is None
    assert decision.considered_route_ids == [
        "R-A",
        "R-B",
    ]


def test_route_selection_can_return_data_incomplete():

    routes = [
        build_route("R-A"),
        build_route("R-B"),
    ]

    intelligence = {
        "R-A": build_intelligence("R-A"),
        "R-B": build_intelligence("R-B"),
    }

    compliance = {
        "R-A": build_compliance("R-A", "EVALUATED"),
        "R-B": build_compliance("R-B", "EVALUATED"),
    }

    eligibility = {
        "R-A": build_eligibility("R-A", "ELIGIBLE"),
        "R-B": build_eligibility("R-B", "ELIGIBLE"),
    }

    ai = MockSelectionAI(
        {
            "status": "DATA_INCOMPLETE",
            "selected_route_id": None,
            "considered_route_ids": [
                "R-A",
                "R-B",
            ],
            "reasons": [
                "Available information is insufficient for reliable selection."
            ],
            "evidence_ids": [],
        }
    )

    agent = RouteSelectionAgent(ai)

    decision = agent.select(
        intent=build_intent(),
        routes=routes,
        intelligence=intelligence,
        compliance=compliance,
        eligibility=eligibility,
    )

    assert decision.status == "DATA_INCOMPLETE"
    assert decision.selected_route_id is None
