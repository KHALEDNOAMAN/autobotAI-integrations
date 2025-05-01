# Import your modules here
import json
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

    params = context["params"]
    clients = context["clients"]

    # Placeholder for retrieving the integration-specific client if needed
    client = clients["bitbucket_cloud"]  # Supports only one client
    # To know about how to use the client, you can refer to the following link:
    # https://atlassian-python-api.readthedocs.io/bitbucket.html#bitbucket-cloud

    # User's Python code execution logic goes here
    # (Replace this comment with the your actual code)

    # Get all workspaces
    results = []

    for workspace in client.workspaces.each():
        workspace_data = {}
        workspace_data["name"] = workspace.name
        workspace_data["slug"] = workspace.slug
        workspace_data["uuid"] = workspace.uuid
        workspace_data["created_on"] = workspace.created_on
        workspace_data["updated_on"] = workspace.updated_on
        workspace_data["is_private"] = workspace.is_private
        results.append(workspace_data)

    return results