import traceback
import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
import requests
import json

cyberark_python_code = """
def executor(context):
    res = []
    user = context["clients"]["ArkIdentityUsersService"]
    info = user.user_info() 
    res.append(info)

    return res
"""

class TestClassCyberArkIdentity:

    def test_integration_active(self, get_keys, sample_integration_dict):
        """Test CyberArk integration connection with valid credentials"""
        tokens = {
            "base_url": get_keys["CYBERARK_BASE_URL"],
            "username": get_keys["CYBERARK_USERNAME"],
            "password": get_keys["CYBERARK_PASSWORD"],
        }
        integration = sample_integration_dict("cyberark_identity", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "base_url": get_keys["CYBERARK_BASE_URL"],
            "username": get_keys["CYBERARK_USERNAME"],
            "password": get_keys["CYBERARK_PASSWORD"],
        }
        integration = sample_integration_dict("cyberark_identity", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("cyberark_identity")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0

    def test_cyberark_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        """Test Cyberark integration with Python SDK - List Users"""

        tokens = {
            "base_url": get_keys["CYBERARK_BASE_URL"],
            "username": get_keys["CYBERARK_USERNAME"],
            "password": get_keys["CYBERARK_PASSWORD"],
        }
        integration = sample_integration_dict("cyberark_identity", tokens)
        task = sample_python_task(
            integration,
            code=cyberark_python_code,
            clients=["ArkIdentityUsersService", "ArkIdentityAPI"],
        )
        result = handle_task(task)
        test_result_format(result)
     


    def test_action_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {
            "base_url": get_keys["CYBERARK_BASE_URL"],
            "username": get_keys["CYBERARK_USERNAME"],
            "password":get_keys["CYBERARK_PASSWORD"]
        }
        integration = sample_integration_dict("cyberark_identity", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            # Get Users
            if action.name == 'Get users details':
                try:
                    task = sample_restapi_task(
                    integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                    test_result_format(result)
                except Exception as e:
                    traceback.print_exc() 