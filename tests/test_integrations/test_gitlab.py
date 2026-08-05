import traceback
import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.models import ConnectionInterfaces

gitlab_python_code = """
import traceback

def executor(context):
    print("in execute")
    gl = context["clients"]['gitlab']    
    current_user = gl.user
    # print(current_user)
    group = gl.groups.get(109266189)    
    pj = []
    for project in group.projects.list(iterator=True):
        # print(project)
        pj.append(project.asdict())

    return pj
"""


class TestClassGitlab:
    def test_gitlab_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {"token": get_keys["GITLAB_TOKEN"]}
        integration = sample_integration_dict("gitlab", tokens)
        task = sample_python_task(
            integration, code=gitlab_python_code, clients=["gitlab"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {"token": get_keys["GITLAB_TOKEN"]}
        integration = sample_integration_dict("gitlab", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {"token": get_keys["GITLAB_TOKEN"][:-2]}
        integration = sample_integration_dict("gitlab", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("gitlab")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
            print(action.model_dump_json(indent=2))
        assert len(actions) > 0

    def test_mcp_server(self, sample_integration_dict):
        service_cls = integration_service_factory.get_service_cls("gitlab")
        assert ConnectionInterfaces.MCP_SERVER in service_cls.supported_connection_interfaces()

        actions = service_cls.get_all_mcp_server_actions()
        expected_names = {
            "GitLab All",
            "GitLab Issues",
            "GitLab Merge Requests",
            "GitLab Pipelines",
            "GitLab Work Items",
            "GitLab Search",
            "GitLab Wiki",
            "GitLab Semantic Code Search",
            "GitLab Security Scan Profiles",
            "GitLab MCP Server Version",
        }
        assert {action.name for action in actions} == expected_names
        for action in actions:
            assert action.code == "{base_url}/api/v4/mcp"
            assert action.executable_type == "mcp_server"

        for base_url in (
            "https://gitlab.com/",
            "https://gitlab.example.com/",
            "http://gitlab.example.com/",
        ):
            integration = sample_integration_dict(
                "gitlab",
                {"token": "glpat-test-token", "base_url": base_url},
            )
            service = integration_service_factory.get_service(None, integration)
            creds = service.generate_mcp_creds()
            assert creds.headers == {
                "Authorization": "Bearer glpat-test-token",
            }

    # "Get applications"
    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {"token": get_keys["GITLAB_TOKEN"]}
        integration = sample_integration_dict("gitlab", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            if (
                action.name
                == "Gets a list of group badges viewable by the authenticated user."
            ):
                params = action.parameters_definition
                for param in params:
                    if param.name == "id":
                        param.values = "109266189"
                    # if param.name == "repo":
                    #     param.values = "<repo-value>"
                action.parameters_definition = params
                try:
                    task = sample_restapi_task(
                        integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                    print(result.model_dump_json(indent=2))
                    test_result_format(result)
                    assert False
                except Exception as e:
                    traceback.print_exc()
                    assert False
