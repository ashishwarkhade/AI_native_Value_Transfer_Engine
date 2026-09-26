import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request


BRICS_COUNTRIES = [
    {"name": "Brazil", "code": "BR", "currency": "BRL", "category": "MEMBER"},
    {"name": "Russia", "code": "RU", "currency": "RUB", "category": "MEMBER"},
    {"name": "India", "code": "IN", "currency": "INR", "category": "MEMBER"},
    {"name": "China", "code": "CN", "currency": "CNY", "category": "MEMBER"},
    {"name": "South Africa", "code": "ZA", "currency": "ZAR", "category": "MEMBER"},
    {"name": "Saudi Arabia", "code": "SA", "currency": "SAR", "category": "MEMBER"},
    {"name": "Egypt", "code": "EG", "currency": "EGP", "category": "MEMBER"},
    {"name": "United Arab Emirates", "code": "AE", "currency": "AED", "category": "MEMBER"},
    {"name": "Ethiopia", "code": "ET", "currency": "ETB", "category": "MEMBER"},
    {"name": "Iran", "code": "IR", "currency": "IRR", "category": "MEMBER"},
    {"name": "Indonesia", "code": "ID", "currency": "IDR", "category": "MEMBER"},
    {"name": "Belarus", "code": "BY", "currency": "BYN", "category": "PARTNER"},
    {"name": "Bolivia", "code": "BO", "currency": "BOB", "category": "PARTNER"},
    {"name": "Cuba", "code": "CU", "currency": "CUP", "category": "PARTNER"},
    {"name": "Kazakhstan", "code": "KZ", "currency": "KZT", "category": "PARTNER"},
    {"name": "Malaysia", "code": "MY", "currency": "MYR", "category": "PARTNER"},
    {"name": "Nigeria", "code": "NG", "currency": "NGN", "category": "PARTNER"},
    {"name": "Thailand", "code": "TH", "currency": "THB", "category": "PARTNER"},
    {"name": "Uganda", "code": "UG", "currency": "UGX", "category": "PARTNER"},
    {"name": "Uzbekistan", "code": "UZ", "currency": "UZS", "category": "PARTNER"},
    {"name": "Vietnam", "code": "VN", "currency": "VND", "category": "PARTNER"},
]


EXPERIMENT_NAME = "ALICEAI_RAW_BRICS_100_DIRECTED"
MATRIX_VERSION = "BRICS-21-MEMBER-PARTNER-V1"
MODEL_NAME = "yandex/AliceAI-Foundation-80B-A3B-Base"

DEFAULT_ENDPOINT = (
    "https://d2svk23kw4msi3-8000.proxy.runpod.net/v1/completions"
)

DEFAULT_AMOUNT = 100000
DEFAULT_MAX_TOKENS = 1500
DEFAULT_TEMPERATURE = 0.2
DEFAULT_TIMEOUT_SECONDS = 600
DEFAULT_PAUSE_SECONDS = 1.0

OUTPUT_FILE = Path(
    "test_results/brics_21_aliceai_raw_route_discovery_100.json"
)


def build_balanced_directed_corridors():
    """
    Build 50 unordered country pairs, then emit both directions.

    The first 21 pairs form a ring so every country participates
    immediately. Additional pairs are selected deterministically
    until 50 unordered pairs exist.

    Final result: 100 directed corridors.
    """

    country_count = len(BRICS_COUNTRIES)

    pairs = []
    seen = set()

    def add_pair(i, j):
        if i == j:
            return

        key = tuple(sorted((i, j)))

        if key in seen:
            return

        seen.add(key)
        pairs.append(key)

    # Ring: every country participates.
    for i in range(country_count):
        add_pair(i, (i + 1) % country_count)

    # Add deterministic distance-based pairs.
    distance = 2

    while len(pairs) < 50:
        for i in range(country_count):
            j = (i + distance) % country_count
            add_pair(i, j)

            if len(pairs) >= 50:
                break

        distance += 1

    directed = []

    sequence = 1

    for i, j in pairs:
        source = BRICS_COUNTRIES[i]
        destination = BRICS_COUNTRIES[j]

        directed.append(
            {
                "sequence": sequence,
                "source": source,
                "destination": destination,
            }
        )
        sequence += 1

        directed.append(
            {
                "sequence": sequence,
                "source": destination,
                "destination": source,
            }
        )
        sequence += 1

    return directed


def build_prompt(source, destination):
    return f"""
You are exploring possible value-transfer routes for a Value Transfer Engine.

This is a RAW ROUTE DISCOVERY experiment.

Do not try to produce JSON.
Do not follow a fixed output schema.
Do not write code.

Explore plausible ways value could move from:

Source:
- Country: {source["name"]}
- Currency: {source["currency"]}
- Country category: {source["category"]}

Destination:
- Country: {destination["name"]}
- Currency: {destination["currency"]}
- Country category: {destination["category"]}

Amount:
- {DEFAULT_AMOUNT} {source["currency"]}

Identify multiple distinct candidate mechanisms where possible.

For each candidate, discuss whatever is relevant, including:
- payment or settlement rail
- funding mechanism
- transfer path
- intermediary or provider/network
- currency conversion
- delivery method
- recipient endpoint
- route requirements or dependencies
- alternative mechanisms

Explore beyond the first obvious route.

Treat everything you identify as a candidate hypothesis.
Do not claim that a route is legally permissible, compliant, eligible,
available, or recommended.
Do not assume that a named provider actually supports this corridor.
Do not invent capabilities as established facts.

The purpose of this experiment is to observe the model's raw route-discovery
behavior. Explain uncertainty when appropriate.

Now explore the candidate value-transfer routes for:
{source["name"]} -> {destination["name"]}.
""".strip()


def call_aliceai(
    endpoint,
    prompt,
    timeout,
    max_tokens,
    temperature,
):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    body = json.dumps(payload).encode("utf-8")

    req = request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "curl/8.0",
            "Accept": "application/json",
        },
        method="POST",
    )

    started = time.perf_counter()

    try:
        with request.urlopen(req, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")

        duration = time.perf_counter() - started

        parsed = json.loads(response_body)

        choices = parsed.get("choices", [])

        if not choices:
            raise RuntimeError(
                "AliceAI response contained no choices."
            )

        text = choices[0].get("text", "")

        return {
            "status": "PASS",
            "duration_seconds": round(duration, 4),
            "raw_ai_response": text,
            "finish_reason": choices[0].get("finish_reason"),
            "stop_reason": choices[0].get("stop_reason"),
            "usage": parsed.get("usage"),
            "response_id": parsed.get("id"),
            "system_fingerprint": parsed.get("system_fingerprint"),
        }

    except error.HTTPError as exc:
        duration = time.perf_counter() - started
        detail = exc.read().decode("utf-8", errors="replace")

        return {
            "status": "ERROR",
            "duration_seconds": round(duration, 4),
            "raw_ai_response": None,
            "error": f"AliceAI HTTP {exc.code}: {detail}",
        }

    except error.URLError as exc:
        duration = time.perf_counter() - started

        return {
            "status": "ERROR",
            "duration_seconds": round(duration, 4),
            "raw_ai_response": None,
            "error": f"AliceAI connection error: {exc.reason}",
        }

    except Exception as exc:
        duration = time.perf_counter() - started

        return {
            "status": "ERROR",
            "duration_seconds": round(duration, 4),
            "raw_ai_response": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def load_existing():
    if not OUTPUT_FILE.exists():
        return None

    try:
        with OUTPUT_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(
            f"WARNING: Could not load existing output: "
            f"{type(exc).__name__}: {exc}"
        )
        return None


def save_output(output):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def build_output(endpoint, max_tokens, temperature):
    return {
        "test": EXPERIMENT_NAME,
        "experiment": (
            "Raw AliceAI BASE-model route discovery. "
            "The model is not required to produce structured JSON. "
            "Raw generated evidence is preserved for downstream analysis."
        ),
        "matrix_version": MATRIX_VERSION,
        "model": MODEL_NAME,
        "endpoint": endpoint,
        "constraints": {
            "swift_excluded": False,
            "deterministic_route_assumptions": False,
            "structured_json_required": False,
            "downstream_validation_required": True,
            "raw_ai_output_preserved": True,
        },
        "generation": {
            "max_tokens": max_tokens,
            "temperature": temperature,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "countries": BRICS_COUNTRIES,
        "country_count": len(BRICS_COUNTRIES),
        "member_count": sum(
            c["category"] == "MEMBER"
            for c in BRICS_COUNTRIES
        ),
        "partner_count": sum(
            c["category"] == "PARTNER"
            for c in BRICS_COUNTRIES
        ),
        "requested_directed_corridors": 100,
        "results": [],
    }


def main():
    parser = argparse.ArgumentParser(
        description="AliceAI raw route-discovery experiment"
    )

    parser.add_argument(
        "--endpoint",
        default=DEFAULT_ENDPOINT,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        choices=range(1, 101),
    )

    parser.add_argument(
        "--pause",
        type=float,
        default=DEFAULT_PAUSE_SECONDS,
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
    )

    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
    )

    parser.add_argument(
        "--fresh",
        action="store_true",
    )

    args = parser.parse_args()

    corridors = build_balanced_directed_corridors()

    if args.fresh:
        output = build_output(
            args.endpoint,
            args.max_tokens,
            args.temperature,
        )
    else:
        output = load_existing()

        if output is None:
            output = build_output(
                args.endpoint,
                args.max_tokens,
                args.temperature,
            )

    existing_sequences = {
        result["sequence"]
        for result in output["results"]
    }

    print()
    print("=" * 80)
    print("VTE — ALICEAI RAW 100-DIRECTED-CORRIDOR ROUTE DISCOVERY")
    print("=" * 80)
    print(f"Model:          {MODEL_NAME}")
    print(f"Endpoint:       {args.endpoint}")
    print(
        f"Countries:      {len(BRICS_COUNTRIES)} "
        f"({output['member_count']} MEMBER + "
        f"{output['partner_count']} PARTNER)"
    )
    print(
        f"Corridors:      100 requested / "
        f"{args.limit} this execution"
    )
    print("Direction:      A -> B and B -> A represented")
    print("SWIFT excluded: False")
    print("JSON required:  False")
    print(f"Max tokens:     {args.max_tokens}")
    print(f"Temperature:    {args.temperature}")
    print(f"Output:         {OUTPUT_FILE}")
    print(f"Existing:       {len(existing_sequences)}")
    print()

    processed = 0

    for corridor in corridors:
        if processed >= args.limit:
            break

        sequence = corridor["sequence"]

        if sequence in existing_sequences:
            continue

        source = corridor["source"]
        destination = corridor["destination"]

        intent_id = (
            f"VTI-ALICE-RAW-"
            f"{source['code']}-"
            f"{destination['code']}-"
            f"{sequence:03d}"
        )

        print("-" * 80)
        print(
            f"[{processed + 1}/{args.limit}] "
            f"{source['name']} ({source['category']}) -> "
            f"{destination['name']} ({destination['category']})"
        )
        print(
            f"Intent: {intent_id} | "
            f"{DEFAULT_AMOUNT} {source['currency']} -> "
            f"{destination['currency']}"
        )

        started_at = datetime.now(timezone.utc).isoformat()

        prompt = build_prompt(source, destination)

        result = call_aliceai(
            endpoint=args.endpoint,
            prompt=prompt,
            timeout=args.timeout,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )

        completed_at = datetime.now(timezone.utc).isoformat()

        record = {
            "sequence": sequence,
            "intent": {
                "intent_id": intent_id,
                "amount": DEFAULT_AMOUNT,
                "from_country": source["name"],
                "source_currency": source["currency"],
                "to_country": destination["name"],
                "destination_currency": destination["currency"],
                "required_delivery_time": "",
            },
            "source_category": source["category"],
            "destination_category": destination["category"],
            "prompt": prompt,
            "status": result["status"],
            "duration_seconds": result["duration_seconds"],
            "raw_ai_response": result.get("raw_ai_response"),
            "finish_reason": result.get("finish_reason"),
            "stop_reason": result.get("stop_reason"),
            "usage": result.get("usage"),
            "response_id": result.get("response_id"),
            "system_fingerprint": result.get(
                "system_fingerprint"
            ),
            "error": result.get("error"),
            "started_at": started_at,
            "completed_at": completed_at,
        }

        output["results"].append(record)

        processed += 1

        output["last_run_completed_at"] = completed_at
        output["completed_this_execution"] = processed
        output["total_results_saved"] = len(output["results"])
        output["pass_count"] = sum(
            r.get("status") == "PASS"
            for r in output["results"]
        )
        output["error_count"] = sum(
            r.get("status") == "ERROR"
            for r in output["results"]
        )

        durations = [
            r["duration_seconds"]
            for r in output["results"]
            if r.get("duration_seconds") is not None
        ]

        output["average_duration_seconds"] = (
            round(sum(durations) / len(durations), 4)
            if durations
            else 0
        )

        save_output(output)

        print(
            f"Status: {record['status']} | "
            f"Runtime: {record['duration_seconds']:.2f}s"
        )

        if record.get("finish_reason"):
            print(
                f"Finish reason: {record['finish_reason']}"
            )

        if record.get("usage"):
            usage = record["usage"]
            print(
                f"Tokens: prompt={usage.get('prompt_tokens')} "
                f"completion={usage.get('completion_tokens')} "
                f"total={usage.get('total_tokens')}"
            )

        if record["raw_ai_response"]:
            preview = record["raw_ai_response"].replace(
                "\n", " "
            )
            print(
                "Raw response preview: "
                f"{preview[:300]}"
            )

        if processed < args.limit:
            time.sleep(args.pause)

    output["last_run_completed_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    output["completed_this_execution"] = processed
    output["total_results_saved"] = len(output["results"])

    output["pass_count"] = sum(
        r.get("status") == "PASS"
        for r in output["results"]
    )

    output["error_count"] = sum(
        r.get("status") == "ERROR"
        for r in output["results"]
    )

    durations = [
        r["duration_seconds"]
        for r in output["results"]
        if r.get("duration_seconds") is not None
    ]

    output["average_duration_seconds"] = (
        round(sum(durations) / len(durations), 4)
        if durations
        else 0
    )


    save_output(output)

    print()
    print("=" * 80)
    print("RUN COMPLETE")
    print("=" * 80)
    print(f"Processed this execution: {processed}")
    print(f"Saved corridor results:   {len(output['results'])}")
    print(f"PASS:                     {output['pass_count']}")
    print(f"ERROR:                    {output['error_count']}")
    print(
        f"Average runtime:          "
        f"{output['average_duration_seconds']:.2f}s"
    )
    print(f"Evidence file:            {OUTPUT_FILE}")


if __name__ == "__main__":
    main()