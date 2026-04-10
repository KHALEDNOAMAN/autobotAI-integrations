# Import your modules here
import json


def executor(context):
    """
    Executes Zscaler Workflow Automation API call using legacy ZWA client.
    """

    params = context["params"]
    clients = context["clients"]

    # Zscaler client (Legacy ZWA)
    client = clients["zscaler"]

    # Default parameters (aligned with your original config)
    test_body = params.get(
        "test_body",
        json.dumps({
            "fields": [
                {"name": "severity", "value": ["HIGH"]}
            ],
            "time_range": {"startTime": "2025-03-03T18:04:52.074Z", "endTime": "2026-04-09T18:04:52.074Z"}
        })
    )

    result = []

    # Ensure body is a dict
    if isinstance(test_body, str):
        body = json.loads(test_body)
    else:
        body = test_body

    # Execute SDK method
    # Reference: dlp_incidents.search_dlp_incidents
    response, status_code, err = client.zwa.dlp_incidents.dlp_incident_search(
        **body
    )
    print(response, status_code, err, body)

    if err:
        raise Exception(err)
    else:
        result.append({
            "status_code": status_code,
            "response": response
        })

    # Always return a list
    return result