import json

from ai.model_interface import AIModel
from compliance.compliance_agent import ComplianceAgent
from compliance.compliance_models import ComplianceContext
from eligibility.eligibility_agent import EligibilityAgent
from intelligence.route_intelligence_agent import RouteIntelligenceAgent
from intent.value_transfer_intent import ValueTransferIntent
from route_discovery.route_discovery_agent import RouteDiscoveryAgent
from route_selection.route_selection_agent import RouteSelectionAgent
from recommendation.recommendation_agent import RecommendationAgent

from pipeline.value_transfer_pipeline import ValueTransferPipeline


class MockAI(AIModel):

    def __init__(self):
        self.calls = []

    def generate(self, system_prompt: str, user_prompt: str) -> str:

        self.calls.append({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        })

        # ----------------------------------------------------------
        # AI ROUTE DISCOVERY
        # ----------------------------------------------------------
        if "Discover candidate value-transfer routes" in user_prompt:
            return json.dumps([
                {
                    "route_id": "R-IN-BR-A",
                    "rail": "BANKING",
                    "source_country": "India",
                    "source_currency": "INR",
                    "destination_country": "Brazil",
                    "destination_currency": "BRL",
                    "funding_method": "INDIA_BANK",
                    "transfer_path": [
                        "INR",
                        "INDIA_BANK",
                        "PROVIDER_A",
                        "FX",
                        "BRAZIL_BANK",
                        "BRL",
                    ],
                    "delivery_method": "BRAZIL_BANK",
                    "corridor_availability": "CANDIDATE_DISCOVERED",
                    "route_requirements": [],
                },
                {
                    "route_id": "R-IN-BR-B",
                    "rail": "INSTANT_PAYMENT",
                    "source_country": "India",
                    "source_currency": "INR",
                    "destination_country": "Brazil",
                    "destination_currency": "BRL",
                    "funding_method": "INDIA_INSTANT_PAYMENT",
                    "transfer_path": [
                        "INR",
                        "INDIA_INSTANT_PAYMENT",
                        "PROVIDER_B",
                        "FX",
                        "BRAZIL_INSTANT_PAYMENT",
                        "BRL",
                    ],
                    "delivery_method": "BRAZIL_INSTANT_PAYMENT",
                    "corridor_availability": "CANDIDATE_DISCOVERED",
                    "route_requirements": [],
                },
            ])

        # ----------------------------------------------------------
        # AI ROUTE INTELLIGENCE
        # ----------------------------------------------------------
        if "Investigate and normalize intelligence" in user_prompt:

            if "R-IN-BR-A" in user_prompt:
                route_id = "R-IN-BR-A"
                provider = "Provider A"
                rate = 0.053
            else:
                route_id = "R-IN-BR-B"
                provider = "Provider B"
                rate = 0.054

            return json.dumps({
                "route_id": route_id,
                "availability": {
                    "status": "KNOWN",
                    "provider": provider,
                    "source_country": "India",
                    "destination_country": "Brazil",
                    "source_currency": "INR",
                    "destination_currency": "BRL",
                    "funding_method": "bank_or_payment",
                    "delivery_method": "Brazil destination",
                    "explanation": "Supplied by test evidence.",
                },
                "fx": {
                    "status": "KNOWN",
                    "reference_rate": rate,
                    "reference_rate_source": "Test FX Source",
                    "reference_rate_type": "reference",
                    "execution_rate": rate,
                    "execution_rate_source": "Test FX Source",
                    "base_currency": "INR",
                    "quote_currency": "BRL",
                    "explanation": "Supplied by test evidence.",
                },
                "fees": {
                    "status": "KNOWN",
                    "transfer_fee": 100.0,
                    "tax": 10.0,
                    "fx_spread": 10.0,
                    "network_fee": None,
                    "other_fee": None,
                    "currency": "INR",
                    "published_example_amount": None,
                    "published_example_fee": None,
                    "published_example_currency": None,
                    "explanation": "Supplied by test evidence.",
                },
                "settlement": {
                    "status": "KNOWN",
                    "estimated_delivery_time": "8h",
                    "settlement_method": "test settlement",
                    "explanation": "Supplied by test evidence.",
                },
                "data_completeness": "COMPLETE",
                "payment_options": [],
                "evidence": [
                    {
                        "evidence_id": "EVIDENCE-TEST",
                        "source_name": "Test Source",
                        "source_type": "test",
                        "source_url": "https://example.test",
                        "observation": "Test evidence.",
                    }
                ],
            })

        # ----------------------------------------------------------
        # AI COMPLIANCE
        # ----------------------------------------------------------
        if "Evaluate compliance for this candidate route" in user_prompt:

            if "R-IN-BR-A" in user_prompt:
                route_id = "R-IN-BR-A"
            else:
                route_id = "R-IN-BR-B"

            return json.dumps({
                "route_id": route_id,
                "status": "EVALUATED",
                "rule_results": [],
                "missing_information": [],
                "evidence": [
                    "EVIDENCE-TEST",
                ],
            })

        # ----------------------------------------------------------
        # AI ELIGIBILITY
        # ----------------------------------------------------------
        if "determine route eligibility" in user_prompt.lower():

            if "R-IN-BR-A" in user_prompt:
                route_id = "R-IN-BR-A"
            else:
                route_id = "R-IN-BR-B"

            return json.dumps({
                "route_id": route_id,
                "status": "ELIGIBLE",
                "reasons": [
                    "Supplied AI evaluation supports the route."
                ],
                "missing_information": [],
                "evidence_ids": [
                    "EVIDENCE-TEST",
                ],
            })

        # ----------------------------------------------------------
        # AI ROUTE SELECTION
        # ----------------------------------------------------------
        if "Select the most appropriate route" in user_prompt:

            return json.dumps({
                "status": "SELECTED",
                "selected_route_id": "R-IN-BR-B",
                "considered_route_ids": [
                    "R-IN-BR-A",
                    "R-IN-BR-B",
                ],
                "reasons": [
                    "The supplied route intelligence supports R-IN-BR-B."
                ],
                "evidence_ids": [
                    "EVIDENCE-TEST",
                ],
            })

        # ----------------------------------------------------------
        # AI RECOMMENDATION
        # ----------------------------------------------------------
        if "Prepare a user-facing recommendation" in user_prompt:

            return json.dumps({
                "status": "RECOMMEND",
                "selected_route_id": "R-IN-BR-B",
                "recommendation": (
                    "Based on the supplied evidence, R-IN-BR-B is the "
                    "selected route for this value-transfer intent."
                ),
                "reasons": [
                    "The route-selection stage selected R-IN-BR-B."
                ],
                "limitations": [
                    "Final execution remains subject to live conditions."
                ],
                "evidence_ids": [
                    "EVIDENCE-TEST",
                ],
            })

        raise AssertionError(
            "Unexpected AI call received by test harness."
        )


def test_complete_user_to_recommendation_pass():

    intent = ValueTransferIntent(
        intent_id="VTI-IN-BR-001",
        from_country="India",
        to_country="Brazil",
        amount=100000,
        source_currency="INR",
        destination_currency="BRL",
        required_delivery_time="24h",
    )

    compliance_context = ComplianceContext(
        sender_type="individual",
        sender_residency="India",
        transfer_purpose="test_value_transfer",
        recipient_type="individual",
        recipient_relationship="test",
        sender_owns_destination_account=False,
        annual_lrs_used_usd=0.0,
        estimated_transaction_usd=1200.0,
        sender_pan_available=True,
        sender_kyc_available=True,
        india_authorized_channel=True,
        brazil_authorized_channel=True,
        required_documentation_available=True,
    )

    ai = MockAI()

    pipeline = ValueTransferPipeline(
        discovery_agent=RouteDiscoveryAgent(ai),
        intelligence_agent=RouteIntelligenceAgent(ai),
        compliance_agent=ComplianceAgent(ai),
        eligibility_agent=EligibilityAgent(ai),
        selection_agent=RouteSelectionAgent(ai),
        recommendation_agent=RecommendationAgent(ai),
    )

    result = pipeline.run(
        intent=intent,
        compliance_context=compliance_context,
    )

    # ----------------------------------------------------------
    # USER -> INTENT
    # ----------------------------------------------------------
    assert result.intent.intent_id == "VTI-IN-BR-001"
    assert result.intent.from_country == "India"
    assert result.intent.to_country == "Brazil"
    assert result.intent.amount == 100000
    assert result.intent.source_currency == "INR"
    assert result.intent.destination_currency == "BRL"
    assert result.intent.required_delivery_time == "24h"

    # ----------------------------------------------------------
    # AI DISCOVERY
    # ----------------------------------------------------------
    assert len(result.candidate_routes) == 2

    assert {
        route.route_id
        for route in result.candidate_routes
    } == {
        "R-IN-BR-A",
        "R-IN-BR-B",
    }

    # ----------------------------------------------------------
    # AI INTELLIGENCE
    # ----------------------------------------------------------
    assert set(result.route_intelligence.keys()) == {
        "R-IN-BR-A",
        "R-IN-BR-B",
    }

    # ----------------------------------------------------------
    # AI COMPLIANCE
    # ----------------------------------------------------------
    assert set(result.compliance_decisions.keys()) == {
        "R-IN-BR-A",
        "R-IN-BR-B",
    }

    # ----------------------------------------------------------
    # AI ELIGIBILITY
    # ----------------------------------------------------------
    assert set(result.eligibility_decisions.keys()) == {
        "R-IN-BR-A",
        "R-IN-BR-B",
    }

    # ----------------------------------------------------------
    # AI SELECTION
    # ----------------------------------------------------------
    assert result.selection.status == "SELECTED"
    assert result.selection.selected_route_id == "R-IN-BR-B"

    # ----------------------------------------------------------
    # AI RECOMMENDATION
    # ----------------------------------------------------------
    assert result.recommendation.status == "RECOMMEND"
    assert result.recommendation.selected_route_id == "R-IN-BR-B"

    assert "R-IN-BR-B" in result.recommendation.recommendation

    # ----------------------------------------------------------
    # COMPLETE AI CALL CHAIN
    # ----------------------------------------------------------
    #
    # Discovery                    = 1
    # Intelligence x 2            = 2
    # Compliance x 2              = 2
    # Eligibility x 2             = 2
    # Selection                   = 1
    # Recommendation              = 1
    #
    # Total                       = 9
    #
    assert len(ai.calls) == 9
