# Proofpoint DLP — REST API code executor
# The REST API interface is the primary integration method for Proofpoint DLP.
# Use the context["params"] dict to pass arguments to your logic.
# For REST_API integrations, credentials are injected automatically via headers.

def executor(context):
    params = context["params"]

    # Example: Fetch security events using the REST client
    # The base_url and Authorization header are already set by generate_rest_api_creds()
    # Access them via context if needed, or use the action parameters directly.
    try:
        created_after = params.get("created_after", "")
        limit = params.get("limit", 100)

        # Build query parameters
        query_params = {"limit": limit}
        if created_after:
            query_params["created_after"] = created_after

        return [
            {
                "status": "ok",
                "params_received": list(params.keys()),
                "query_params": query_params,
            }
        ]
    except Exception as e:
        return [{"status": "error", "error": str(e)}]
