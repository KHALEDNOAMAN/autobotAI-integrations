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

    # Retrieve the Azure DevOps Connection client object
    connection = clients["azure_devops"]  # Supports azure.devops.connection.Connection
    # For documentation on how to use the client, refer to:
    # https://github.com/microsoft/azure-devops-python-api

    # Get the Core client to interact with projects and teams
    core_client = connection.clients.get_core_client()
    git_client = connection.clients.get_git_client()

    results = []

    # Get top 50 projects in the organization
    projects = core_client.get_projects(top=50)
    if projects:
        for project in projects:
            project_data = {
                "project_id": project.id,
                "project_name": project.name,
                "description": project.description,
                "state": str(project.state) if project.state else None,
                "visibility": str(project.visibility) if project.visibility else None,
                "repositories": [],
            }

            # Retrieve git repositories inside each project
            try:
                repos = git_client.get_repositories(project_id=project.id)
                if repos:
                    for repo in repos:
                        project_data["repositories"].append(
                            {
                                "repo_id": repo.id,
                                "repo_name": repo.name,
                                "default_branch": repo.default_branch,
                                "web_url": repo.web_url,
                                "size": repo.size,
                            }
                        )
            except Exception as e:
                project_data["error_fetching_repos"] = str(e)

            results.append(project_data)

    return results
