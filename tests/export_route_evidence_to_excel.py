import json
import re
from pathlib import Path
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter


ROOT = Path(".")
OUTPUT = ROOT / "test_results" / "VTE_route_discovery_evidence.xlsx"

# JSON files that are inventories/catalogs rather than experiment results.
EXCLUDE_FROM_RESULTS = {
    "evidence_archive/inventory/inventory.json",
    "evidence_archive/inventory/all_runs_parsed.json",
}


def load_json(path):
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)


def infer_swift_mode(path, data):
    s = str(path).lower()

    if "swift_off" in s or "no_swift" in s or "exclude_swift" in s:
        return "SWIFT_OFF"

    if "swift_on" in s:
        return "SWIFT_ON"

    # Inspect metadata when filename does not tell us.
    text = json.dumps(data, ensure_ascii=False).lower()

    if '"swift_excluded": true' in text:
        return "SWIFT_OFF"

    if '"swift_excluded": false' in text:
        return "SWIFT_NOT_EXCLUDED"

    return "UNKNOWN"


def infer_round(path, data):
    m = re.search(r"round(\d+)", str(path), re.I)
    if m:
        return f"ROUND{m.group(1)}"

    text = json.dumps(data, ensure_ascii=False)
    m = re.search(r'"round"\s*:\s*"?(ROUND[^",}]+)', text, re.I)
    if m:
        return m.group(1)

    return ""


def infer_provider_model(path, data):
    name = path.name

    provider = ""
    model = ""

    # Common providers
    for p in ["ollama", "nebius", "tokenharbor"]:
        if p.lower() in name.lower():
            provider = p
            break

    # Try common metadata fields
    if isinstance(data, dict):
        for key in ["provider", "model_provider"]:
            if data.get(key):
                provider = str(data[key])

        for key in ["model", "model_name"]:
            if data.get(key):
                model = str(data[key])

    # Filename-based model extraction
    if not model:
        patterns = [
            r"ollama_(.+)\.json$",
            r"tokenharbor_(.+)\.json$",
            r"nebius_(.+)\.json$",
        ]

        for pattern in patterns:
            m = re.search(pattern, name, re.I)
            if m:
                model = m.group(1)
                break

    return provider, model


def find_records(data):
    """
    Normalize the different JSON layouts used across the historical runs.
    Returns a list of corridor/result records.
    """
    if isinstance(data, list):
        return data

    if not isinstance(data, dict):
        return []

    for key in [
        "results",
        "records",
        "corridors",
        "route_results",
        "data",
    ]:
        value = data.get(key)
        if isinstance(value, list):
            return value

    return []


def find_routes(record):
    if not isinstance(record, dict):
        return []

    for key in ["routes", "candidate_routes", "discovered_routes"]:
        value = record.get(key)
        if isinstance(value, list):
            return value

    return []


def first_value(d, *keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) is not None:
            return d.get(k)
    return ""


def text_value(value):
    if value is None:
        return ""

    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)

    return str(value)


def truncate(value, limit=32000):
    value = text_value(value)
    if len(value) > limit:
        return value[:limit] + "\n...[TRUNCATED FOR EXCEL CELL LIMIT]"
    return value


# ----------------------------------------------------------------------
# Discover JSON files
# ----------------------------------------------------------------------

json_files = sorted(
    p for p in ROOT.rglob("*.json")
    if ".git" not in p.parts
)

print("=" * 80)
print("VTE JSON → EXCEL EVIDENCE EXPORT")
print("=" * 80)
print(f"JSON files discovered: {len(json_files)}")
print()

# ----------------------------------------------------------------------
# Workbook
# ----------------------------------------------------------------------

wb = Workbook()

ws_index = wb.active
ws_index.title = "FILE_CATALOG"

ws_run = wb.create_sheet("RUN_SUMMARY")
ws_corr = wb.create_sheet("CORRIDORS")
ws_route = wb.create_sheet("ROUTES")
ws_swift = wb.create_sheet("SWIFT_ANALYSIS")
ws_error = wb.create_sheet("ERRORS")


# ----------------------------------------------------------------------
# Headers
# ----------------------------------------------------------------------

index_headers = [
    "File",
    "Relative Path",
    "Category",
    "Round",
    "Provider",
    "Model",
    "SWIFT Mode",
    "Size Bytes",
    "JSON Parse Status",
]

run_headers = [
    "Source File",
    "Relative Path",
    "Round",
    "Provider",
    "Model",
    "SWIFT Mode",
    "Records",
    "Passed",
    "Errors",
    "Routes",
    "Routes / Corridor",
    "Duplicate Route IDs",
    "Routes Mentioning SWIFT",
]

corr_headers = [
    "Source File",
    "Relative Path",
    "Round",
    "Provider",
    "Model",
    "SWIFT Mode",
    "Record Index",
    "Status",
    "VTI ID",
    "Source",
    "Destination",
    "Source Country",
    "Destination Country",
    "Corridor",
    "Route Count",
    "Error",
]

route_headers = [
    "Source File",
    "Relative Path",
    "Round",
    "Provider",
    "Model",
    "SWIFT Mode",
    "Record Index",
    "Route Index",
    "Record Status",
    "VTI ID",
    "Source",
    "Destination",
    "Route ID",
    "Rail",
    "Funding Method",
    "Delivery Method",
    "Transfer Path",
    "Route Requirements",
    "Corridor Availability",
    "Raw Route JSON",
]

swift_headers = [
    "Source File",
    "Round",
    "Provider",
    "Model",
    "SWIFT Mode",
    "Record Index",
    "Route Index",
    "Route ID",
    "SWIFT Text Present",
    "SWIFT Text Count",
    "SWIFT Snippet",
]

error_headers = [
    "Source File",
    "Relative Path",
    "Round",
    "Provider",
    "Model",
    "SWIFT Mode",
    "Record Index",
    "Status",
    "Error",
]


for ws, headers in [
    (ws_index, index_headers),
    (ws_run, run_headers),
    (ws_corr, corr_headers),
    (ws_route, route_headers),
    (ws_swift, swift_headers),
    (ws_error, error_headers),
]:
    ws.append(headers)


# ----------------------------------------------------------------------
# Process files
# ----------------------------------------------------------------------

total_records = 0
total_routes = 0
result_files = 0
parse_errors = 0

for path in json_files:
    rel = path.as_posix()
    data, parse_error = load_json(path)

    provider, model = infer_provider_model(path, data)
    round_name = infer_round(path, data)
    swift_mode = infer_swift_mode(path, data)

    if parse_error:
        parse_errors += 1
        category = "JSON_PARSE_ERROR"

        ws_index.append([
            path.name,
            rel,
            category,
            round_name,
            provider,
            model,
            swift_mode,
            path.stat().st_size,
            parse_error,
        ])

        ws_error.append([
            path.name,
            rel,
            round_name,
            provider,
            model,
            swift_mode,
            "",
            "JSON_PARSE_ERROR",
            parse_error,
        ])

        continue

    if rel in EXCLUDE_FROM_RESULTS:
        category = "INVENTORY / CATALOG"
        ws_index.append([
            path.name,
            rel,
            category,
            round_name,
            provider,
            model,
            swift_mode,
            path.stat().st_size,
            "OK",
        ])
        continue

    records = find_records(data)

    # Files without recognizable result records are still catalogued.
    if not records:
        category = "JSON / NON-ROUTE DATA"

        ws_index.append([
            path.name,
            rel,
            category,
            round_name,
            provider,
            model,
            swift_mode,
            path.stat().st_size,
            "OK",
        ])
        continue

    result_files += 1
    category = "ROUTE DISCOVERY RESULT"

    ws_index.append([
        path.name,
        rel,
        category,
        round_name,
        provider,
        model,
        swift_mode,
        path.stat().st_size,
        "OK",
    ])

    route_rows = []
    route_ids = []
    swift_route_rows = []

    passed = 0
    errors = 0

    for record_index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            continue

        status = str(first_value(record, "status", "execution_status"))

        if status.upper() in ["PASS", "PASSED", "SUCCESS", "COMPLETED"]:
            passed += 1
        else:
            errors += 1

        vti = first_value(
            record,
            "vti_id",
            "value_transfer_intent_id",
            "intent_id",
            "id",
        )

        source = first_value(
            record,
            "source",
            "source_country",
            "origin",
            "origin_country",
        )

        destination = first_value(
            record,
            "destination",
            "destination_country",
            "target",
            "target_country",
        )

        corridor = ""
        if source and destination:
            corridor = f"{source} -> {destination}"

        routes = find_routes(record)

        corr_error = first_value(record, "error", "error_message", "exception")

        ws_corr.append([
            path.name,
            rel,
            round_name,
            provider,
            model,
            swift_mode,
            record_index,
            status,
            vti,
            source,
            destination,
            source,
            destination,
            corridor,
            len(routes),
            truncate(corr_error),
        ])

        total_records += 1

        for route_index, route in enumerate(routes, start=1):
            if not isinstance(route, dict):
                continue

            total_routes += 1

            route_id = first_value(route, "route_id", "id")
            if route_id:
                route_ids.append(str(route_id))

            rail = first_value(route, "rail")
            funding = first_value(route, "funding_method")
            delivery = first_value(route, "delivery_method")
            transfer_path = first_value(route, "transfer_path")
            requirements = first_value(route, "route_requirements")
            availability = first_value(route, "corridor_availability")

            raw_route = json.dumps(route, ensure_ascii=False)

            ws_route.append([
                path.name,
                rel,
                round_name,
                provider,
                model,
                swift_mode,
                record_index,
                route_index,
                status,
                vti,
                source,
                destination,
                route_id,
                truncate(rail),
                truncate(funding),
                truncate(delivery),
                truncate(transfer_path),
                truncate(requirements),
                truncate(availability),
                truncate(raw_route),
            ])

            route_text = raw_route.lower()

            if "swift" in route_text:
                snippets = []

                for field_name, field_value in [
                    ("rail", rail),
                    ("funding_method", funding),
                    ("delivery_method", delivery),
                    ("transfer_path", transfer_path),
                    ("route_requirements", requirements),
                ]:
                    value = text_value(field_value)

                    if "swift" in value.lower():
                        snippets.append(f"{field_name}: {value}")

                snippet = " | ".join(snippets)

                ws_swift.append([
                    path.name,
                    round_name,
                    provider,
                    model,
                    swift_mode,
                    record_index,
                    route_index,
                    route_id,
                    "YES",
                    route_text.count("swift"),
                    truncate(snippet, 8000),
                ])

        if status.upper() not in ["PASS", "PASSED", "SUCCESS", "COMPLETED"]:
            ws_error.append([
                path.name,
                rel,
                round_name,
                provider,
                model,
                swift_mode,
                record_index,
                status,
                truncate(corr_error),
            ])

    duplicate_ids = len(route_ids) - len(set(route_ids))
    swift_count = 0

    # Count SWIFT route rows for this file.
    for row in ws_swift.iter_rows(min_row=2, values_only=True):
        if row[0] == path.name and row[1] == round_name and row[2] == provider and row[3] == model:
            swift_count += 1

    ws_run.append([
        path.name,
        rel,
        round_name,
        provider,
        model,
        swift_mode,
        len(records),
        passed,
        errors,
        len(route_ids),
        len(route_ids) / len(records) if records else 0,
        duplicate_ids,
        swift_count,
    ])


# ----------------------------------------------------------------------
# Formatting
# ----------------------------------------------------------------------

header_fill = PatternFill("solid", fgColor="1F4E78")
header_font = Font(color="FFFFFF", bold=True)

for ws in wb.worksheets:
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for column_cells in ws.columns:
        max_len = 0

        for cell in column_cells[:1000]:
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))

        width = min(max(max_len + 2, 12), 45)

        ws.column_dimensions[get_column_letter(column_cells[0].column)].width = width


# Specific widths for large evidence columns
for col in ["R", "S", "T", "U"]:
    if col in ws_route.column_dimensions:
        ws_route.column_dimensions[col].width = 45


# Number format
for row in ws_run.iter_rows(min_row=2):
    row[10].number_format = "0.00"


# ----------------------------------------------------------------------
# Add a small README sheet
# ----------------------------------------------------------------------

ws_readme = wb.create_sheet("README", 0)

readme = [
    ["VTE Route Discovery Evidence Workbook", ""],
    ["Purpose", "Consolidated evidence index and analysis workbook for historical and current JSON route-discovery experiments."],
    ["Source policy", "Every discovered JSON file is catalogued. Route-discovery JSON files are expanded into corridor and route-level sheets."],
    ["Deduplication", "NO deduplication. Archive/current/test copies remain separate so experimental provenance is preserved."],
    ["SWIFT", "SWIFT mode is inferred from path and available metadata. 'Routes Mentioning SWIFT' means text presence only; it is NOT semantic SWIFT usage classification."],
    ["Raw evidence", "Raw route JSON is preserved in the ROUTES sheet where practical, subject to Excel's cell-size limit."],
    ["Inventory files", "Known inventory/catalog JSON files are catalogued but not treated as route experiments."],
    ["Generated by", "tests/export_route_evidence_to_excel.py"],
]

for row in readme:
    ws_readme.append(row)

ws_readme.column_dimensions["A"].width = 28
ws_readme.column_dimensions["B"].width = 110

for cell in ws_readme[1]:
    cell.font = Font(bold=True, size=14)

# Move README to front
wb._sheets.remove(ws_readme)
wb._sheets.insert(0, ws_readme)

# Save
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
wb.save(OUTPUT)

print()
print("=" * 80)
print("EXPORT COMPLETE")
print("=" * 80)
print(f"JSON files discovered:     {len(json_files)}")
print(f"Route result files:        {result_files}")
print(f"JSON parse errors:         {parse_errors}")
print(f"Corridor/result records:   {total_records}")
print(f"Route objects:              {total_routes}")
print()
print(f"Excel workbook:")
print(OUTPUT)
print("=" * 80)
