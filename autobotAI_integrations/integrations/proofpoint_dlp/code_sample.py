# Proofpoint DLP — Python SDK executor
# Use the REST API interface for all Proofpoint calls.
# The `clients` dict is empty for REST_API integrations —
# use the context params to pass arguments to your logic.

def executor(context):
    params = context["params"]
    clients = context["clients"]

    # Example: inspect what params were passed in
    return [{"status": "ok", "params_received": list(params.keys())}]
