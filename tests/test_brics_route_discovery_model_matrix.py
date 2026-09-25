import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from ai.model_interface import AIModel
from ai.ollama_ai import OllamaAI
from ai.nebius_ai import NebiusAI
from ai.tokenharbor_ai import TokenHarborAI
from intent.value_transfer_intent import ValueTransferIntent
from route_discovery.route_discovery_agent import RouteDiscoveryAgent


# ---------------------------------------------------------------------------
# BRICS COUNTRY UNIVERSE
# ---------------------------------------------------------------------------

BRICS_COUNTRIES = [
    {
        "country": "Brazil",
        "code": "BR",
        "currency": "BRL",
        "category": "MEMBER",
    },
    {
        "country": "Russia",
        "code": "RU",
        "currency": "RUB",
        "category": "MEMBER",
    },
    {
        "country": "India",
        "code": "IN",
        "currency": "INR",
        "category": "MEMBER",
    },
    {
        "country": "China",
        "code": "CN",
        "currency": "CNY",
        "category": "MEMBER",
    },
    {
        "country": "South Africa",
        "code": "ZA",
        "currency": "ZAR",
        "category": "MEMBER",
    },
    {
        "country": "Saudi Arabia",
        "code": "SA",
        "currency": "SAR",
        "category": "MEMBER",
    },
    {
        "country": "Egypt",
        "code": "EG",
        "currency": "EGP",
        "category": "MEMBER",
    },
    {
        "country": "United Arab Emirates",
        "code": "AE",
        "currency": "AED",
        "category": "MEMBER",
    },
    {
        "country": "Ethiopia",
        "code": "ET",
        "currency": "ETB",
        "category": "MEMBER",
    },
    {
        "country": "Iran",
        "code": "IR",
        "currency": "IRR",
        "category": "MEMBER",
    },
    {
        "country": "Indonesia",
        "code": "ID",
        "currency": "IDR",
        "category": "MEMBER",
    },
    {
        "country": "Belarus",
        "code": "BY",
        "currency": "BYN",
        "category": "PARTNER",
    },
    {
        "country": "Bolivia",
        "code": "BO",
        "currency": "BOB",
        "category": "PARTNER",
    },
    {
        "country": "Cuba",
        "code": "CU",
        "currency": "CUP",
        "category": "PARTNER",
    },
    {
        "country": "Kazakhstan",
        "code": "KZ",
        "currency": "KZT",
        "category": "PARTNER",
    },
    {
        "country": "Malaysia",
        "code": "MY",
        "currency": "MYR",
        "category": "PARTNER",
    },
    {
        "country": "Nigeria",
        "code": "NG",
        "currency": "NGN",
        "category": "PARTNER",
    },
    {
        "country": "Thailand",
        "code": "TH",
        "currency": "THB",
        "category": "PARTNER",
    },
    {
        "country": "Uganda",
        "code": "UG",
        "currency": "UGX",
        "category": "PARTNER",
    },
    {
        "country": "Uzbekistan",
        "code": "UZ",
        "currency": "UZS",
        "category": "PARTNER",
    },
    {
        "country": "Vietnam",
        "code": "VN",
        "currency": "VND",
        "category": "PARTNER",
    },
]


# ---------------------------------------------------------------------------
# MATRIX CONFIGURATION
# ---------------------------------------------------------------------------

MATRIX_VERSION = "BRICS-21-MEMBER-PARTNER-V2-SWIFT-SEMANTIC"
ROUND_NAME = "ROUND9_NO_SWIFT_SEMANTIC"

OUTPUT_DIR = Path("test_results")

DEFAULT_AMOUNT = 100000
DEFAULT_DELIVERY_TIME = ""
DEFAULT_PAUSE_SECONDS = 1
DEFAULT_TIMEOUT_SECONDS = 600


# ---------------------------------------------------------------------------
# RECORDING / EXPERIMENT-CONTROLLED AI
# ---------------------------------------------------------------------------

class RecordingAI(AIModel):

    def __init__(
        self,
        wrapped_ai: AIModel,
        *,
        exclude_swift: bool = False,
    ):
        self.wrapped_ai = wrapped_ai
        self.exclude_swift = exclude_swift
        self.calls = []

    def _build_system_prompt(
        self,
        system_prompt: str,
    ) -> str:

        if not self.exclude_swift:
            return system_prompt

        experiment_constraint = """

EXPERIMENT CONSTRAINT — SWIFT OFF

SWIFT is excluded from this route-discovery experiment.

For every candidate route:

1. RAIL
   The selected "rail" must NOT be SWIFT.

2. TRANSFER PATH
   No step in "transfer_path" may use SWIFT as the messaging
   network, transfer mechanism, intermediary network, or
   settlement path.

3. ROUTE REQUIREMENTS
   "route_requirements" must NOT require SWIFT access,
   SWIFT membership, SWIFT codes, SWIFT-enabled banks,
   or SWIFT network connectivity.

4. CROSS-FIELD CONSISTENCY
   Do not select SWIFT in one field and describe it as
   excluded, unused, unavailable, or replaced in another field.

5. SWIFT MAY BE MENTIONED ONLY AS NEGATIVE/CONTEXTUAL TEXT
   A route may mention SWIFT when explicitly stating that
   SWIFT is not used, excluded, unavailable, or being
   replaced by another mechanism. Such a mention must never
   make SWIFT the selected rail or an operational transfer step.

6. ALTERNATIVE DISCOVERY
   Discover alternative candidate mechanisms available for
   the source and destination corridor. Do not generate a
   SWIFT route and relabel it as non-SWIFT.

This is a route-discovery experiment. Do not invent provider
capabilities, availability, pricing, FX rates, settlement
capabilities, regulatory approval, or other facts.

Candidate routes remain candidates and require downstream
investigation and evaluation.
"""

        return (
            system_prompt.rstrip()
            + "\n"
            + experiment_constraint.strip()
            + "\n"
        )

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        effective_system_prompt = self._build_system_prompt(
            system_prompt
        )

        response = self.wrapped_ai.generate(
            effective_system_prompt,
            user_prompt,
        )

        self.calls.append(
            {
                "system_prompt": effective_system_prompt,
                "user_prompt": user_prompt,
                "response": response,
            }
        )

        return response

    @property
    def last_response(self):

        if not self.calls:
            return None

        return self.calls[-1]["response"]


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def build_intent(
    source: dict,
    destination: dict,
    sequence: int,
) -> ValueTransferIntent:

    return ValueTransferIntent(
        intent_id=(
            f"VTI-BRICS-"
            f"{source['code']}-"
            f"{destination['code']}-"
            f"{sequence:03d}"
        ),
        from_country=source["country"],
        to_country=destination["country"],
        amount=DEFAULT_AMOUNT,
        source_currency=source["currency"],
        destination_currency=destination["currency"],
        required_delivery_time=DEFAULT_DELIVERY_TIME,
    )


def route_to_dict(route):

    return {
        "route_id": route.route_id,
        "rail": route.rail,
        "source": {
            "country": route.source.country,
            "currency": route.source.currency,
        },
        "destination": {
            "country": route.destination.country,
            "currency": route.destination.currency,
        },
        "funding_method": route.funding_method,
        "transfer_path": list(route.transfer_path),
        "delivery_method": route.delivery_method,
        "corridor_availability": route.corridor_availability,
        "route_requirements": list(route.route_requirements),
    }


def validate_swift_route(route) -> dict:
    """
    Validate whether a candidate route operationally uses SWIFT.

    The validator is semantic rather than a simple substring filter:
    negative/contextual references such as "non-SWIFT" or
    "SWIFT is not used" are not violations.

    Returns:
        {
            "violation": bool,
            "fields": [...],
            "details": {
                "rail": [...],
                "transfer_path": [...],
                "route_requirements": [...]
            }
        }
    """
    import re

    field_values = {
        "rail": [route.rail],
        "transfer_path": list(route.transfer_path),
        "route_requirements": list(route.route_requirements),
    }

    negative_patterns = [
        r"\bnon[- ]swift\b",
        r"\bno\s+swift\b",
        r"\bwithout\s+swift\b",
        r"\bexcluding\s+swift\b",
        r"\bexclude\s+swift\b",
        r"\bswift\s+excluded\b",
        r"\bswift[- ]free\b",
        r"\bswift\s+not\s+used\b",
        r"\bswift\s+is\s+not\s+used\b",
        r"\bdoes\s+not\s+use\s+swift\b",
        r"\bdoesn['’]t\s+use\s+swift\b",
        r"\bnot\s+using\s+swift\b",
        r"\bnot\s+use\s+swift\b",
        r"\bnot\s+swift\b",
        r"\balternative\s+to\s+swift\b",
        r"\binstead\s+of\s+swift\b",
        r"\bother\s+than\s+swift\b",
        r"\breplace(?:d|s)?\s+swift\b",
        r"\breplacing\s+swift\b",
    ]

    details = {}
    violating_fields = []

    for field_name, values in field_values.items():
        field_matches = []

        for value in values:
            if value is None:
                continue

            original = str(value)
            text = original.lower()

            for pattern in negative_patterns:
                text = re.sub(pattern, "", text)

            if re.search(r"\bswift\b", text):
                field_matches.append(original)

        if field_matches:
            details[field_name] = field_matches
            violating_fields.append(field_name)

    return {
        "violation": bool(violating_fields),
        "fields": violating_fields,
        "details": details,
    }


def route_contains_swift(route) -> bool:
    """
    Backward-compatible boolean wrapper around validate_swift_route().
    """
    return validate_swift_route(route)["violation"]

def find_swift_routes(routes):

    violations = []

    for route in routes:
        validation = validate_swift_route(route)

        if validation["violation"]:
            violations.append(
                {
                    "route_id": route.route_id,
                    "fields": validation["fields"],
                    "details": validation["details"],
                }
            )

    return violations


def create_empty_output(
    total_corridors: int,
    model_name: str,
    provider: str,
    exclude_swift: bool,
):

    return {
        "test": "BRICS_ROUTE_DISCOVERY_MODEL_MATRIX",
        "matrix_version": MATRIX_VERSION,
        "round": ROUND_NAME,
        "provider": provider,
        "model": model_name,
        "constraints": {
            "swift_excluded": exclude_swift,
        },
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "countries": BRICS_COUNTRIES,
        "country_count": len(BRICS_COUNTRIES),
        "member_count": sum(
            1
            for country in BRICS_COUNTRIES
            if country["category"] == "MEMBER"
        ),
        "partner_count": sum(
            1
            for country in BRICS_COUNTRIES
            if country["category"] == "PARTNER"
        ),
        "total_directed_corridors": total_corridors,
        "default_amount": DEFAULT_AMOUNT,
        "default_delivery_time": DEFAULT_DELIVERY_TIME,
        "results": [],
    }


def output_file_for_model(
    model_name: str,
    provider: str,
    exclude_swift: bool,
) -> Path:

    safe_model_name = (
        model_name
        .replace(":", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )

    if exclude_swift:
        filename = (
            f"brics_21_route_discovery_"
            f"{ROUND_NAME.lower()}_"
            f"{provider}_"
            f"{safe_model_name}.json"
        )
    else:
        filename = (
            f"brics_21_route_discovery_"
            f"{provider}_"
            f"{safe_model_name}.json"
        )

    return OUTPUT_DIR / filename


def load_existing_output(
    output_file: Path,
    model_name: str,
    provider: str,
    exclude_swift: bool,
):

    if not output_file.exists():
        return None

    try:
        data = json.loads(
            output_file.read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return None

    if data.get("matrix_version") != MATRIX_VERSION:
        return None

    if data.get("model") != model_name:
        return None

    if data.get("provider") != provider:
        return None

    constraints = data.get(
        "constraints",
        {},
    )

    if constraints.get(
        "swift_excluded",
        False,
    ) != exclude_swift:
        return None

    return data


def save_output(
    output_file: Path,
    output,
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def build_result_index(output):

    return {
        result["intent"]["intent_id"]: result
        for result in output["results"]
    }


def build_sequence(
    source_index: int,
    destination_index: int,
    country_count: int,
) -> int:

    sequence = (
        source_index * (country_count - 1)
    )

    destination_offset = (
        destination_index
        if destination_index < source_index
        else destination_index - 1
    )

    sequence += destination_offset + 1

    return sequence


def build_ai(
    provider: str,
    model: str,
    timeout: int,
) -> AIModel:

    if provider == "ollama":
        return OllamaAI(
            model_name=model,
            timeout=timeout,
        )

    if provider == "nebius":
        return NebiusAI(
            model_name=model,
            timeout=timeout,
        )

    if provider == "tokenharbor":
        return TokenHarborAI(
            model_name=model,
            timeout=timeout,
        )

    raise ValueError(
        f"Unsupported provider: {provider}"
    )


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Run AI route discovery across all directed "
            "BRICS member/partner country corridors "
            "using Ollama or Nebius."
        )
    )

    parser.add_argument(
        "--provider",
        choices=[
           "ollama",
           "nebius",
           "tokenharbor",
        ],
        default="ollama",
        help=(
            "AI provider."
        ),
    )

    parser.add_argument(
        "--model",
        required=True,
        help=(
            "Model name. Examples: qwen3:4b, "
            "gemma3:4b, or "
            "deepseek-ai/DeepSeek-V4-Pro."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Optional maximum number of corridors "
            "to process during this execution."
        ),
    )

    parser.add_argument(
        "--pause",
        type=float,
        default=DEFAULT_PAUSE_SECONDS,
        help=(
            "Pause in seconds between model calls."
        ),
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=(
            "AI request timeout in seconds."
        ),
    )

    parser.add_argument(
        "--fresh",
        action="store_true",
        help=(
            "Ignore an existing result file and "
            "start again."
        ),
    )

    parser.add_argument(
        "--exclude-swift",
        action="store_true",
        help=(
            "Exclude SWIFT from route discovery and apply "
            "semantic SWIFT-OFF validation."
        ),
    )

    args = parser.parse_args()

    if args.limit is not None and args.limit <= 0:
        parser.error(
            "--limit must be greater than zero."
        )

    if args.pause < 0:
        parser.error(
            "--pause cannot be negative."
        )

    country_count = len(BRICS_COUNTRIES)

    total_corridors = (
        country_count *
        (country_count - 1)
    )

    output_file = output_file_for_model(
        args.model,
        args.provider,
        args.exclude_swift,
    )

    # -----------------------------------------------------------------------
    # OUTPUT / RESUME
    # -----------------------------------------------------------------------

    if args.fresh:

        output = create_empty_output(
            total_corridors,
            args.model,
            args.provider,
            args.exclude_swift,
        )

    else:

        output = load_existing_output(
            output_file,
            args.model,
            args.provider,
            args.exclude_swift,
        )

        if output is None:

            output = create_empty_output(
                total_corridors,
                args.model,
                args.provider,
                args.exclude_swift,
            )

    existing_results = build_result_index(
        output
    )

    # -----------------------------------------------------------------------
    # AI
    # -----------------------------------------------------------------------

    base_ai = build_ai(
        args.provider,
        args.model,
        args.timeout,
    )

    ai = RecordingAI(
        base_ai,
        exclude_swift=args.exclude_swift,
    )

    discovery_agent = RouteDiscoveryAgent(
        ai
    )

    # -----------------------------------------------------------------------
    # HEADER
    # -----------------------------------------------------------------------

    print()
    print("=" * 80)
    print(
        "BRICS 21-COUNTRY CROSS-BORDER "
        "ROUTE DISCOVERY MODEL MATRIX"
    )
    print("=" * 80)

    print(
        f"Round:                {ROUND_NAME}"
    )

    print(
        f"Provider:             {args.provider}"
    )

    print(
        f"Model:                {args.model}"
    )

    print(
        f"Members:              "
        f"{sum(c['category'] == 'MEMBER' for c in BRICS_COUNTRIES)}"
    )

    print(
        f"Partners:             "
        f"{sum(c['category'] == 'PARTNER' for c in BRICS_COUNTRIES)}"
    )

    print(
        f"Total countries:      {country_count}"
    )

    print(
        f"Directed corridors:   {total_corridors}"
    )

    print(
        f"SWIFT excluded:       "
        f"{args.exclude_swift}"
    )

    print(
        f"Existing results:     "
        f"{len(existing_results)}"
    )

    print(
        f"Output:               "
        f"{output_file}"
    )

    print()

    processed_this_run = 0
    stop_requested = False

    # -----------------------------------------------------------------------
    # MATRIX
    # -----------------------------------------------------------------------

    for source_index, source in enumerate(
        BRICS_COUNTRIES
    ):

        for destination_index, destination in enumerate(
            BRICS_COUNTRIES
        ):

            if source["country"] == destination["country"]:
                continue

            sequence = build_sequence(
                source_index,
                destination_index,
                country_count,
            )

            intent = build_intent(
                source,
                destination,
                sequence,
            )

            # ---------------------------------------------------------------
            # RESUME
            # ---------------------------------------------------------------

            if intent.intent_id in existing_results:
                continue

            if (
                args.limit is not None
                and processed_this_run >= args.limit
            ):
                stop_requested = True
                break

            processed_this_run += 1

            # ---------------------------------------------------------------
            # CORRIDOR
            # ---------------------------------------------------------------

            print("-" * 80)

            print(
                f"[{sequence}/{total_corridors}] "
                f"{source['country']} "
                f"({source['category']}) "
                f"-> "
                f"{destination['country']} "
                f"({destination['category']})"
            )

            print(
                f"Intent: {intent.intent_id} | "
                f"{intent.amount} "
                f"{intent.source_currency} -> "
                f"{intent.destination_currency} | "
                f"delivery={intent.required_delivery_time}"
            )

            started_at = datetime.now(
                timezone.utc
            )

            raw_ai_response = None

            try:

                routes = discovery_agent.discover(
                    intent
                )

                raw_ai_response = (
                    ai.last_response
                )

                completed_at = datetime.now(
                    timezone.utc
                )

                duration_seconds = (
                    completed_at - started_at
                ).total_seconds()

                route_records = [
                    route_to_dict(route)
                    for route in routes
                ]

                swift_route_violations = []

                if args.exclude_swift:
                    swift_route_violations = find_swift_routes(
                        routes
                    )

                result = {
                    "sequence": sequence,
                    "intent": {
                        "intent_id": intent.intent_id,
                        "from_country": (
                            intent.from_country
                        ),
                        "to_country": (
                            intent.to_country
                        ),
                        "from_category": (
                            source["category"]
                        ),
                        "to_category": (
                            destination["category"]
                        ),
                        "amount": intent.amount,
                        "source_currency": (
                            intent.source_currency
                        ),
                        "destination_currency": (
                            intent.destination_currency
                        ),
                        "required_delivery_time": (
                            intent.required_delivery_time
                        ),
                    },
                    "status": "PASS",
                    "started_at": (
                        started_at.isoformat()
                    ),
                    "completed_at": (
                        completed_at.isoformat()
                    ),
                    "duration_seconds": (
                        duration_seconds
                    ),
                    "route_count": (
                        len(route_records)
                    ),
                    "routes": route_records,
                    "raw_ai_response": (
                        raw_ai_response
                    ),
                }

                if args.exclude_swift:
                    result[
                        "experiment_validation"
                    ] = {
                        "swift_route_violation": (
                            len(swift_route_violations) > 0
                        ),
                        "swift_violation_count": (
                            len(swift_route_violations)
                        ),
                        "swift_violation_routes": (
                            swift_route_violations
                        ),
                    }

                print(
                    f"Routes discovered: "
                    f"{len(route_records)}"
                )

                print(
                    f"Duration: "
                    f"{duration_seconds:.2f}s"
                )

                if args.exclude_swift:
                    if swift_route_violations:
                        print(
                            "SWIFT CONSTRAINT VIOLATION: "
                            f"{len(swift_route_violations)} route(s)"
                        )

                        for violation in swift_route_violations:
                            print(
                                f"    {violation['route_id']} | "
                                f"fields={violation['fields']}"
                            )
                    else:
                        print(
                            "SWIFT CONSTRAINT: PASS"
                        )

                for route in routes:

                    print(
                        f"  - {route.route_id} | "
                        f"{route.rail} | "
                        f"{route.funding_method} | "
                        f"{route.delivery_method}"
                    )

            except Exception as exc:

                raw_ai_response = (
                    ai.last_response
                )

                completed_at = datetime.now(
                    timezone.utc
                )

                duration_seconds = (
                    completed_at - started_at
                ).total_seconds()

                result = {
                    "sequence": sequence,
                    "intent": {
                        "intent_id": intent.intent_id,
                        "from_country": (
                            intent.from_country
                        ),
                        "to_country": (
                            intent.to_country
                        ),
                        "from_category": (
                            source["category"]
                        ),
                        "to_category": (
                            destination["category"]
                        ),
                        "amount": intent.amount,
                        "source_currency": (
                            intent.source_currency
                        ),
                        "destination_currency": (
                            intent.destination_currency
                        ),
                        "required_delivery_time": (
                            intent.required_delivery_time
                        ),
                    },
                    "status": "ERROR",
                    "started_at": (
                        started_at.isoformat()
                    ),
                    "completed_at": (
                        completed_at.isoformat()
                    ),
                    "duration_seconds": (
                        duration_seconds
                    ),
                    "route_count": 0,
                    "routes": [],
                    "error": str(exc),
                    "raw_ai_response": (
                        raw_ai_response
                    ),
                }

                print(
                    f"ERROR: {exc}"
                )

                print(
                    f"Duration: "
                    f"{duration_seconds:.2f}s"
                )

                if raw_ai_response:
                    print(
                        "Raw AI response preserved."
                    )

            # ---------------------------------------------------------------
            # SAVE IMMEDIATELY
            # ---------------------------------------------------------------

            output["results"].append(
                result
            )

            existing_results[
                intent.intent_id
            ] = result

            save_output(
                output_file,
                output,
            )

            if args.pause > 0:
                time.sleep(
                    args.pause
                )

        if stop_requested:
            break

    # -----------------------------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------------------------

    passed = sum(
        1
        for result in output["results"]
        if result["status"] == "PASS"
    )

    failed = sum(
        1
        for result in output["results"]
        if result["status"] == "ERROR"
    )

    total_routes = sum(
        result["route_count"]
        for result in output["results"]
    )

    completed = len(
        output["results"]
    )

    remaining = (
        total_corridors - completed
    )

    durations = [
        result["duration_seconds"]
        for result in output["results"]
        if "duration_seconds" in result
    ]

    total_duration_seconds = sum(
        durations
    )

    average_duration_seconds = (
        total_duration_seconds / len(durations)
        if durations
        else 0
    )

    swift_violation_corridors = 0
    swift_violation_routes = 0

    if args.exclude_swift:

        swift_violation_corridors = sum(
            1
            for result in output["results"]
            if result.get(
                "experiment_validation",
                {},
            ).get(
                "swift_route_violation",
                False,
            )
        )

        swift_violation_routes = sum(
            result.get(
                "experiment_validation",
                {},
            ).get(
                "swift_violation_count",
                0,
            )
            for result in output["results"]
        )

    output["summary"] = {
        "completed_corridors": completed,
        "remaining_corridors": remaining,
        "passed_corridors": passed,
        "error_corridors": failed,
        "total_candidate_routes": total_routes,
        "average_routes_per_completed_corridor": (
            total_routes / completed
            if completed
            else 0
        ),
        "total_duration_seconds": (
            total_duration_seconds
        ),
        "average_duration_seconds": (
            average_duration_seconds
        ),
        "swift_excluded": (
            args.exclude_swift
        ),
        "swift_violation_corridors": (
            swift_violation_corridors
        ),
        "swift_violation_routes": (
            swift_violation_routes
        ),
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    save_output(
        output_file,
        output,
    )

    print()
    print("=" * 80)
    print(
        "BRICS ROUTE DISCOVERY MODEL MATRIX SUMMARY"
    )
    print("=" * 80)

    print(
        f"Round:                  {ROUND_NAME}"
    )

    print(
        f"Provider:               {args.provider}"
    )

    print(
        f"Model:                  {args.model}"
    )

    print(
        f"Total countries:        {country_count}"
    )

    print(
        f"Directed corridors:     {total_corridors}"
    )

    print(
        f"SWIFT excluded:         "
        f"{args.exclude_swift}"
    )

    print(
        f"Completed:              {completed}"
    )

    print(
        f"Remaining:              {remaining}"
    )

    print(
        f"Passed:                 {passed}"
    )

    print(
        f"Errors:                 {failed}"
    )

    print(
        f"Candidate routes:       {total_routes}"
    )

    if completed:
        print(
            "Average routes/corridor:"
            f" {total_routes / completed:.2f}"
        )

    print(
        f"Total duration:         "
        f"{total_duration_seconds:.2f}s"
    )

    print(
        f"Average duration:       "
        f"{average_duration_seconds:.2f}s"
    )

    if args.exclude_swift:
        print(
            f"SWIFT violation corridors:"
            f" {swift_violation_corridors}"
        )
        print(
            f"SWIFT violation routes:    "
            f"{swift_violation_routes}"
        )

    print()
    print(
        f"Results saved: {output_file}"
    )

    print("=" * 80)


if __name__ == "__main__":
    main()
