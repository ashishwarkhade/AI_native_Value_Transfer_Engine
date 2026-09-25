import json

from ai.model_interface import AIModel
from compliance.compliance_agent import ComplianceAgent
from compliance.compliance_models import (
    ComplianceContext,
)
from eligibility.eligibility_agent import (
    EligibilityAgent,
)
from intelligence.intelligence_models import (
    AvailabilityIntelligence,
    Evidence,
    FeeIntelligence,
    FXIntelligence,
    RouteIntelligence,
    SettlementIntelligence,
)
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
    Simulates AI Route Intelligence.

    This is deliberately provider-neutral.
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        assert "R-IN-BR-BANKING-001" in user_prompt

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
                        "Route capability established "
                        "by supplied evidence."
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
                        "Reference rate known; "
                        "execution rate unavailable."
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
                        "Transaction-specific fees "
                        "are not established."
                    ),
                },
                "settlement": {
                    "status": "UNKNOWN",
                    "estimated_delivery_time": None,
                    "settlement_method": None,
                    "explanation": (
                        "Settlement timing is "
                        "not established."
                    ),
                },
                "payment_options": [],
                "data_completeness": "INCOMPLETE",
                "evidence": [
                    {
                        "evidence_id": (
                            "EVIDENCE-BANK-001"
                        ),
                        "source_name": (
                            "Example FX Provider"
                        ),
                        "source_type": (
                            "PROVIDER_DOCUMENTATION"
                        ),
                        "source_url": (
                            "https://example.com/provider"
                        ),
                        "observation": (
                            "Provider documentation "
                            "supports the candidate "
                            "route capability."
                        ),
                        "jurisdiction": None,
                        "observed_at": "2026-09-08",
                    }
                ],
            }
        )


class MockComplianceModel(AIModel):
    """
    Simulates AI Compliance evaluation.

    The provider authorization required for the Brazilian
    side is deliberately unresolved.
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        assert "R-IN-BR-BANKING-001" in user_prompt
        assert "EVIDENCE-IN-RBI-001" in user_prompt
        assert "EVIDENCE-BR-BCB-001" in user_prompt

        return json.dumps(
            {
                "status": "DATA_INCOMPLETE",
                "rule_results": [
                    {
                        "rule_id": (
                            "INDIA-REGULATORY-CHANNEL"
                        ),
                        "jurisdiction": "India",
                        "status": "PASS",
                        "explanation": (
                            "The supplied evidence and "
                            "transaction context establish "
                            "the applicable Indian channel "
                            "requirement."
                        ),
                    },
                    {
                        "rule_id": (
                            "BRAZIL-REGULATED-CHANNEL"
                        ),
                        "jurisdiction": "Brazil",
                        "status": "UNKNOWN",
                        "explanation": (
                            "The specific provider's "
                            "Brazilian authorization has "
                            "not been established."
                        ),
                    },
                ],
                "missing_information": [
                    (
                        "Verified authorization status "
                        "of the specific provider or "
                        "intermediary in Brazil."
                    )
                ],
                "evidence": [
                    "EVIDENCE-IN-RBI-001",
                    "EVIDENCE-BR-BCB-001",
                ],
            }
        )


class MockEligibilityModel(AIModel):
    """
    Simulates AI Eligibility evaluation.

    Because AI Compliance is DATA_INCOMPLETE and route
    intelligence is INCOMPLETE, eligibility cannot currently
    be established.
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        assert "R-IN-BR-BANKING-001" in user_prompt
        assert "DATA_INCOMPLETE" in user_prompt

        return json.dumps(
            {
                "status": "DATA_INCOMPLETE",
                "reasons": [
                    (
                        "Eligibility cannot currently "
                        "be established because the AI "
                        "Compliance Agent has unresolved "
                        "Brazilian authorization evidence."
                    ),
                    (
                        "Route intelligence is incomplete "
                        "because transaction-specific fees "
                        "and settlement timing are unknown."
                    ),
                ],
                "missing_information": [
                    (
                        "Verified Brazilian authorization "
                        "status for the route provider."
                    ),
                    (
                        "Transaction-specific route fee "
                        "and settlement information."
                    ),
                ],
                "evidence_ids": [
                    "EVIDENCE-BANK-001",
                    "EVIDENCE-IN-RBI-001",
                    "EVIDENCE-BR-BCB-001",
                ],
            }
        )


def build_route() -> CandidateRoute:
    return CandidateRoute(
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


def build_compliance_context():
    return ComplianceContext(
        sender_type="RESIDENT_INDIVIDUAL",
        sender_residency="INDIA",
        transfer_purpose="PRIVATE_VISIT",
        recipient_type="INDIVIDUAL",
        recipient_relationship="SELF",
        sender_owns_destination_account=True,
        annual_lrs_used_usd=0.0,
        estimated_transaction_usd=1200.0,
        sender_pan_available=True,
        sender_kyc_available=True,
        india_authorized_channel=True,
        brazil_authorized_channel=False,
        required_documentation_available=True,
    )


def build_regulatory_evidence():
    return [
        Evidence(
            evidence_id="EVIDENCE-IN-RBI-001",
            source_name="Reserve Bank of India",
            source_type="REGULATORY_SOURCE",
            source_url="https://www.rbi.org.in/",
            observation=(
                "Evidence concerning Indian "
                "foreign-exchange requirements."
            ),
            jurisdiction="India",
            observed_at="2026-09-08",
        ),
        Evidence(
            evidence_id="EVIDENCE-BR-BCB-001",
            source_name=(
                "Banco Central do Brasil"
            ),
            source_type="REGULATORY_SOURCE",
            source_url="https://www.bcb.gov.br/",
            observation=(
                "Evidence concerning Brazilian "
                "foreign-exchange authorization."
            ),
            jurisdiction="Brazil",
            observed_at="2026-09-08",
        ),
    ]


def main():
    print("\n=== AI ELIGIBILITY AGENT ===")

    # ------------------------------------------------------------
    # 1. Intent
    # ------------------------------------------------------------

    intent = create_india_brazil_intent()

    print("\nIntent:")
    print(f"  ID: {intent.intent_id}")
    print(
        f"  {intent.from_country} -> "
        f"{intent.to_country}"
    )
    print(
        f"  Amount: {intent.amount} "
        f"{intent.source_currency}"
    )

    # ------------------------------------------------------------
    # 2. Candidate route
    #
    # This represents a route already discovered by AI.
    # There is NO deterministic route discovery here.
    # ------------------------------------------------------------

    route = build_route()

    print("\nCandidate Route:")
    print(f"  Route: {route.route_id}")
    print(f"  Rail: {route.rail}")

    # ------------------------------------------------------------
    # 3. AI Route Intelligence
    # ------------------------------------------------------------

    intelligence_agent = RouteIntelligenceAgent(
        MockRouteIntelligenceModel()
    )

    intelligence = intelligence_agent.investigate(
        intent=intent,
        route=route,
        evidence=[
            Evidence(
                evidence_id="EVIDENCE-BANK-001",
                source_name="Example FX Provider",
                source_type=(
                    "PROVIDER_DOCUMENTATION"
                ),
                source_url=(
                    "https://example.com/provider"
                ),
                observation=(
                    "Provider documentation supports "
                    "the candidate route capability."
                ),
                observed_at="2026-09-08",
            )
        ],
    )

    print("\nAI Route Intelligence:")
    print(
        f"  Availability: "
        f"{intelligence.availability.status}"
    )
    print(
        f"  FX: {intelligence.fx.status}"
    )
    print(
        f"  Fees: {intelligence.fees.status}"
    )
    print(
        f"  Settlement: "
        f"{intelligence.settlement.status}"
    )
    print(
        f"  Data completeness: "
        f"{intelligence.data_completeness}"
    )

    # ------------------------------------------------------------
    # 4. AI Compliance
    # ------------------------------------------------------------

    compliance_agent = ComplianceAgent(
        MockComplianceModel()
    )

    compliance = compliance_agent.evaluate(
        intent=intent,
        route=route,
        route_intelligence=intelligence,
        compliance_context=(
            build_compliance_context()
        ),
        evidence=build_regulatory_evidence(),
    )

    print("\nAI Compliance:")
    print(
        f"  Status: {compliance.status}"
    )

    for result in compliance.rule_results:
        print(
            f"  - {result.rule_id}: "
            f"{result.status}"
        )

    # ------------------------------------------------------------
    # 5. AI Eligibility
    # ------------------------------------------------------------

    eligibility_agent = EligibilityAgent(
        MockEligibilityModel()
    )

    decision = eligibility_agent.evaluate(
        intent=intent,
        route=route,
        compliance=compliance,
        intelligence=intelligence,
    )

    print("\nAI Eligibility Decision:")
    print(
        f"  Route: {decision.route_id}"
    )
    print(
        f"  Status: {decision.status}"
    )

    print("\nReasons:")

    for reason in decision.reasons:
        print(f"  - {reason}")

    print("\nMissing Information:")

    for item in decision.missing_information:
        print(f"  - {item}")

    print("\nEvidence IDs:")

    for evidence_id in decision.evidence_ids:
        print(f"  - {evidence_id}")

    # ------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------

    assert intent.intent_id == "VTI-IN-BR-001"

    assert route.route_id == (
        "R-IN-BR-BANKING-001"
    )

    assert (
        intelligence.data_completeness
        == "INCOMPLETE"
    )

    assert (
        compliance.status
        == "DATA_INCOMPLETE"
    )

    assert (
        decision.status
        == "DATA_INCOMPLETE"
    )

    assert len(
        decision.missing_information
    ) == 2

    assert (
        "EVIDENCE-IN-RBI-001"
        in decision.evidence_ids
    )

    assert (
        "EVIDENCE-BR-BCB-001"
        in decision.evidence_ids
    )

    print(
        "\nPASS: AI Intelligence -> "
        "AI Compliance -> AI Eligibility"
    )


if __name__ == "__main__":
    main()
