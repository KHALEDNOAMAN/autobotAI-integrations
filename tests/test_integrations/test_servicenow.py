import traceback
import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
import requests
import json

servicenow_python_code = """
def executor(context):
    servicenow = context["clients"]["servicenow"]
    
    gr = servicenow.GlideRecord("incident")
    gr.query()
    
    result = []
    for record in gr:
        details = {
            "number": record.number,
            "short_description": record.short_description,
            "priority": record.priority,
            "state": record.state,
        }
        result.append({
            "sys_id": record.sys_id,
            "details": details,
        })
    return [{"result": result}]
"""


class TestClassServiceNow:
   
    def test_get_user_info(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        """Test getting current user information"""
        tokens = {
            "base_url": get_keys["SERVICENOW_BASE_URL"],
            "username": get_keys["SERVICENOW_USERNAME"],
            "password": get_keys["SERVICENOW_PASSWORD"],
        }
        integration = sample_integration_dict("servicenow", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        
        action_found = False
        for action in actions:
            if action.name == "Get current user":
                action_found = True
                try:
                    task = sample_restapi_task(
                        integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                    print("Get Current User Result:")
                    print(result.model_dump_json(indent=2))
                    test_result_format(result)
                except Exception as e:
                    traceback.print_exc()
                    assert False, f"Action execution failed: {str(e)}"
                break

    def test_integration_active(self, get_keys, sample_integration_dict):
        """Test ServiceNow integration connection with valid credentials"""
        tokens = {
            "base_url": get_keys["SERVICENOW_BASE_URL"],
            "username": get_keys["SERVICENOW_USERNAME"],
            "password": get_keys["SERVICENOW_PASSWORD"],
        }
        integration = sample_integration_dict("servicenow", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        
        assert res["success"], f"Integration connection failed: {res.get('error')}"

    def test_servicenow_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        """Test ServiceNow integration with Python SDK - List Incidents"""

        tokens = {
            "base_url": get_keys["SERVICENOW_BASE_URL"],
            "username": get_keys["SERVICENOW_USERNAME"],
            "password": get_keys["SERVICENOW_PASSWORD"],
        }
        integration = sample_integration_dict("servicenow", tokens)
        task = sample_python_task(integration, code=servicenow_python_code, clients=["servicenow"])
        result = handle_task(task)
        test_result_format(result)
        # print(result.model_dump_json(indent=2))
        # assert False 
    # Read all Records from a table
    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {
        "base_url": get_keys["SERVICENOW_BASE_URL"], 
        "username": get_keys["SERVICENOW_USERNAME"],
        "password": get_keys["SERVICENOW_PASSWORD"],
        }
        integration = sample_integration_dict("servicenow", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()

        for action in actions:
            if action.name == "Retrieve records from a table":
                params = action.parameters_definition

                for param in params:
                    if param.name == "tableName":
                        param.values = "incident"

                    if param.name == "sysparm_limit":
                        param.values = "2"  
                    
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
                # assert False