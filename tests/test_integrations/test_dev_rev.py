from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
import traceback



class TestClassDevRev:
    def test_dev_rev_token(
        self,
        get_keys,
        sample_integration_dict,
        test_result_format,
    ):
        tokens = {"api_key": get_keys["DEV_REV_API_KEY"]}
        integration = sample_integration_dict("dev_rev", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]

        tokens = {
            "api_key": get_keys["DEV_REV_API_KEY"][:-3],
        }
        integration = sample_integration_dict("dev_rev", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("dev_rev")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0
    
    # def test_actions_run(
    #     self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    # ):
    #     tokens = {"api_key": get_keys["DEV_REV_API_KEY"]}
    #     integration = sample_integration_dict("dev_rev", tokens)
    #     service = integration_service_factory.get_service(None, integration)
    #     actions = service.get_all_rest_api_actions()
    #     for action in actions:
    #         try:
    #             # In most Cases this will fail as parameters_definition does not contains actual values
    #             task = sample_restapi_task(
    #                 integration, action.code, action.parameters_definition
    #             )
    #             result = handle_task(task)
    #             print(result.model_dump_json(indent=2))
    #             test_result_format(result)
    #         except Exception as e:
    #             traceback.print_exc()