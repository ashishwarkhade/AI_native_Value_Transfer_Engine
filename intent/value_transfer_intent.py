from models.contracts import ValueTransferIntent


def create_india_brazil_intent() -> ValueTransferIntent:
    """
    First vertical-pass transaction for the Value Transfer Engine.
    """

    return ValueTransferIntent(
        intent_id="VTI-IN-BR-001",
        from_country="India",
        to_country="Brazil",
        amount=100000,
        source_currency="INR",
        destination_currency="BRL",
        required_delivery_time="24h",
    )
