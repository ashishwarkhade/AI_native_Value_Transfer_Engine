import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


WISE_API_BASE_URL = os.getenv(
    "WISE_API_BASE_URL",
    "https://api.wise.com/2026Q3",
)


@dataclass(frozen=True)
class WisePaymentOption:
    pay_in: Optional[str] = None
    pay_out: Optional[str] = None

    enabled: bool = False

    disabled_reason_code: Optional[str] = None
    disabled_reason_message: Optional[str] = None

    source_amount: Optional[float] = None
    target_amount: Optional[float] = None

    execution_rate: Optional[float] = None

    transfer_fee: Optional[float] = None
    tax: Optional[float] = None
    total_fee: Optional[float] = None
    fee_currency: Optional[str] = None

    estimated_delivery: Optional[str] = None
    formatted_estimated_delivery: Optional[str] = None

    fee_percentage: Optional[float] = None


@dataclass(frozen=True)
class WiseQuoteResult:
    status: str

    quote_id: Optional[str] = None

    source_currency: Optional[str] = None
    target_currency: Optional[str] = None

    source_amount: Optional[float] = None
    target_amount: Optional[float] = None

    execution_rate: Optional[float] = None

    transfer_fee: Optional[float] = None
    tax: Optional[float] = None
    total_fee: Optional[float] = None
    fee_currency: Optional[str] = None

    estimated_delivery: Optional[str] = None

    preferred_pay_in: Optional[str] = None
    pay_out: Optional[str] = None

    payment_options: List[WisePaymentOption] = field(
        default_factory=list
    )

    explanation: str = ""

    raw_response: Optional[Dict[str, Any]] = None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_value_amount(
    value_object: Optional[Dict[str, Any]],
) -> Optional[float]:
    if not value_object:
        return None

    return _to_float(value_object.get("amount"))


def _parse_payment_option(
    option: Dict[str, Any],
) -> WisePaymentOption:

    price = option.get("price") or {}
    price_total = price.get("total") or {}
    price_total_value = price_total.get("value") or {}

    transfer_fee = None
    tax = None

    # Wise documents price.items as the detailed fee/tax breakdown.
    for item in price.get("items") or []:
        item_type = str(
            item.get("type", "")
        ).upper()

        label = str(
            item.get("label", "")
        ).lower()

        value = item.get("value") or {}
        amount = _extract_value_amount(value)

        if amount is None:
            continue

        if item_type == "TRANSFERWISE":
            transfer_fee = amount

        elif (
            item_type == "BRL_TAX"
            or "iof" in label
            or "tax" in label
        ):
            tax = amount

    disabled_reason = option.get("disabledReason") or {}

    return WisePaymentOption(
        pay_in=option.get("payIn"),
        pay_out=option.get("payOut"),
        enabled=not bool(option.get("disabled", False)),
        disabled_reason_code=disabled_reason.get("code"),
        disabled_reason_message=disabled_reason.get("message"),
        source_amount=_to_float(option.get("sourceAmount")),
        target_amount=_to_float(option.get("targetAmount")),
        execution_rate=None,
        transfer_fee=transfer_fee,
        tax=tax,
        total_fee=_extract_value_amount(price_total_value),
        fee_currency=price_total_value.get("currency"),
        estimated_delivery=option.get("estimatedDelivery"),
        formatted_estimated_delivery=option.get(
            "formattedEstimatedDelivery"
        ),
        fee_percentage=_to_float(
            option.get("feePercentage")
        ),
    )


def _select_preferred_option(
    options: List[WisePaymentOption],
    preferred_pay_in: Optional[str],
) -> Optional[WisePaymentOption]:
    """
    Prefer an enabled option matching the requested pay-in method.

    If none is enabled, retain a matching disabled option so the
    engine can explain why the provider quote is not operationally
    usable.

    If no requested method matches, prefer the first enabled option.
    Otherwise retain the first returned option.
    """

    if preferred_pay_in:
        matching = [
            option
            for option in options
            if option.pay_in == preferred_pay_in
        ]

        enabled_matching = [
            option
            for option in matching
            if option.enabled
        ]

        if enabled_matching:
            return enabled_matching[0]

        if matching:
            return matching[0]

    enabled = [
        option
        for option in options
        if option.enabled
    ]

    if enabled:
        return enabled[0]

    return options[0] if options else None


def request_wise_quote(
    source_currency: str,
    target_currency: str,
    source_amount: float,
    profile_id: Optional[str] = None,
    token: Optional[str] = None,
    payment_metadata: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = 20,
) -> WiseQuoteResult:

    token = token or os.getenv("WISE_API_TOKEN")
    profile_id = profile_id or os.getenv("WISE_PROFILE_ID")

    if profile_id and token:
        endpoint = (
            f"{WISE_API_BASE_URL}/profiles/"
            f"{profile_id}/quotes"
        )
        quote_mode = "AUTHENTICATED"
    else:
        endpoint = f"{WISE_API_BASE_URL}/quotes"
        quote_mode = "UNAUTHENTICATED"

    body: Dict[str, Any] = {
        "sourceCurrency": source_currency,
        "targetCurrency": target_currency,
        "sourceAmount": source_amount,
        "targetAmount": None,
        "targetAccount": None,
        "payOut": "BANK_TRANSFER",
        "preferredPayIn": "BANK_TRANSFER",
    }

    if payment_metadata:
        body["paymentMetadata"] = payment_metadata

    request_data = json.dumps(body).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(
        endpoint,
        data=request_data,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout_seconds,
        ) as response:
            response_body = response.read().decode("utf-8")
            parsed = json.loads(response_body)

    except urllib.error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8")
        except Exception:
            error_body = ""

        return WiseQuoteResult(
            status="PROVIDER_ERROR",
            explanation=(
                f"Wise returned HTTP {exc.code}. "
                f"Response: {error_body[:500]}"
            ),
        )

    except urllib.error.URLError as exc:
        return WiseQuoteResult(
            status="UNAVAILABLE",
            explanation=f"Unable to reach Wise API: {exc.reason}",
        )

    except TimeoutError:
        return WiseQuoteResult(
            status="UNAVAILABLE",
            explanation="Wise API request timed out.",
        )

    except json.JSONDecodeError:
        return WiseQuoteResult(
            status="PROVIDER_ERROR",
            explanation="Wise returned a non-JSON response.",
        )

    raw_options = parsed.get("paymentOptions") or []

    payment_options = [
        _parse_payment_option(option)
        for option in raw_options
    ]

    preferred_pay_in = parsed.get("preferredPayIn")

    selected_option = _select_preferred_option(
        payment_options,
        preferred_pay_in,
    )

    # The top-level quote rate applies to the quote.
    execution_rate = _to_float(
        parsed.get("rate")
    )

    if selected_option is not None:
        selected_option = WisePaymentOption(
            pay_in=selected_option.pay_in,
            pay_out=selected_option.pay_out,
            enabled=selected_option.enabled,
            disabled_reason_code=(
                selected_option.disabled_reason_code
            ),
            disabled_reason_message=(
                selected_option.disabled_reason_message
            ),
            source_amount=selected_option.source_amount,
            target_amount=selected_option.target_amount,
            execution_rate=execution_rate,
            transfer_fee=selected_option.transfer_fee,
            tax=selected_option.tax,
            total_fee=selected_option.total_fee,
            fee_currency=selected_option.fee_currency,
            estimated_delivery=selected_option.estimated_delivery,
            formatted_estimated_delivery=(
                selected_option.formatted_estimated_delivery
            ),
            fee_percentage=selected_option.fee_percentage,
        )

        # Replace the selected object in the list so it also carries
        # the transaction-specific execution rate.
        payment_options = [
            selected_option
            if option.pay_in == selected_option.pay_in
            and option.pay_out == selected_option.pay_out
            and option.source_amount == selected_option.source_amount
            and option.target_amount == selected_option.target_amount
            else option
            for option in payment_options
        ]

    source_amount_response = _to_float(
        parsed.get("sourceAmount")
    )

    return WiseQuoteResult(
        status="KNOWN",
        quote_id=parsed.get("id"),
        source_currency=parsed.get(
            "sourceCurrency",
            source_currency,
        ),
        target_currency=parsed.get(
            "targetCurrency",
            target_currency,
        ),
        source_amount=source_amount_response,
        target_amount=(
            selected_option.target_amount
            if selected_option
            else _to_float(parsed.get("targetAmount"))
        ),
        execution_rate=execution_rate,
        transfer_fee=(
            selected_option.transfer_fee
            if selected_option
            else None
        ),
        tax=(
            selected_option.tax
            if selected_option
            else None
        ),
        total_fee=(
            selected_option.total_fee
            if selected_option
            else None
        ),
        fee_currency=(
            selected_option.fee_currency
            if selected_option
            else None
        ),
        estimated_delivery=(
            selected_option.estimated_delivery
            if selected_option
            else None
        ),
        preferred_pay_in=preferred_pay_in,
        pay_out=parsed.get("payOut"),
        payment_options=payment_options,
        explanation=(
            f"Wise returned a {quote_mode.lower()} quote with "
            f"{len(payment_options)} payment option(s). "
            "Pricing is taken from the provider's paymentOptions "
            "price breakdown; disabled options remain distinguishable "
            "from operationally available options."
        ),
        raw_response=parsed,
    )
