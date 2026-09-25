from intent.value_transfer_intent import create_india_brazil_intent
from intelligence.route_intelligence import collect_route_intelligence
from route_discovery.route_discovery import discover_routes


def main():
    intent = create_india_brazil_intent()
    routes = discover_routes(intent)

    print("\n=== ROUTE INTELLIGENCE ===")

    assert len(routes) == 1

    for route in routes:
        intelligence = collect_route_intelligence(route)

        print(f"\nRoute: {intelligence.route_id}")

        print("\nAvailability:")
        print(f"  Status: {intelligence.availability.status}")
        print(f"  Provider: {intelligence.availability.provider}")
        print(f"  Source: {intelligence.availability.source_country}")
        print(
            f"  Destination: "
            f"{intelligence.availability.destination_country}"
        )
        print(
            f"  Currency: "
            f"{intelligence.availability.destination_currency}"
        )
        print(f"  Funding: {intelligence.availability.funding_method}")
        print(f"  Delivery: {intelligence.availability.delivery_method}")

        print("\nFX:")
        print(f"  Status: {intelligence.fx.status}")
        print(f"  Reference rate: {intelligence.fx.reference_rate}")
        print(
            f"  Reference rate type: "
            f"{intelligence.fx.reference_rate_type}"
        )
        print(f"  Execution rate: {intelligence.fx.execution_rate}")
        print(
            f"  Execution rate source: "
            f"{intelligence.fx.execution_rate_source}"
        )

        print("\nFees:")
        print(f"  Status: {intelligence.fees.status}")
        print(f"  Transfer fee: {intelligence.fees.transfer_fee}")
        print(f"  Tax: {intelligence.fees.tax}")
        print(f"  FX spread: {intelligence.fees.fx_spread}")
        print(
            f"  Published example amount: "
            f"{intelligence.fees.published_example_amount}"
        )
        print(
            f"  Published example fee: "
            f"{intelligence.fees.published_example_fee}"
        )

        print("\nPayment Options:")

        for option in intelligence.payment_options:
            print(f"  Pay-in: {option.pay_in}")
            print(f"  Pay-out: {option.pay_out}")
            print(f"  Enabled: {option.enabled}")
            print(f"  Source amount: {option.source_amount}")
            print(f"  Target amount: {option.target_amount}")
            print(f"  Transfer fee: {option.transfer_fee}")
            print(f"  Tax: {option.tax}")
            print(f"  Total fee: {option.total_fee}")
            print(
                f"  Delivery: "
                f"{option.formatted_estimated_delivery}"
            )
            print(
                f"  Disabled reason: "
                f"{option.disabled_reason_message}"
            )
            print()

        print("\nSettlement:")
        print(f"  Status: {intelligence.settlement.status}")
        print(
            f"  Delivery estimate: "
            f"{intelligence.settlement.estimated_delivery_time}"
        )
        print(
            f"  Method: "
            f"{intelligence.settlement.settlement_method}"
        )

        print("\nData completeness:")
        print(f"  {intelligence.data_completeness}")

        print("\nEvidence:")

        for evidence in intelligence.evidence:
            print(f"  Evidence ID: {evidence.evidence_id}")
            print(f"  Source: {evidence.source_name}")
            print(f"  Type: {evidence.source_type}")
            print(f"  URL: {evidence.source_url}")
            print(f"  Observation: {evidence.observation}")

        # --------------------------------------------------------
        # Assertions
        # --------------------------------------------------------

        assert intelligence.route_id == "R-IN-BR-WISE-001"

        # --------------------------------------------------------
        # Availability
        # --------------------------------------------------------

        assert intelligence.availability.status == "KNOWN"
        assert intelligence.availability.provider == "Wise"
        assert intelligence.availability.source_country == "India"
        assert intelligence.availability.destination_country == "Brazil"
        assert intelligence.availability.source_currency == "INR"
        assert intelligence.availability.destination_currency == "BRL"

        # --------------------------------------------------------
        # FX
        # --------------------------------------------------------

        # Reference market information remains available.
        assert intelligence.fx.reference_rate == 0.05405
        assert intelligence.fx.reference_rate_type == "MID_MARKET"

        # Live provider execution rate must exist, but must NOT be
        # hard-coded because Wise quotes are dynamic.
        assert intelligence.fx.execution_rate is not None
        assert intelligence.fx.execution_rate > 0
        assert (
            intelligence.fx.execution_rate_source
            == "Wise API transaction quote"
        )
        assert intelligence.fx.status == "KNOWN"

        # --------------------------------------------------------
        # Payment options
        # --------------------------------------------------------

        assert len(intelligence.payment_options) >= 2

        bank_transfer_options = [
            option
            for option in intelligence.payment_options
            if option.pay_in == "BANK_TRANSFER"
        ]

        assert len(bank_transfer_options) == 1

        bank_transfer = bank_transfer_options[0]

        assert bank_transfer.pay_out == "BANK_TRANSFER"

        # The live Wise response currently reports this option
        # as disabled.
        assert bank_transfer.enabled is False

        assert (
            bank_transfer.disabled_reason_code
            == "error.payInmethod.disabled"
        )

        # The source amount is our transaction intent.
        assert bank_transfer.source_amount == float(intent.amount)

        # Live quote values must exist but should not be asserted
        # against a fixed number.
        assert bank_transfer.target_amount is not None
        assert bank_transfer.target_amount > 0

        assert bank_transfer.transfer_fee is not None
        assert bank_transfer.transfer_fee >= 0

        assert bank_transfer.tax is not None
        assert bank_transfer.tax >= 0

        assert bank_transfer.total_fee is not None
        assert bank_transfer.total_fee >= 0

        assert bank_transfer.fee_currency == "INR"

        # The fee breakdown should reconcile to the provider total.
        assert abs(
            (
                bank_transfer.transfer_fee
                + bank_transfer.tax
            )
            - bank_transfer.total_fee
        ) < 0.01

        # --------------------------------------------------------
        # Balance option
        # --------------------------------------------------------

        balance_options = [
            option
            for option in intelligence.payment_options
            if option.pay_in == "BALANCE"
        ]

        assert len(balance_options) == 1

        balance = balance_options[0]

        assert balance.pay_out == "BANK_TRANSFER"
        assert balance.enabled is False

        assert balance.source_amount == float(intent.amount)

        assert balance.target_amount is not None
        assert balance.target_amount > 0

        assert balance.transfer_fee is not None
        assert balance.transfer_fee >= 0

        assert balance.tax is not None
        assert balance.tax >= 0

        assert balance.total_fee is not None
        assert balance.total_fee >= 0

        assert balance.fee_currency == "INR"

        assert abs(
            (
                balance.transfer_fee
                + balance.tax
            )
            - balance.total_fee
        ) < 0.01

        # --------------------------------------------------------
        # Route-level fee summary
        # --------------------------------------------------------

        # The preferred BANK_TRANSFER option supplies the route-level
        # transaction economics.
        assert intelligence.fees.status == "KNOWN"

        assert intelligence.fees.transfer_fee is not None
        assert intelligence.fees.transfer_fee >= 0

        assert intelligence.fees.tax is not None
        assert intelligence.fees.tax >= 0

        # We deliberately do not fabricate an FX spread.
        assert intelligence.fees.fx_spread is None

        # Published example remains separate evidence.
        assert (
            intelligence.fees.published_example_amount
            == 80000.0
        )
        assert (
            intelligence.fees.published_example_fee
            == 2092.07
        )

        # --------------------------------------------------------
        # Settlement
        # --------------------------------------------------------

        assert intelligence.settlement.status == "KNOWN"

        assert (
            intelligence.settlement.settlement_method
            == "BANK_TRANSFER"
        )

        assert (
            intelligence.settlement.estimated_delivery_time
            is not None
        )

        # --------------------------------------------------------
        # Completeness
        # --------------------------------------------------------

        # Economics are known, but the preferred payment option is
        # disabled, so the route is not operationally complete.
        assert intelligence.data_completeness == "INCOMPLETE"

        # Public evidence + live quote + payment-option evidence.
        assert len(intelligence.evidence) >= 8

    print("\nPASS: Candidate Routes -> Intelligence")


if __name__ == "__main__":
    main()
