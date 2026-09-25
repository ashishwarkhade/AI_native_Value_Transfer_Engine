import json

from ai.model_interface import AIModel
from intelligence.intelligence_models import Evidence
from intelligence.route_intelligence_agent import (
    RouteIntelligenceAgent,
)
from intent.value_transfer_intent import (
    create_india_brazil_intent,
)
from models.contracts import (
    CandidateRoute,
    RouteEndpoint,
)


class MockRouteIntelligenceModel(AIModel):
    """
    Temporary AI model for testing.

    It demonstrates that the intelligence agent can normalize
    evidence-backed intelligence without embedding a provider
    such as Wise into the agent.
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        # The test deliberately checks that the candidate route
        # reaches the AI investigation context.
        assert "R-IN-BR-BANKING-001" in user_prompt
        assert "CROSS_BORDER_FX_PROVIDER" in user_prompt
        assert "EVIDENCE-BANK-001" in user_prompt

        return json.dumps(
            {
                "availability": {
                    "status": "KNOWN",
                    "provider": "Example FX Provider",
                    "source_country": "India",
                    "destination_country": "Brazil",
                    "source_currency": "INR",
                    "destination_currency": "BRL",
                    "funding_method": (
                        "PERSONAL_INDIAN_BANK_ACCOUNT"
                    ),
                    "delivery_method": (
                        "BRAZIL_LOCAL_BANK_ACCOUNT"
                    ),
                    "explanation": (
                        "The supplied evidence establishes "
                        "the investigated route capability."
                    ),
                },
                "fx": {
                    "status": "KNOWN",
                    "reference_rate": 0.054,
                    "reference_rate_source": (
                        "Example FX Market Data"
                    ),
                    "reference_rate_type": "REFERENCE",
                    "execution_rate": None,
                    "execution_rate_source": None,
                    "base_currency": "INR",
                    "quote_currency": "BRL",
                    "explanation": (
                        "A reference FX rate is available, "
                        "but no execution quote was supplied."
                    ),
                },
                "fees": {
                    "status": "UNKNOWN",
                    "transfer_fee": None,
                    "tax": None,
                    "fx_spread": None,
                    "network_fee": None,
                    "other_fee": None,
                    "currency": "INR",
                    "published_example_amount": None,
                    "published_example_fee": None,
                    "published_example_currency": None,
                    "explanation": (
                        "No verified transaction-specific "
                        "fee information was supplied."
                    ),
                },
                "settlement": {
                    "status": "UNKNOWN",
                    "estimated_delivery_time": None,
                    "settlement_method": None,
                    "explanation": (
                        "No verified delivery estimate "
                        "was supplied."
                    ),
                },
                "payment_options": [],
                "data_completeness": "INCOMPLETE",
                "evidence": [
                    {
                        "evidence_id": "EVIDENCE-BANK-001",
                        "source_name": "Example FX Provider",
                        "source_type": "PROVIDER_DOCUMENTATION",
                        "source_url": (
                            "https://example.com/provider"
                        ),
                        "observation": (
                            "Provider documentation indicates "
                            "support for the investigated "
                            "India-to-Brazil transfer path."
                        ),
                        "jurisdiction": None,
                        "observed_at": "2026-09-08",
                    },
                    {
                        "evidence_id": "EVIDENCE-FX-001",
                        "source_name": "Example FX Market Data",
                        "source_type": "MARKET_DATA",
                        "source_url": (
                            "https://example.com/fx"
                        ),
                        "observation": (
                            "Reference INR/BRL rate observed "
                            "at 0.054."
                        ),
                        "jurisdiction": None,
                        "observed_at": "2026-09-08",
                    },
                ],
            }
        )


def main():
    print("\n=== AI ROUTE INTELLIGENCE AGENT ===")

    intent = create_india_brazil_intent()

    route = CandidateRoute(
        route_id="R-IN-BR-BANKING-001",
        rail="BANKING",
        source=RouteEndpoint(
            country="India",
            currency="INR",
        ),
        destination=RouteEndpoint(
            country="Brazil",
            currency="BRL",
        ),
        funding_method=(
            "PERSONAL_INDIAN_BANK_ACCOUNT"
        ),
        transfer_path=[
            "INR",
            "INDIA_BANK",
            "CROSS_BORDER_FX_PROVIDER",
            "BRAZIL_LOCAL_BANKING",
            "BRL",
        ],
        delivery_method=(
            "BRAZIL_LOCAL_BANK_ACCOUNT"
        ),
        corridor_availability=(
            "CANDIDATE_DISCOVERED"
        ),
        route_requirements=[],
    )

    evidence = [
        Evidence(
            evidence_id="EVIDENCE-BANK-001",
            source_name="Example FX Provider",
            source_type="PROVIDER_DOCUMENTATION",
            source_url="https://example.com/provider",
            observation=(
                "Provider documentation indicates support "
                "for the investigated India-to-Brazil "
                "transfer path."
            ),
            observed_at="2026-09-08",
        ),
        Evidence(
            evidence_id="EVIDENCE-FX-001",
            source_name="Example FX Market Data",
            source_type="MARKET_DATA",
            source_url="https://example.com/fx",
            observation=(
                "Reference INR/BRL rate observed at 0.054."
            ),
            observed_at="2026-09-08",
        ),
    ]

    agent = RouteIntelligenceAgent(
        MockRouteIntelligenceModel()
    )

    intelligence = agent.investigate(
        intent=intent,
        route=route,
        evidence=evidence,
    )

    print(f"\nRoute: {intelligence.route_id}")

    print(
        "Availability:",
        intelligence.availability.status,
        "/",
        intelligence.availability.provider,
    )

    print(
        "FX:",
        intelligence.fx.status,
        "/",
        intelligence.fx.reference_rate,
    )

    print(
        "Fees:",
        intelligence.fees.status,
    )

    print(
        "Settlement:",
        intelligence.settlement.status,
    )

    print(
        "Data completeness:",
        intelligence.data_completeness,
    )

    print("\nEvidence:")

    for item in intelligence.evidence:
        print(
            f"  - {item.evidence_id}: "
            f"{item.source_name}"
        )

    # ------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------

    assert intelligence.route_id == (
        "R-IN-BR-BANKING-001"
    )

    assert (
        intelligence.availability.status
        == "KNOWN"
    )

    assert (
        intelligence.availability.provider
        == "Example FX Provider"
    )

    assert (
        intelligence.fx.status
        == "KNOWN"
    )

    assert (
        intelligence.fx.reference_rate
        == 0.054
    )

    # Missing transaction-specific fee data must remain UNKNOWN.
    assert (
        intelligence.fees.status
        == "UNKNOWN"
    )

    assert (
        intelligence.fees.transfer_fee
        is None
    )

    # Missing settlement data must remain UNKNOWN.
    assert (
        intelligence.settlement.status
        == "UNKNOWN"
    )

    assert (
        intelligence.settlement.estimated_delivery_time
        is None
    )

    # Therefore the overall intelligence dataset is incomplete.
    assert (
        intelligence.data_completeness
        == "INCOMPLETE"
    )

    assert len(intelligence.evidence) == 2

    evidence_ids = [
        item.evidence_id
        for item in intelligence.evidence
    ]

    assert evidence_ids == [
        "EVIDENCE-BANK-001",
        "EVIDENCE-FX-001",
    ]

    print(
        "\nPASS: Candidate Route "
        "-> AI Route Intelligence Agent"
    )


if __name__ == "__main__":
    main()
