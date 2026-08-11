# Import your modules here
import traceback  # noqa: F401

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    """
    Executes provided Python code within integrations.

    Args:
        context (dict): A dictionary containing information about the current execution.
            - params (dict): A dictionary containing parameters specified while creating action.
            - clients (dict): A dictionary that contain selected client objects while defining action.

    Returns:
        list: Always returns an empty list (`[]`) or a list containing the results of the code execution.
    """

    client = context["clients"]["palo_alto_scm"]

    # List devices from Strata Cloud Manager
    response = client.request("GET", "/config/setup/v1/devices")
    response.raise_for_status()
    return response.json().get("data", [])

    # --- Additional examples for reference ---

    # # List folders
    # response = client.request("GET", "/config/setup/v1/folders")
    # return response.json().get("data", [])

    # # List address objects in a folder
    # response = client.request(
    #     "GET",
    #     "/config/objects/v1/addresses",
    #     params={"folder": "Shared"},
    # )
    # return response.json().get("data", [])

    # # List security rules in a folder
    # response = client.request(
    #     "GET",
    #     "/config/security/v1/security-rules",
    #     params={"folder": "Shared"},
    # )
    # return response.json().get("data", [])
