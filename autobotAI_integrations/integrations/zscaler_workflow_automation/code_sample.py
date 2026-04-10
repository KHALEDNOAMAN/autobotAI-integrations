# Import your modules here
import json


def executor(context):
    """
    Executes Zscaler Workflow Automation API call using legacy ZWA client.
    """

    params = context["params"]
    clients = context["clients"]
    print(context)

    client = clients["zscaler"]  # legacy ZWA client

    # Defaults (can be overridden via params)
    method = params.get("test_method", "post").lower()
    api = params.get("test_api", "/dlp/v1/incidents/search")
    body = params.get(
        "test_body",
        json.dumps({"fields": [{"name": "priority", "value": ["HIGH"]}]})
    )

    result = []

    try:
        # Parse body if string
        if isinstance(body, str):
            body = json.loads(body)

        # Legacy ZWA raw request pattern
        # Assumes client.zwa.request exists
        resp, status, err = client.zwa.request(
            method=method,
            path=api,
            json=body
        )

        if err:
            result.append({"error": str(err)})
        else:
            result.append({
                "status": status,
                "response": resp
            })

    except Exception as e:
        result.append({"error": str(e)})

    return result