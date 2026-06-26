"""Redact secret-like OpenAPI example values that trigger static secret scanners."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

JWT_PATTERN = re.compile(r"^eyJ[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]*){2,}")
PKCS8_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN PRIVATE KEY-----[\s\S]+-----END PRIVATE KEY-----"
)
RSA_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN RSA PRIVATE KEY-----[\s\S]+-----END RSA PRIVATE KEY-----"
)

JWT_PLACEHOLDER = "signed-jwt-token-example-redacted"
PKCS8_PRIVATE_KEY_PLACEHOLDER = (
    "-----BEGIN PRIVATE KEY-----\n"
    "REDACTED-EXAMPLE-PRIVATE-KEY-MATERIAL...\n"
    "-----END PRIVATE KEY-----\n"
)
RSA_PRIVATE_KEY_PLACEHOLDER = (
    "-----BEGIN RSA PRIVATE KEY-----\n"
    "REDACTED-EXAMPLE-PRIVATE-KEY-MATERIAL...\n"
    "-----END RSA PRIVATE KEY-----\n"
)


def sanitize_string(value: str) -> tuple[str, bool]:
    if value in {
        JWT_PLACEHOLDER,
        PKCS8_PRIVATE_KEY_PLACEHOLDER,
        RSA_PRIVATE_KEY_PLACEHOLDER,
    }:
        return value, False

    updated = value
    changed = False

    if JWT_PATTERN.match(value):
        return JWT_PLACEHOLDER, True

    if PKCS8_PRIVATE_KEY_PATTERN.search(value) and "REDACTED-EXAMPLE-PRIVATE-KEY-MATERIAL" not in value:
        updated = PKCS8_PRIVATE_KEY_PATTERN.sub(PKCS8_PRIVATE_KEY_PLACEHOLDER, updated)
        changed = updated != value

    if RSA_PRIVATE_KEY_PATTERN.search(value) and "REDACTED-EXAMPLE-PRIVATE-KEY-MATERIAL" not in value:
        updated = RSA_PRIVATE_KEY_PATTERN.sub(RSA_PRIVATE_KEY_PLACEHOLDER, updated)
        changed = updated != value

    return updated, changed


def sanitize_value(value: Any) -> tuple[Any, int]:
    if isinstance(value, str):
        sanitized, changed = sanitize_string(value)
        return sanitized, int(changed)

    if isinstance(value, list):
        replacements = 0
        sanitized_items = []
        for item in value:
            sanitized_item, item_replacements = sanitize_value(item)
            sanitized_items.append(sanitized_item)
            replacements += item_replacements
        return sanitized_items, replacements

    if isinstance(value, dict):
        replacements = 0
        sanitized_mapping: dict[Any, Any] = {}
        for key, item in value.items():
            sanitized_item, item_replacements = sanitize_value(item)
            sanitized_mapping[key] = sanitized_item
            replacements += item_replacements
        return sanitized_mapping, replacements

    return value, 0


def sanitize_open_api_file(path: Path) -> int:
    with path.open(encoding="utf-8-sig") as handle:
        payload = json.load(handle)

    sanitized_payload, replacements = sanitize_value(payload)
    if replacements:
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(sanitized_payload, handle, indent=4, ensure_ascii=False)
            handle.write("\n")

    return replacements


def default_open_api_files(integrations_root: Path) -> list[Path]:
    return sorted(integrations_root.glob("*/open_api.json"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="open_api.json files to sanitize (defaults to all integration specs)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    integrations_root = repo_root / "autobotAI_integrations" / "integrations"
    targets = args.paths or default_open_api_files(integrations_root)

    total_replacements = 0
    for path in targets:
        if not path.is_file() or path.stat().st_size == 0:
            print(f"{path}: skipped empty or missing file")
            continue
        try:
            replacements = sanitize_open_api_file(path)
        except json.JSONDecodeError as exc:
            print(f"{path}: skipped invalid JSON ({exc})")
            continue
        total_replacements += replacements
        if replacements:
            print(f"{path}: redacted {replacements} secret-like example value(s)")

    if total_replacements == 0:
        print("No secret-like example values found.")


if __name__ == "__main__":
    main()
