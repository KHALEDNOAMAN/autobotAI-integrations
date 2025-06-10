# Import your modules here
import json  # noqa: F401
import traceback  # noqa: F401

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    """
    Executes provided Python code within integrations.

    Args:
        context (dict): A dictionary containing information about the current execution.
            - params (dict): A dictionary containing parameters specified while creating action.
            - clients (dict): A dictionary that contain selected client objects while defining action. (The specific clients present and their usage depend on the specific action being executed.)

    Returns:
        list: Always returns an empty list (`[]`) or a list containing the results of the code execution. The specific content of the returned list depends on the code and how it interacts with the integration.
    """

    client = context["clients"]["python_http_requests"]

    # Example Which fetches thee integrations using API
    # POST Request Example with json=
    payload = {
        "name": "Example Integration",
        "type": "webhook",
        "config": {"url": "https://example.com/webhook", "method": "POST"},
    }
    response = client.request("POST", "/integrations", json=payload)

    return response.json()

    # --- Additional examples for reference ---

    # # GET Request Example
    # response = client.request("GET", "/integrations")
    # print("GET /integrations:", response.status_code, response.json())

    # # Example with Query Parameters
    # params = {"status": "active"}
    # response_with_params = client.request("GET", "/integrations", params=params)
    # print("GET with query params:", response_with_params.status_code, response_with_params.json())

    # # Example with Custom Headers
    # custom_headers = {"X-Custom-Token": "abc123"}
    # response_with_headers = client.request("GET", "/integrations", headers=custom_headers)
    # print("GET with custom headers:", response_with_headers.status_code, response_with_headers.json())

    # # POST Request Example with data=
    # form_encoded_data = "name=Example+Integration&type=webhook"
    # response_data = client.request("POST", "/integrations", data=form_encoded_data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    # print("POST with data=", response_data.status_code, response_data.text)

    # # Error Handling Example
    # try:
    #     bad_response = client.request("GET", "/non-existent-endpoint")
    #     bad_response.raise_for_status()
    # except requests.exceptions.RequestException as e:
    #     print("Request failed:", e)
    #     print(traceback.format_exc())

    # return []
