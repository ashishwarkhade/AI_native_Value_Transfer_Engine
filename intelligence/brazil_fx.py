from intelligence.intelligence_models import (
    AvailabilityIntelligence,
    Evidence,
)


BCB_AUTHORIZED_FX_URL = (
    "https://www.bcb.gov.br/rex/IAMC/Port/Instituicoes/"
    "inst_autorizadas.asp?frame=1"
)


def get_brazil_fx_authorization_intelligence():
    """
    Returns authoritative evidence that Brazil maintains an official
    registry of institutions authorized to operate in the FX market.

    This function does NOT claim that a particular institution can
    execute our India -> Brazil transaction.

    Provider-specific corridor verification comes later.
    """

    evidence = Evidence(
        evidence_id="BCB-FX-AUTH-001",
        source_name="Banco Central do Brasil",
        source_type="REGULATORY_REGISTRY",
        source_url=BCB_AUTHORIZED_FX_URL,
        observation=(
            "Banco Central do Brasil publishes a current list of "
            "institutions authorized to operate in the foreign-exchange market."
        ),
        jurisdiction="BRAZIL",
    )

    availability = AvailabilityIntelligence(
        status="KNOWN",
        provider=None,
        source_country=None,
        destination_country="Brazil",
        source_currency=None,
        destination_currency="BRL",
        funding_method=None,
        delivery_method=None,
        explanation=(
            "Brazil has an official authorization registry for FX institutions. "
            "Specific provider and corridor availability still require verification."
        ),
    )

    return availability, evidence
