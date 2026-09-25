import json
from pathlib import Path
from collections import Counter


ROOT = Path("evidence_archive")
OUTPUT = ROOT / "inventory" / "all_runs_parsed.json"


def classify_run(path: Path):
    name = path.name.lower()
    text = str(path).lower()

    labels = []

    for label in [
        "trial",
        "smoke",
        "partial",
        "test",
        "full",
        "pilot",
        "failed",
        "stopped",
    ]:
        if label in name or label in text:
            labels.append(label)

    return labels or ["unknown"]


def classify_swift(path: Path):
    text = str(path).lower()

    if "swift_off" in text or "no_swift" in text:
        return "OFF"

    if "swift_on" in text:
        return "ON"

    return "UNKNOWN"


def extract_results(data):
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    for key in ("results", "records"):
        value = data.get(key)
        if isinstance(value, list):
            return value

    return []


def parse_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        return {
            "source_file": str(path),
            "file_type": "json",
            "parse_status": "ERROR",
            "error": str(exc),
        }

    results = extract_results(data)

    record = {
        "source_file": str(path),
        "file_type": "json",
        "parse_status": "OK",
        "run_type": classify_run(path),
        "swift": classify_swift(path),
        "top_level_type": type(data).__name__,
        "top_level_keys": (
            sorted(data.keys())
            if isinstance(data, dict)
            else []
        ),
        "record_count": len(results),
    }

    if isinstance(data, dict):
        # Preserve metadata when present.
        for key in [
            "round",
            "test",
            "matrix_version",
            "provider",
            "model",
            "generated_at",
            "country_count",
            "member_count",
            "partner_count",
            "total_directed_corridors",
            "default_amount",
            "default_delivery_time",
            "constraints",
        ]:
            if key in data:
                record[key] = data[key]

        summary = data.get("summary")

        if isinstance(summary, dict):
            record["summary"] = summary

    if results:
        statuses = Counter()
        total_routes = 0
        durations = []

        for item in results:
            if not isinstance(item, dict):
                continue

            status = item.get("status")
            if status:
                statuses[status] += 1

            try:
                total_routes += int(item.get("route_count", 0) or 0)
            except (TypeError, ValueError):
                pass

            duration = item.get("duration_seconds")

            if duration is not None:
                try:
                    durations.append(float(duration))
                except (TypeError, ValueError):
                    pass

        record["status_counts"] = dict(statuses)
        record["route_count_total"] = total_routes

        if durations:
            record["duration_seconds_total"] = sum(durations)
            record["duration_seconds_average"] = (
                sum(durations) / len(durations)
            )
        else:
            record["duration_seconds_total"] = None
            record["duration_seconds_average"] = None

        first_record = next(
            (
                item
                for item in results
                if isinstance(item, dict)
            ),
            None,
        )

        if first_record:
            record["record_fields"] = sorted(first_record.keys())

    return record


def parse_text(path: Path):
    try:
        content = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        return {
            "source_file": str(path),
            "file_type": path.suffix.lower() or "text",
            "parse_status": "OK",
            "run_type": classify_run(path),
            "swift": classify_swift(path),
            "size_bytes": path.stat().st_size,
            "line_count": len(content.splitlines()),
        }

    except Exception as exc:
        return {
            "source_file": str(path),
            "file_type": path.suffix.lower() or "text",
            "parse_status": "ERROR",
            "error": str(exc),
        }


def main():
    files = sorted(
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and p.name != OUTPUT.name
    )

    parsed = []

    for path in files:
        if path.suffix.lower() == ".json":
            parsed.append(parse_json(path))
        else:
            parsed.append(parse_text(path))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(
            parsed,
            f,
            indent=2,
            ensure_ascii=False,
        )

    json_files = [
        r for r in parsed
        if r.get("file_type") == "json"
    ]

    json_ok = sum(
        r.get("parse_status") == "OK"
        for r in json_files
    )

    json_errors = sum(
        r.get("parse_status") == "ERROR"
        for r in json_files
    )

    run_types = Counter()

    for r in parsed:
        for run_type in r.get("run_type", []):
            run_types[run_type] += 1

    swift_counts = Counter(
        r.get("swift", "UNKNOWN")
        for r in parsed
    )

    print("=" * 80)
    print("ALL EVIDENCE PARSED")
    print("=" * 80)

    print(f"Files discovered : {len(parsed)}")
    print(f"JSON files       : {len(json_files)}")
    print(f"JSON parsed      : {json_ok}")
    print(f"JSON errors      : {json_errors}")

    print()
    print("RUN TYPES")
    for key, value in sorted(run_types.items()):
        print(f"  {key:10} {value}")

    print()
    print("SWIFT CLASSIFICATION")
    for key, value in sorted(swift_counts.items()):
        print(f"  {key:10} {value}")

    print()
    print("JSON RUN RECORDS")

    for r in parsed:
        if r.get("file_type") != "json":
            continue

        print(
            f"  {r['source_file']}"
            f" | records={r.get('record_count')}"
            f" | swift={r.get('swift')}"
            f" | type={','.join(r.get('run_type', []))}"
        )

    print()
    print("OUTPUT")
    print(OUTPUT)
    print("=" * 80)


if __name__ == "__main__":
    main()
