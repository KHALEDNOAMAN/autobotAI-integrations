# Import your modules here
import json

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    """
    Executes a GitHub action to comment on a Pull Request.

    Args:
        context (dict):
            - params (dict):
                - repo (str): Repository in format "owner/repo".
                - pull_number (int): Pull request number.
                - comment (str): Comment text to post.
            - clients (dict): Contains GitHub client object (PyGithub) authenticated
                              with an Installation Access Token.
    Returns:
        list: Contains details of the posted comment or error details.
    """

    params = context["params"]
    clients = context["clients"]

    # GitHub client from PyGithub, authenticated with Installation Access Token
    client = clients["github"]

    repo_name = params["repo"]
    pull_number = params["pull_number"]
    comment_body = params["comment"]

    try:
        repo = client.get_repo(repo_name)
        pr = repo.get_pull(pull_number)
        comment = pr.create_issue_comment(comment_body)

        return [
            {
                "id": comment.id,
                "url": comment.html_url,
                "body": comment.body,
            }
        ]

    except Exception as e:
        return [
            {
                "error": str(e),
            }
        ]
