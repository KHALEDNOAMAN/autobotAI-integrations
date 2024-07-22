import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

github_python_code = """
def executor(context):
    gh = context["clients"]["github"]
    result = []
    for repo in gh.get_user().get_repos():
        details = {
            "name": repo.name,
            "url": repo.url,
            "stars_count": repo.stargazers_count,
        }
        result.append({
            "id": repo.id,
            "details": details,
        })
    return [{"result": result}]
"""


class TestClassGithub:
    def test_github_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {"token": get_keys["GITHUB_TOKEN"]}
        integration = sample_integration_dict("github", tokens)
        github_query = "select * from github_my_repository"
        task = sample_steampipe_task(integration, query=github_query)
        result = handle_task(task)
        test_result_format(result)

    def test_github_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {"token": get_keys["GITHUB_TOKEN"]}
        integration = sample_integration_dict("github", tokens)
        task = sample_python_task(
            integration, code=github_python_code, clients=["github"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {"token": get_keys["GITHUB_TOKEN"]}
        integration = sample_integration_dict("github", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {"token": get_keys["GITHUB_TOKEN"][:-2]}
        integration = sample_integration_dict("github", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
