from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Evidence:
    """
    Evidence supporting an intelligence observation.
    """

    evidence_id: str
    source_name: str
    source_type: str
    source_url: str
    observation: str
    jurisdiction: Optional[str] = None
    observed_at: Optional[str] = None


@dataclass(frozen=True)
class AvailabilityIntelligence:
    status: str
    provider: Optional[str] = None
    source_country: Optional[str] = None
    destination_country: Optional[str] = None
    source_currency: Optional[str] = None
    destination_currency: Optional[str] = None
    funding_method: Optional[str] = None
    delivery_method: Optional[str] = None
    explanation: str = ""


@dataclass(frozen=True)
class PaymentOptionIntelligence:
    """
    Provider-specific payment option returned by a quote.

    Economic availability and operational availability are kept
    separate. A provider can return pricing for an option that is
    currently disabled.
    """

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

    explanation: str = ""


@dataclass(frozen=True)
class FXIntelligence:
    """
    FX intelligence deliberately separates reference-market data
    from transaction-specific execution data.
    """

    status: str

    # Reference market rate
    reference_rate: Optional[float] = None
    reference_rate_source: Optional[str] = None
    reference_rate_type: Optional[str] = None

    # Provider / transaction-specific rate
    execution_rate: Optional[float] = None
    execution_rate_source: Optional[str] = None

    base_currency: Optional[str] = None
    quote_currency: Optional[str] = None

    explanation: str = ""


@dataclass(frozen=True)
class FeeIntelligence:
    status: str

    # Exact transaction economics
    transfer_fee: Optional[float] = None
    tax: Optional[float] = None
    fx_spread: Optional[float] = None
    network_fee: Optional[float] = None
    other_fee: Optional[float] = None

    currency: Optional[str] = None

    # Published provider example that is NOT necessarily
    # applicable to the current transaction.
    published_example_amount: Optional[float] = None
    published_example_fee: Optional[float] = None
    published_example_currency: Optional[str] = None

    explanation: str = ""


@dataclass(frozen=True)
class SettlementIntelligence:
    status: str
    estimated_delivery_time: Optional[str] = None
    settlement_method: Optional[str] = None
    explanation: str = ""


@dataclass(frozen=True)
class RouteIntelligence:
    route_id: str
    availability: AvailabilityIntelligence
    fx: FXIntelligence
    fees: FeeIntelligence
    settlement: SettlementIntelligence
    data_completeness: str

    # Provider may return several ways to fund/deliver the same route.
    payment_options: List[PaymentOptionIntelligence] = field(
        default_factory=list
    )

    evidence: List[Evidence] = field(default_factory=list)
