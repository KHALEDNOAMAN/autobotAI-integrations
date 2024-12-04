from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

alienvault_python_code = """

# Import your modules here
from OTXv2 import IndicatorTypes

# Security Note: Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):

    params = context["params"]
    clients = context["clients"]

    # Placeholder for retrieving the integration-specific client if needed
    client = clients["OTXv2"]  # Supports only one client
    # Use code parameters
    print(params)

    # Example: # Get everything OTX knows about google.com
    # for full details visit: https://github.com/AlienVault-OTX/OTX-Python-SDK?tab=readme-ov-file

    return client.get_indicator_details_full(IndicatorTypes.DOMAIN, "google.com")

"""

class TestClassAlienvault:
    def test_alienvault_token(
        self,
        get_keys,
        sample_integration_dict,
        test_result_format,
    ):
        tokens = {
            "token": get_keys["ALIENVAULT_OTX_TOKEN"],
        }
        integration = sample_integration_dict("alienvault_otx", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]

        tokens = {
            "token": get_keys["ALIENVAULT_OTX_TOKEN"][:-2],
        }
        integration = sample_integration_dict("alienvault_otx", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_alienvault_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "token": get_keys["ALIENVAULT_OTX_TOKEN"],
        }
        integration = sample_integration_dict("alienvault_otx", tokens)
        task = sample_python_task(integration, code=alienvault_python_code, clients=["OTXv2"])
        result = handle_task(task)
        test_result_format(result)

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls('alienvault_otx')
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0
