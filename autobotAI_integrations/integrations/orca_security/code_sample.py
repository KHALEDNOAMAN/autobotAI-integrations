# Orca Security — REST API code executor
# This integration uses the REST API interface to query the Orca Security CNAPP platform.
# Credentials (base_url + Authorization: Token header) are injected automatically via
# generate_rest_api_creds(). Use context["params"] to pass arguments to your logic.


def executor(context):
    params = context.get("params", {})

    try:
        # --- Alert fetch with optional severity + status filters ---
        severity = params.get("severity", "")   # critical | high | medium | low | informational
        status   = params.get("status", "")     # open | closed | in_progress | dismissed

        valid_severities = ["critical", "high", "medium", "low", "informational"]
        valid_statuses   = ["open", "closed", "in_progress", "dismissed"]

        if severity and severity not in valid_severities:
            return [{
                "status": "error",
                "error": f"Invalid severity: '{severity}'. Must be one of: {', '.join(valid_severities)}."
            }]

        if status and status not in valid_statuses:
            return [{
                "status": "error",
                "error": f"Invalid status: '{status}'. Must be one of: {', '.join(valid_statuses)}."
            }]

        # Build query parameters — only include non-empty filters
        query_params = {"limit": params.get("limit", 20)}

        if severity:
            query_params["severity"] = severity
        if status:
            query_params["status"] = status

        # The REST executor automatically attaches base_url and Authorization header.
        return [
            {
                "status":       "ok",
                "endpoint":     "/api/query/alerts",
                "method":       "GET",
                "query_params": query_params,
                "note": (
                    "Pass 'severity' (critical/high/medium/low/informational) and/or "
                    "'status' (open/closed/in_progress/dismissed) as params to filter results. "
                    "Use 'limit' for page size (default 20, max 10000)."
                ),
            }
        ]

    except Exception as e:
        return [{"status": "error", "error": str(e)}]
