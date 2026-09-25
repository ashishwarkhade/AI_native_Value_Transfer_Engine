from compliance.compliance_models import ComplianceContext


def create_india_brazil_first_pass_context() -> ComplianceContext:
    """
    Concrete first-pass scenario:

    Indian resident individual
    -> own/controlled account in Brazil
    -> private visit
    -> INR 100,000

    The estimated USD amount is intentionally supplied as scenario data.
    In the production engine this will come from live FX intelligence.
    """

    return ComplianceContext(
        sender_type="RESIDENT_INDIVIDUAL",
        sender_residency="INDIA",
        transfer_purpose="PRIVATE_VISIT",
        recipient_type="SELF",
        recipient_relationship="SELF",
        sender_owns_destination_account=True,

        # First-pass test assumption.
        annual_lrs_used_usd=0.0,
        estimated_transaction_usd=1200.0,

        sender_pan_available=True,
        sender_kyc_available=True,

        india_authorized_channel=True,
        brazil_authorized_channel=True,

        required_documentation_available=True,
    )
