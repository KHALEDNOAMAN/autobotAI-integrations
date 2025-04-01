import traceback

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassGithub:
    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {"token": get_keys["GITGUARDIAN_TOKEN"]}
        integration = sample_integration_dict("gitguardian", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {"token": get_keys["GITGUARDIAN_TOKEN"][:-2]}
        integration = sample_integration_dict("gitguardian", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("gitguardian")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
            print(action.model_dump_json(indent=2))
        assert len(actions) > 0

    # "Retrieve details of the current API token."
    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {"token": get_keys["GITGUARDIAN_TOKEN"]}
        integration = sample_integration_dict("gitguardian", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            if action.name.startswith("Retrieve details of the current API token"):
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
