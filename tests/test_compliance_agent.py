import json

from ai.model_interface import AIModel
from compliance.compliance_agent import ComplianceAgent
from compliance.compliance_models import ComplianceContext
from intelligence.intelligence_models import (
    AvailabilityIntelligence,
    Evidence,
    FeeIntelligence,
    FXIntelligence,
    RouteIntelligence,
    SettlementIntelligence,
)
from intent.value_transfer_intent import (
    create_india_brazil_intent,
)
from models.contracts import (
    CandidateRoute,
    RouteEndpoint,
)


class MockComplianceModel(AIModel):
    """
    Temporary AI model used to validate the AI Compliance Agent.

    The response deliberately contains an unresolved compliance
    requirement so that the agent returns DATA_INCOMPLETE.
    """

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        assert "VTI-IN-BR-001" in user_prompt
        assert "R-IN-BR-BANKING-001" in user_prompt
        assert "RBI" in user_prompt
        assert "BCB" in user_prompt
        assert "EVIDENCE-IN-RBI-001" in user_prompt
        assert "EVIDENCE-BR-BCB-001" in user_prompt

        return json.dumps(
            {
                "status": "DATA_INCOMPLETE",
                "rule_results": [
                    {
                        "rule_id": "INDIA-REGULATORY-CHANNEL",
                        "jurisdiction": "India",
                        "status": "PASS",
                        "explanation": (
                            "The supplied regulatory evidence "
                            "establishes the applicable Indian "
                            "authorized-channel requirement, "
                            "and the transaction context states "
                            "that an authorized channel is being "
                            "used."
                        ),
                    },
                    {
                        "rule_id": "INDIA-PAN-KYC",
                        "jurisdiction": "India",
                        "status": "PASS",
                        "explanation": (
                            "The supplied transaction context "
                            "states that PAN and KYC information "
                            "is available."
                        ),
                    },
                    {
                        "rule_id": "BRAZIL-REGULATED-CHANNEL",
                        "jurisdiction": "Brazil",
                        "status": "UNKNOWN",
                        "explanation": (
                            "The supplied Brazilian regulatory "
                            "evidence establishes the need for "
                            "an authorized FX institution or "
                            "authorized correspondent, but the "
                            "specific route provider has not "
                            "been established as authorized by "
                            "the supplied evidence."
                        ),
                    },
                ],
                "missing_information": [
                    (
                        "Verified authorization status of the "
                        "specific provider/intermediary used by "
                        "the candidate route in Brazil."
                    )
                ],
                "evidence": [
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


def build_route_intelligence() -> RouteIntelligence:
    return RouteIntelligence(
        route_id="R-IN-BR-BANKING-001",
        availability=AvailabilityIntelligence(
            status="KNOWN",
            provider="Example FX Provider",
            source_country="India",
            destination_country="Brazil",
            source_currency="INR",
            destination_currency="BRL",
            funding_method=(
                "PERSONAL_INDIAN_BANK_ACCOUNT"
            ),
            delivery_method=(
                "BRAZIL_LOCAL_BANK_ACCOUNT"
            ),
            explanation=(
                "Candidate route capability is "
                "established by supplied evidence."
            ),
        ),
        fx=FXIntelligence(
            status="KNOWN",
            reference_rate=0.054,
            reference_rate_source=(
                "Example FX Market Data"
            ),
            reference_rate_type="REFERENCE",
            base_currency="INR",
            quote_currency="BRL",
            explanation=(
                "Reference FX information is available."
            ),
        ),
        fees=FeeIntelligence(
            status="UNKNOWN",
            currency="INR",
            explanation=(
                "Transaction-specific fee information "
                "is not established."
            ),
        ),
        settlement=SettlementIntelligence(
            status="UNKNOWN",
            explanation=(
                "Settlement timing is not established."
            ),
        ),
        data_completeness="INCOMPLETE",
        payment_options=[],
        evidence=[],
    )


def build_compliance_context() -> ComplianceContext:
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
            source_url=(
                "https://www.rbi.org.in/"
            ),
            observation=(
                "Regulatory evidence concerning India's "
                "Liberalised Remittance Scheme and "
                "authorized-channel requirements."
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
            source_url=(
                "https://www.bcb.gov.br/"
            ),
            observation=(
                "Regulatory evidence concerning authorized "
                "institutions/correspondents for foreign "
                "exchange operations in Brazil."
            ),
            jurisdiction="Brazil",
            observed_at="2026-09-08",
        ),
    ]


def main():
    print("\n=== AI COMPLIANCE AGENT ===")

    intent = create_india_brazil_intent()
    route = build_route()
    route_intelligence = build_route_intelligence()
    compliance_context = build_compliance_context()
    evidence = build_regulatory_evidence()

    agent = ComplianceAgent(
        MockComplianceModel()
    )

    decision = agent.evaluate(
        intent=intent,
        route=route,
        route_intelligence=route_intelligence,
        compliance_context=compliance_context,
        evidence=evidence,
    )

    print(
        f"\nRoute: {decision.route_id}"
    )

    print(
        f"Compliance status: {decision.status}"
    )

    print("\nCompliance findings:")

    for result in decision.rule_results:
        print(
            f"  - {result.rule_id} "
            f"[{result.jurisdiction}] "
            f"{result.status}"
        )
        print(
            f"    {result.explanation}"
        )

    print("\nMissing information:")

    for item in decision.missing_information:
        print(
            f"  - {item}"
        )

    print("\nEvidence:")

    for evidence_id in decision.evidence:
        print(
            f"  - {evidence_id}"
        )

    # ------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------

    assert decision.route_id == (
        "R-IN-BR-BANKING-001"
    )

    assert decision.status == (
        "DATA_INCOMPLETE"
    )

    assert len(decision.rule_results) == 3

    assert (
        decision.rule_results[0].status
        == "PASS"
    )

    assert (
        decision.rule_results[1].status
        == "PASS"
    )

    assert (
        decision.rule_results[2].status
        == "UNKNOWN"
    )

    assert len(
        decision.missing_information
    ) == 1

    assert (
        "authorization"
        in decision.missing_information[0].lower()
    )

    assert decision.evidence == [
        "EVIDENCE-IN-RBI-001",
        "EVIDENCE-BR-BCB-001",
    ]

    print(
        "\nPASS: Route + Intelligence + "
        "Regulatory Evidence -> AI Compliance Agent"
    )


if __name__ == "__main__":
    main()
