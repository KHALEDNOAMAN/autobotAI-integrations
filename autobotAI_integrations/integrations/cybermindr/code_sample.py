# CyberMindr — REST API code executor
# This integration uses the REST API interface to query CyberMindr's CTEM platform.
# Credentials (base_url + Authorization header) are injected automatically via
# generate_rest_api_creds(). Use context["params"] to pass arguments to your logic.


def executor(context):
    params = context.get("params", {})

    try:
        # --- Findings fetch with optional severity + pagination filters ---
        severity = params.get("severity", "")       # critical | high | medium | low | info
        status   = params.get("status", "")         # open | resolved | accepted | in_progress
        page     = params.get("page", 1)
        limit    = params.get("limit", 50)

        # Build query parameters — only include non-empty filters
        query_params = {
            "page":  page,
            "limit": limit,
        }
        if severity:
            query_params["severity"] = severity
        if status:
            query_params["status"] = status

        # The REST executor automatically attaches base_url and Authorization header.
        # Return the constructed call spec so the platform can execute it.
        return [
            {
                "status":       "ok",
                "endpoint":     "/api/v1/findings",
                "method":       "GET",
                "query_params": query_params,
                "note": (
                    "Pass 'severity' (critical/high/medium/low/info) and/or "
                    "'status' (open/resolved/accepted/in_progress) as params to filter results. "
                    "Use 'page' and 'limit' for pagination."
                ),
            }
        ]

    except Exception as e:
        return [{"status": "error", "error": str(e)}]
