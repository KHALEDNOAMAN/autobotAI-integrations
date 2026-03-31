#!/usr/bin/env python3
"""
Convert the ZIA section of the Zscaler OneAPI Postman collection into a proper
OpenAPI 3.0 JSON file with path parameters, query parameters, and request body
examples.

This script:
  1. Reads the Postman collection (expects the ZIA folder)
  2. Replaces hardcoded numeric IDs in URL paths with {id} path parameters
  3. Merges duplicate logical paths (same pattern, different sample IDs)
  4. Preserves existing {variable} patterns from the Postman collection
  5. Extracts query parameters from url.query
  6. Parses request body JSON into example schemas
  7. Produces proper OpenAPI 3.0 parameters arrays

Usage:
    python convert_postman_to_openapi.py <postman_collection.json> [output.json]

If output path is omitted, writes to open_api.json in the same directory as
this script.
"""

import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Known non-ID path segments that happen to look numeric but are part of the
# API path structure. Extend as needed.
KNOWN_LITERAL_SEGMENTS = frozenset()

# Segments that are already Postman-style variables (with or without braces).
_POSTMAN_VAR_RE = re.compile(r"^\{?\{?(\w+)\}?\}?$")

# Heuristic: a path segment is a "hardcoded sample ID" if it is purely digits
# (length >= 1) or looks like a hex hash (length >= 16, hex chars only).
_NUMERIC_ID_RE = re.compile(r"^\d+$")
_HEX_HASH_RE = re.compile(r"^[0-9A-Fa-f]{16,}$")


def _is_sample_id(segment: str) -> bool:
    """Return True if the segment looks like a hardcoded sample ID."""
    if segment in KNOWN_LITERAL_SEGMENTS:
        return False
    if _NUMERIC_ID_RE.match(segment):
        return True
    if _HEX_HASH_RE.match(segment):
        return True
    return False


def _infer_param_name(prev_segment: str | None) -> str:
    """
    Infer a descriptive parameter name from the preceding path segment.
    e.g. 'adminUsers' -> 'adminUserId', 'dlpEngines' -> 'dlpEngineId'
    """
    if not prev_segment or prev_segment.startswith("{"):
        return "id"
    # Strip leading slash, braces etc
    clean = prev_segment.strip("/{}").rstrip("s")  # rough singularize
    if clean.endswith("ie"):  # 'categories' -> 'categorie' -> 'category'
        clean = clean[:-2] + "y"
    # camelCase -> add Id suffix
    return f"{clean}Id" if clean else "id"


def _normalise_path_segment(seg: str) -> str:
    """Normalise a Postman path segment: strip double-curly Postman vars."""
    # {{var}} -> {var}
    m = re.match(r"^\{\{(\w+)\}\}$", seg)
    if m:
        return "{" + m.group(1) + "}"
    # {var} already fine
    if re.match(r"^\{(\w+)\}$", seg):
        return seg
    return seg


# ---------------------------------------------------------------------------
# Postman collection traversal
# ---------------------------------------------------------------------------


def find_zia_section(collection: dict) -> dict | None:
    """Find the 'Zscaler Internet Access (ZIA)' top-level folder."""
    for item in collection.get("item", []):
        if "Zscaler Internet Access (ZIA)" in item.get("name", ""):
            return item
    return None


def iter_requests(item: dict, folder_path: list | None = None):
    """Yield (request_item, folder_names) for every leaf request."""
    if folder_path is None:
        folder_path = []
    if "request" in item:
        yield item, list(folder_path)
    for child in item.get("item", []):
        child_path = folder_path + [item["name"]] if item.get("name") else folder_path
        yield from iter_requests(child, child_path)


# ---------------------------------------------------------------------------
# Path + parameter extraction
# ---------------------------------------------------------------------------


def build_path_and_params(url_obj: dict):
    """
    Build an OpenAPI path string and extract path parameters.

    Returns (path_str, [path_param_defs]) or (None, []) if path can't be built.
    """
    if "path" not in url_obj:
        return None, []

    raw_segments = [s for s in url_obj.get("path", []) if s]
    if not raw_segments:
        return None, []

    path_params = []
    normalised = []
    prev_seg = None

    for seg in raw_segments:
        seg_norm = _normalise_path_segment(seg)

        # Already a variable like {dictId}
        if re.match(r"^\{\w+\}$", seg_norm):
            var_name = seg_norm.strip("{}")
            normalised.append(seg_norm)
            path_params.append(_make_path_param(var_name))
            prev_seg = seg_norm
            continue

        # Hardcoded sample ID -> replace with {paramName}
        if _is_sample_id(seg):
            param_name = _infer_param_name(prev_seg)
            # Avoid collisions in the same path
            existing_names = {p["name"] for p in path_params}
            if param_name in existing_names:
                param_name = param_name + "2"
            normalised.append("{" + param_name + "}")
            path_params.append(_make_path_param(param_name))
            prev_seg = "{" + param_name + "}"
            continue

        normalised.append(seg)
        prev_seg = seg

    path = "/api/v1/" + "/".join(normalised)
    # Clean up double slashes
    path = re.sub(r"/+", "/", path)
    if not path.startswith("/"):
        path = "/" + path

    return path, path_params


def _make_path_param(name: str) -> dict:
    return {
        "name": name,
        "in": "path",
        "required": True,
        "schema": {"type": "string"},
        "description": f"Unique identifier ({name})",
    }


def extract_query_params(url_obj: dict) -> list:
    """Extract query parameters from Postman URL object."""
    params = []
    for q in url_obj.get("query", []):
        if q.get("disabled", False):
            continue
        key = q.get("key", "")
        if not key:
            continue
        param = {
            "name": key,
            "in": "query",
            "required": False,
            "schema": {"type": "string"},
        }
        desc = q.get("description", "")
        if desc:
            param["description"] = desc
        val = q.get("value", "")
        if val:
            param["schema"]["example"] = val
        params.append(param)
    return params


# ---------------------------------------------------------------------------
# Request body extraction
# ---------------------------------------------------------------------------


def extract_request_body(request_obj: dict) -> dict | None:
    """
    Build an OpenAPI requestBody from a Postman request body.
    Parses raw JSON bodies to produce an example.
    """
    body = request_obj.get("body")
    if not body:
        return None

    mode = body.get("mode", "")

    if mode == "raw":
        raw = (body.get("raw") or "").strip()
        if not raw:
            return None

        # Try to parse as JSON to produce an example
        example = None
        try:
            example = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            pass

        schema: dict = {"type": "object"}
        if example is not None:
            schema["example"] = example

        return {
            "required": True,
            "content": {
                "application/json": {
                    "schema": schema,
                }
            },
        }

    if mode == "formdata":
        return {
            "required": True,
            "content": {
                "multipart/form-data": {"schema": {"type": "object"}},
            },
        }

    return None


# ---------------------------------------------------------------------------
# Post-processing: merge paths with conflicting param names
# ---------------------------------------------------------------------------


def _merge_conflicting_param_paths(paths: dict) -> dict:
    """
    Merge paths that are logically identical but have different parameter
    names.  e.g. /foo/{id} and /foo/{barId} should become /foo/{barId}.

    Strategy: group by normalised pattern (replace all {xxx} with {X}),
    pick the longest/most-descriptive param name as canonical, merge all
    methods under that single path, and rewrite parameter definitions.
    """
    import re as _re
    from collections import defaultdict

    groups = defaultdict(list)
    for path in paths:
        norm = _re.sub(r"\{[^}]+\}", "{X}", path)
        groups[norm].append(path)

    merged = {}
    for _norm, variants in groups.items():
        if len(variants) == 1:
            merged[variants[0]] = paths[variants[0]]
            continue

        # Pick canonical param names — prefer the longest (most descriptive)
        # Build a map of position -> best name
        split_variants = [v.split("/") for v in variants]
        canonical_segs = list(split_variants[0])  # start with first

        for seg_idx in range(len(canonical_segs)):
            if not _re.match(r"^\{.+\}$", canonical_segs[seg_idx]):
                continue
            # Collect all param names at this position
            names = set()
            for sv in split_variants:
                if seg_idx < len(sv) and _re.match(r"^\{.+\}$", sv[seg_idx]):
                    names.add(sv[seg_idx].strip("{}"))
            # Pick longest name
            best = max(names, key=len) if names else canonical_segs[seg_idx].strip("{}")
            canonical_segs[seg_idx] = "{" + best + "}"

        canonical_path = "/".join(canonical_segs)

        # Merge all methods under canonical path
        merged_methods = {}
        for variant in variants:
            for method, operation in paths[variant].items():
                if method in merged_methods:
                    continue  # first wins
                # Rewrite path param names in the operation's parameters
                if "parameters" in operation:
                    _rewrite_path_params(operation["parameters"], canonical_segs)
                merged_methods[method] = operation
        merged[canonical_path] = merged_methods

    return dict(sorted(merged.items()))


def _rewrite_path_params(params: list, canonical_segs: list):
    """Update path parameter names to match the canonical path segments."""
    import re as _re

    canonical_names = [
        seg.strip("{}") for seg in canonical_segs if _re.match(r"^\{.+\}$", seg)
    ]
    path_params = [p for p in params if p.get("in") == "path"]
    for i, pp in enumerate(path_params):
        if i < len(canonical_names):
            pp["name"] = canonical_names[i]
            pp["description"] = f"Unique identifier ({canonical_names[i]})"


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------


def convert(postman_path: str, output_path: str):
    print(f"Reading Postman collection: {postman_path}")
    with open(postman_path, "r", encoding="utf-8") as f:
        collection = json.load(f)

    zia = find_zia_section(collection)
    if not zia:
        print("ERROR: 'Zscaler Internet Access (ZIA)' section not found")
        sys.exit(1)

    print(f"Found ZIA section with {len(zia.get('item', []))} sub-folders")

    openapi: dict = {
        "openapi": "3.0.0",
        "info": {
            "title": "Zscaler OneAPI - Internet Access (ZIA)",
            "description": (
                "Zscaler OneAPI REST API for ZIA. Covers activation, admin "
                "management, DLP, firewall policies, URL filtering, user "
                "management, traffic forwarding, and more."
            ),
            "version": "1.0.0",
            "contact": {
                "name": "Zscaler Support",
                "url": "https://help.zscaler.com",
            },
        },
        "servers": [{"url": "{base_url}"}],
        "paths": {},
    }

    stats = {
        "total_requests": 0,
        "endpoints": 0,
        "merged_duplicates": 0,
        "skipped_duplicates": 0,
        "paths_with_params": 0,
        "paths_with_query": 0,
        "paths_with_body": 0,
    }

    for sub_folder in zia.get("item", []):
        tag = sub_folder.get("name", "General")

        for req_item, _folders in iter_requests(sub_folder):
            stats["total_requests"] += 1
            request = req_item.get("request", {})
            if not request:
                continue

            url_obj = request.get("url", {})
            if not url_obj:
                continue

            method = request.get("method", "GET").lower()
            name = req_item.get("name", "")

            # Build path with parameterised IDs
            api_path, path_params = build_path_and_params(url_obj)
            if not api_path:
                continue

            # Query parameters
            query_params = extract_query_params(url_obj)

            # Merge all parameters
            all_params = path_params + query_params

            # Build operation
            operation: dict = {
                "summary": name,
                "operationId": re.sub(r"[^a-zA-Z0-9_]", "_", name).strip("_")[:120],
                "tags": [tag],
                "responses": {"200": {"description": "Successful response"}},
            }

            if all_params:
                operation["parameters"] = all_params

            # Request body
            req_body = extract_request_body(request)
            if req_body:
                operation["requestBody"] = req_body
                stats["paths_with_body"] += 1

            # Add to spec, merging methods under the same path
            if api_path not in openapi["paths"]:
                openapi["paths"][api_path] = {}

            if method in openapi["paths"][api_path]:
                # Same method already exists — this is a true duplicate
                # (e.g. multiple filter variants on the same POST endpoint).
                # Keep the first one, skip subsequent.
                stats["skipped_duplicates"] += 1
                continue

            openapi["paths"][api_path][method] = operation
            stats["endpoints"] += 1

            if path_params:
                stats["paths_with_params"] += 1
            if query_params:
                stats["paths_with_query"] += 1

    # Sort paths for readability
    openapi["paths"] = dict(sorted(openapi["paths"].items()))

    # Post-process: merge paths that differ only in parameter names
    # e.g. /urlFilteringRules/{id}, /urlFilteringRules/{ruleid},
    #      /urlFilteringRules/{urlFilteringRuleId} -> single canonical path
    openapi["paths"] = _merge_conflicting_param_paths(openapi["paths"])
    stats["merged_duplicates"] = (
        stats["total_requests"] - stats["endpoints"] - stats["skipped_duplicates"]
    )

    # Write output
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi, f, indent=2, ensure_ascii=False)

    # Print stats
    print(f"\nConversion complete!")
    print(f"  Postman requests processed: {stats['total_requests']}")
    print(f"  OpenAPI operations created: {stats['endpoints']}")
    print(f"  Unique paths:              {len(openapi['paths'])}")
    print(f"  Duplicates merged:         {stats['merged_duplicates']}")
    print(f"  Duplicates skipped:        {stats['skipped_duplicates']}")
    print(f"  Operations with path params: {stats['paths_with_params']}")
    print(f"  Operations with query params:{stats['paths_with_query']}")
    print(f"  Operations with body:        {stats['paths_with_body']}")
    print(f"  Output: {output_path}")

    return openapi


def validate_with_parser(output_path: str):
    """Validate the output can be parsed by autobotAI's OpenApiParser."""
    try:
        # Try to find autobotAI_integrations in parent dirs
        base = os.path.dirname(os.path.abspath(__file__))
        for _ in range(5):
            candidate = os.path.join(base, "autobotAI_integrations")
            if os.path.isdir(candidate):
                sys.path.insert(0, os.path.dirname(candidate))
                break
            base = os.path.dirname(base)

        from autobotAI_integrations.utils.open_api_parser import OpenApiParser

        parser = OpenApiParser()
        parser.parse_file(output_path)

        actions = parser.get_actions("zscaler")

        # Count actions with actual user-visible parameters
        actions_with_params = sum(
            1
            for a in actions
            if len(a.parameters_definition) > 1  # >1 because 'method' is always added
        )

        print(f"\n  Parser validation: SUCCESS")
        print(f"  Parser found {len(parser.paths)} operations")
        print(f"  Actions generated: {len(actions)}")
        print(f"  Actions with parameters: {actions_with_params}")
        print(f"  Parser base_url: {parser.base_url}")
    except Exception as e:
        print(f"\n  Parser validation: FAILED — {e}")
        import traceback

        traceback.print_exc()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <postman_collection.json> [output.json]")
        sys.exit(1)

    postman_file = sys.argv[1]
    output_file = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.path.join(os.path.dirname(os.path.abspath(__file__)), "open_api.json")
    )

    convert(postman_file, output_file)
    validate_with_parser(output_file)
