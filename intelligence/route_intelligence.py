from intelligence.intelligence_models import (
    AvailabilityIntelligence,
    Evidence,
    FXIntelligence,
    FeeIntelligence,
    PaymentOptionIntelligence,
    RouteIntelligence,
    SettlementIntelligence,
)
from intelligence.wise_quote import request_wise_quote
from models.contracts import CandidateRoute


WISE_INDIA_BRAZIL_URL = (
    "https://wise.com/in/send-money/send-money-to-brazil"
)

WISE_INR_CONVERTER_URL = (
    "https://wise.com/in/currency-converter/"
    "inr-to-brl-rate?amount=100000"
)

WISE_INR_GUIDE_URL = (
    "https://wise.com/help/articles/2932151/"
    "guide-to-inr-transfers"
)

WISE_BRL_GUIDE_URL = (
    "https://wise.com/help/articles/2932353/"
    "guide-to-brl-transfers"
)


def _collect_public_evidence():
    return [
        Evidence(
            evidence_id="WISE-IN-BR-CORRIDOR-001",
            source_name="Wise",
            source_type="PROVIDER_CORRIDOR",
            source_url=WISE_INDIA_BRAZIL_URL,
            observation=(
                "Wise publicly supports sending INR from India to Brazil "
                "and delivering BRL to a local Brazilian bank account."
            ),
            jurisdiction="INDIA/BRAZIL",
        ),
        Evidence(
            evidence_id="WISE-INR-REQUIREMENTS-001",
            source_name="Wise",
            source_type="PROVIDER_REQUIREMENTS",
            source_url=WISE_INR_GUIDE_URL,
            observation=(
                "Wise requires INR senders to be Indian tax residents "
                "based in India and documents Aadhaar, PAN, verification "
                "and personal Indian bank/UPI funding requirements."
            ),
            jurisdiction="INDIA",
        ),
        Evidence(
            evidence_id="WISE-BRL-DELIVERY-001",
            source_name="Wise",
            source_type="PROVIDER_DELIVERY",
            source_url=WISE_BRL_GUIDE_URL,
            observation=(
                "Wise supports BRL delivery to Brazilian personal and "
                "business bank accounts and publishes recipient requirements."
            ),
            jurisdiction="BRAZIL",
        ),
        Evidence(
            evidence_id="WISE-INR-BRL-MARKET-001",
            source_name="Wise",
            source_type="REFERENCE_FX",
            source_url=WISE_INR_CONVERTER_URL,
            observation=(
                "Current Wise INR/BRL reference page shows a mid-market "
                "rate of 1 INR = 0.05405 BRL and displays 100,000 INR "
                "as approximately 5,405.19 BRL before transfer economics."
            ),
            jurisdiction="INDIA/BRAZIL",
        ),
        Evidence(
            evidence_id="WISE-IN-BR-PRICING-001",
            source_name="Wise",
            source_type="PROVIDER_PRICING_EXAMPLE",
            source_url=WISE_INDIA_BRAZIL_URL,
            observation=(
                "Wise currently publishes an example for an 80,000 INR "
                "India-to-Brazil transfer showing 2,092.07 INR in transfer "
                "cost for bank-transfer funding. This is a published example "
                "and is NOT treated as the fee for the current 100,000 INR intent."
            ),
            jurisdiction="INDIA/BRAZIL",
        ),
    ]


def _convert_payment_option(option):
    return PaymentOptionIntelligence(
        pay_in=option.pay_in,
        pay_out=option.pay_out,
        enabled=option.enabled,
        disabled_reason_code=option.disabled_reason_code,
        disabled_reason_message=option.disabled_reason_message,
        source_amount=option.source_amount,
        target_amount=option.target_amount,
        execution_rate=option.execution_rate,
        transfer_fee=option.transfer_fee,
        tax=option.tax,
        total_fee=option.total_fee,
        fee_currency=option.fee_currency,
        estimated_delivery=option.estimated_delivery,
        formatted_estimated_delivery=(
            option.formatted_estimated_delivery
        ),
        fee_percentage=option.fee_percentage,
        explanation=(
            "Payment option returned by Wise quote."
            if option.enabled
            else (
                "Payment option returned by Wise quote but "
                "currently disabled by the provider."
            )
        ),
    )


def _collect_wise_quote_evidence(quote):
    evidence = []

    if quote.status == "KNOWN":
        evidence.append(
            Evidence(
                evidence_id="WISE-QUOTE-LIVE-001",
                source_name="Wise API",
                source_type="TRANSACTION_QUOTE",
                source_url=(
                    "https://api.wise.com/2026Q3/quotes"
                ),
                observation=(
                    "Wise returned transaction-specific quote data for "
                    f"{quote.source_amount} {quote.source_currency} "
                    f"to {quote.target_currency}, including "
                    f"{len(quote.payment_options)} payment option(s)."
                ),
                jurisdiction="INDIA/BRAZIL",
            )
        )

    for index, option in enumerate(
        quote.payment_options,
        start=1,
    ):
        evidence.append(
            Evidence(
                evidence_id=(
                    f"WISE-QUOTE-OPTION-{index:03d}"
                ),
                source_name="Wise API",
                source_type="PAYMENT_OPTION",
                source_url=(
                    "https://api.wise.com/2026Q3/quotes"
                ),
                observation=(
                    f"Payment option {index}: "
                    f"pay-in={option.pay_in}, "
                    f"pay-out={option.pay_out}, "
                    f"enabled={option.enabled}, "
                    f"target={option.target_amount} "
                    f"{quote.target_currency}, "
                    f"total_fee={option.total_fee} "
                    f"{option.fee_currency}. "
                    f"Disabled reason: "
                    f"{option.disabled_reason_message}"
                ),
                jurisdiction="INDIA/BRAZIL",
            )
        )

    return evidence


def collect_route_intelligence(
    route: CandidateRoute,
) -> RouteIntelligence:
    """
    Collect route intelligence for the Wise India -> Brazil route.

    Provider quote information is normalized at payment-option level.

    A route can therefore have:
      - known economics
      - multiple payment options
      - disabled payment options
      - no currently usable payment option

    These are deliberately kept distinct from final eligibility.
    """

    evidence = _collect_public_evidence()

    availability = AvailabilityIntelligence(
        status="KNOWN",
        provider="Wise",
        source_country="India",
        destination_country="Brazil",
        source_currency="INR",
        destination_currency="BRL",
        funding_method="PERSONAL_INDIAN_BANK_ACCOUNT_OR_UPI",
        delivery_method="BRAZIL_LOCAL_BANK_ACCOUNT",
        explanation=(
            "Wise publicly documents the India-to-Brazil corridor, "
            "Indian funding requirements and Brazilian bank-account delivery."
        ),
    )

    fx = FXIntelligence(
        status="UNKNOWN",
        reference_rate=0.05405,
        reference_rate_source="Wise INR/BRL Currency Converter",
        reference_rate_type="MID_MARKET",
        execution_rate=None,
        execution_rate_source=None,
        base_currency="INR",
        quote_currency="BRL",
        explanation=(
            "A current reference mid-market rate is available, but the "
            "transaction-specific Wise execution rate has not yet been captured."
        ),
    )

    fees = FeeIntelligence(
        status="UNKNOWN",
        transfer_fee=None,
        tax=None,
        fx_spread=None,
        network_fee=None,
        other_fee=None,
        currency="INR",
        published_example_amount=80000.0,
        published_example_fee=2092.07,
        published_example_currency="INR",
        explanation=(
            "Wise publishes an example fee for a different transaction. "
            "Transaction-specific economics will be taken from the "
            "selected provider payment option."
        ),
    )

    settlement = SettlementIntelligence(
        status="KNOWN",
        estimated_delivery_time="PROVIDER_ESTIMATE_AVAILABLE",
        settlement_method="BRAZIL_LOCAL_BANK_ACCOUNT",
        explanation=(
            "Wise publishes route-level delivery estimates and states "
            "that actual timing depends on the funding method."
        ),
    )

    quote = request_wise_quote(
        source_currency=route.source.currency,
        target_currency=route.destination.currency,
        source_amount=100000.0,
    )

    evidence.extend(
        _collect_wise_quote_evidence(quote)
    )

    payment_options = [
        _convert_payment_option(option)
        for option in quote.payment_options
    ]

    # The selected option is the option whose economics feed the
    # route-level summary. Operational availability is retained
    # separately in payment_options.
    selected_option = None

    if payment_options:
        preferred = [
            option
            for option in payment_options
            if option.pay_in == quote.preferred_pay_in
        ]

        enabled_preferred = [
            option
            for option in preferred
            if option.enabled
        ]

        if enabled_preferred:
            selected_option = enabled_preferred[0]
        elif preferred:
            selected_option = preferred[0]
        else:
            enabled_options = [
                option
                for option in payment_options
                if option.enabled
            ]

            if enabled_options:
                selected_option = enabled_options[0]
            else:
                selected_option = payment_options[0]

    if quote.status == "KNOWN":

        if quote.execution_rate is not None:
            fx = FXIntelligence(
                status="KNOWN",
                reference_rate=0.05405,
                reference_rate_source="Wise INR/BRL Currency Converter",
                reference_rate_type="MID_MARKET",
                execution_rate=quote.execution_rate,
                execution_rate_source="Wise API transaction quote",
                base_currency=route.source.currency,
                quote_currency=route.destination.currency,
                explanation=(
                    "Wise returned a transaction-specific execution rate "
                    "for the current quote."
                ),
            )

        if selected_option is not None:

            if (
                selected_option.transfer_fee is not None
                or selected_option.tax is not None
                or selected_option.total_fee is not None
            ):
                fees = FeeIntelligence(
                    status="KNOWN",
                    transfer_fee=selected_option.transfer_fee,
                    tax=selected_option.tax,
                    fx_spread=None,
                    network_fee=None,
                    other_fee=None,
                    currency=(
                        selected_option.fee_currency
                        or "INR"
                    ),
                    published_example_amount=80000.0,
                    published_example_fee=2092.07,
                    published_example_currency="INR",
                    explanation=(
                        "Transaction-specific fee information was "
                        "returned by the selected Wise payment option. "
                        "FX spread remains UNKNOWN unless explicitly "
                        "supported by provider data."
                    ),
                )

            if (
                selected_option.estimated_delivery
                or selected_option.formatted_estimated_delivery
            ):
                settlement = SettlementIntelligence(
                    status="KNOWN",
                    estimated_delivery_time=(
                        selected_option.estimated_delivery
                        or selected_option.formatted_estimated_delivery
                    ),
                    settlement_method=(
                        selected_option.pay_out
                        or "BRAZIL_LOCAL_BANK_ACCOUNT"
                    ),
                    explanation=(
                        "Transaction-specific delivery information "
                        "was returned by the selected Wise payment option."
                    ),
                )

    complete = (
        availability.status == "KNOWN"
        and fx.execution_rate is not None
        and fees.transfer_fee is not None
        and settlement.status == "KNOWN"
        and selected_option is not None
        and selected_option.enabled
    )

    data_completeness = (
        "COMPLETE"
        if complete
        else "INCOMPLETE"
    )

    return RouteIntelligence(
        route_id=route.route_id,
        availability=availability,
        fx=fx,
        fees=fees,
        settlement=settlement,
        data_completeness=data_completeness,
        payment_options=payment_options,
        evidence=evidence,
    )
