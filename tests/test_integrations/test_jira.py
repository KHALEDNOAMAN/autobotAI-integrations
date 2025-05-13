import traceback
import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

jira_python_code = """
import traceback

def executor(context):
    print("in execute")
    jira = context["clients"]['jira']    
    try:
        results = []
        projects = jira.projects()
        for project in projects:
            results.append({
                "name": project.name,
                "key": project.key
            })
    except JiraApiError as e:
        print(f"Got an error: {e.response['error']}")
        return {
            "success": False
        }
    else:
        return results
"""


class TestClassJira:
    def test_jira_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "username": get_keys["JIRA_USER"],
            "base_url": get_keys["JIRA_URL"],
            "token": get_keys["JIRA_TOKEN"],
        }
        integration = sample_integration_dict("jira", tokens)
        task = sample_python_task(
            integration, code=jira_python_code, clients=["jira"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "username": get_keys["JIRA_USER"],
            "base_url": get_keys["JIRA_URL"],
            "token": get_keys["JIRA_TOKEN"],
        }
        integration = sample_integration_dict("jira", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "username": get_keys["JIRA_USER"],
            "base_url": get_keys["JIRA_URL"],
            "token": get_keys["JIRA_TOKEN"][:-2],
        }
        integration = sample_integration_dict("jira", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("jira")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
            print(action.model_dump_json(indent=2))
        assert len(actions) > 0

    "Get all projects"
    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {
            "username": get_keys["JIRA_USER"],
            "base_url": get_keys["JIRA_URL"],
            "token": get_keys["JIRA_TOKEN"],
        }
        integration = sample_integration_dict("jira", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            # print(action.name)
            if action.name == "Get all projects":
                params = action.parameters_definition
                action.parameters_definition = params
                try:
                    task = sample_restapi_task(
                        integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                    print(result.model_dump_json(indent=2))
                    test_result_format(result)
                except Exception as e:
                    traceback.print_exc()
                    assert False
