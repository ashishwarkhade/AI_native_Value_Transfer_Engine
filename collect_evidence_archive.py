import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path.cwd()
ARCHIVE_ROOT = PROJECT_ROOT / "evidence_archive"

EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "evidence_archive",
}

EXCLUDED_FILES = {
    ".env",
}

INCLUDE_EXTENSIONS = {
    ".json",
    ".jsonl",
    ".log",
    ".txt",
    ".md",
    ".py",
}

KEYWORDS = (
    "round",
    "result",
    "response",
    "route",
    "matrix",
    "test",
    "smoke",
    "pre",
    "benchmark",
    "harness",
    "swift",
    "tokenharbor",
    "ollama",
    "nebius",
)


def is_excluded(path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return True

    if path.name in EXCLUDED_FILES:
        return True

    return False


def is_evidence_file(path: Path) -> bool:
    if is_excluded(path):
        return False

    if not path.is_file():
        return False

    if path.suffix.lower() not in INCLUDE_EXTENSIONS:
        return False

    name = path.name.lower()

    return any(keyword in name for keyword in KEYWORDS)


def classify(path: Path) -> str:
    name = path.name.lower()

    if "smoke" in name:
        return "smoke"

    if "pre" in name:
        return "pre_test"

    if "round" in name:
        return "full_runs"

    if "result" in name or "response" in name:
        return "raw_results"

    if "log" in name:
        return "logs"

    if "test" in name or "matrix" in name or "harness" in name:
        return "test"

    return "raw_results"


def file_metadata(path: Path) -> dict:
    stat = path.stat()

    return {
        "source": str(path.relative_to(PROJECT_ROOT)),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(
            stat.st_mtime,
            tz=timezone.utc,
        ).isoformat(),
    }


def inspect_json(path: Path) -> dict:
    result = {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))

        result["json_valid"] = True
        result["json_type"] = type(data).__name__

        if isinstance(data, dict):
            result["keys"] = list(data.keys())

            for key in (
                "test",
                "round",
                "matrix_version",
                "provider",
                "model",
                "generated_at",
                "default_amount",
                "default_delivery_time",
                "total_directed_corridors",
            ):
                if key in data:
                    result[key] = data[key]

            if isinstance(data.get("results"), list):
                result["result_count"] = len(data["results"])

            if isinstance(data.get("summary"), dict):
                result["summary"] = data["summary"]

    except Exception as exc:
        result["json_valid"] = False
        result["json_error"] = str(exc)

    return result


def main():
    ARCHIVE_ROOT.mkdir(exist_ok=True)

    categories = [
        "inventory",
        "pre_test",
        "smoke",
        "test",
        "full_runs",
        "raw_results",
        "logs",
        "source_metadata",
    ]

    for category in categories:
        (ARCHIVE_ROOT / category).mkdir(
            parents=True,
            exist_ok=True,
        )

    evidence_files = []

    for path in PROJECT_ROOT.rglob("*"):
        if is_evidence_file(path):
            evidence_files.append(path)

    evidence_files = sorted(
        evidence_files,
        key=lambda p: str(p),
    )

    inventory = {
        "archive_created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "archive_root": str(ARCHIVE_ROOT),
        "source_count": len(evidence_files),
        "sources": [],
    }

    for source in evidence_files:
        category = classify(source)

        destination = (
            ARCHIVE_ROOT
            / category
            / source.relative_to(PROJECT_ROOT)
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(source, destination)

        metadata = file_metadata(source)

        if source.suffix.lower() == ".json":
            metadata["content"] = inspect_json(source)

        inventory["sources"].append(metadata)

    inventory_path = (
        ARCHIVE_ROOT
        / "inventory"
        / "inventory.json"
    )

    inventory_path.write_text(
        json.dumps(
            inventory,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print("=" * 80)
    print("VTE EVIDENCE ARCHIVE CREATED")
    print("=" * 80)
    print(f"Project:        {PROJECT_ROOT}")
    print(f"Archive:        {ARCHIVE_ROOT}")
    print(f"Evidence files: {len(evidence_files)}")
    print()
    print("Categories:")
    for category in categories:
        count = len(
            list(
                (ARCHIVE_ROOT / category).rglob("*")
            )
        )
        print(f"  {category:15} {count}")
    print()
    print(f"Inventory: {inventory_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
