import traceback
from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

sailpoint_python_code = """
from sailpoint.v2025.api.tenant_api import TenantApi
def executor(context):
    cli = context["clients"]["sailpoint"]

    tenant_api = TenantApi(cli).get_tenant()
    
    result = tenant_api.model_dump()
    
    return [{"result": result}]
"""


class TestClassSailPointIdentityNow:
    def test_integration_active(self, get_keys, sample_integration_dict):
        """Test SailPoint integration connection with valid credentials"""
        tokens = {
            "tenantname": get_keys["SAILPOINT_TENANTNAME"],
            "tenantdomain": get_keys["SAILPOINT_TENANTDOMAIN"],
            "username": get_keys["SAILPOINT_CLIENTID"],
            "password": get_keys["SAILPOINT_CLIENT_SECRET"],
        }
        integration = sample_integration_dict("sailpoint", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()

        assert res["success"], f"Integration connection failed: {res.get('error')}"

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("sailpoint")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0

    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {
            "tenantname": get_keys["SAILPOINT_TENANTNAME"],
            "tenantdomain": get_keys["SAILPOINT_TENANTDOMAIN"],
            "username": get_keys["SAILPOINT_CLIENTID"],
            "password": get_keys["SAILPOINT_CLIENT_SECRET"],
        }
        integration = sample_integration_dict("sailpoint", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            if action.name == "Get tenant information":
                try:
                    task = sample_restapi_task(
                        integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                    test_result_format(result)
                except Exception as e:
                    traceback.print_exc()

    def test_sailpoint_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "tenantname": get_keys["SAILPOINT_TENANTNAME"],
            "tenantdomain": get_keys["SAILPOINT_TENANTDOMAIN"],
            "username": get_keys["SAILPOINT_CLIENTID"],
            "password": get_keys["SAILPOINT_CLIENT_SECRET"],
        }
        integration = sample_integration_dict("sailpoint", tokens)
        task = sample_python_task(
            integration, code=sailpoint_python_code, clients=["sailpoint"]
        )
        result = handle_task(task)
        test_result_format(result)
