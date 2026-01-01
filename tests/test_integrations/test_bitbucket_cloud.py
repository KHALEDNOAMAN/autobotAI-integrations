import traceback
import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

bit_bucket_cloud_python_code = """
def executor(context):
    bitbucket = context["clients"]["bitbucket_cloud"]
    results = []

    for workspace in bitbucket.workspaces.each():
        workspace_data = {}
        workspace_data["name"] = workspace.name
        workspace_data["slug"] = workspace.slug
        workspace_data["uuid"] = workspace.uuid
        workspace_data["created_on"] = workspace.created_on
        workspace_data["updated_on"] = workspace.updated_on
        workspace_data["is_private"] = workspace.is_private
        results.append(workspace_data)

    return results

"""


class TestClassbit_bucket_cloud:
    def test_bit_bucket_cloud_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "username": get_keys["BITBUCKET_CLOUD_KEY"],
            "password": get_keys["BITBUCKET_CLOUD_SECRET"],
        }
        integration = sample_integration_dict("bitbucket_cloud", tokens)
        task = sample_python_task(
            integration, code=bit_bucket_cloud_python_code, clients=["bitbucket_cloud"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "username": get_keys["BITBUCKET_CLOUD_KEY"],
            "password": get_keys["BITBUCKET_CLOUD_SECRET"],
        }
        integration = sample_integration_dict("bitbucket_cloud", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "username": get_keys["BITBUCKET_CLOUD_KEY"],
            "password": get_keys["BITBUCKET_CLOUD_SECRET"][:-2],
        }
        integration = sample_integration_dict("bitbucket_cloud", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("bitbucket_cloud")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
            print(action.model_dump_json(indent=2))
        assert len(actions) > 0

    # "Get a repository"
    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {
            "username": get_keys["BITBUCKET_CLOUD_KEY"],
            "password": get_keys["BITBUCKET_CLOUD_SECRET"],
        }
        integration = sample_integration_dict("bitbucket_cloud", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            if action.name == "Get a repository":
                params = action.parameters_definition
                for param in params:
                    if param.name == "repo_slug":
                        param.values = "test-repo-2026"
                    if param.name == "workspace":
                        param.values = "abhishek-rathod"
                action.parameters_definition = params
                try:
                    task = sample_restapi_task(
                        integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                    test_result_format(result)
                except Exception as e:
                    traceback.print_exc()
