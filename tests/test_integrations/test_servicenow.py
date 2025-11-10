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

    def test_actions_run_create_incident(self, get_keys):
        """Directly test creating an incident in ServiceNow via REST API"""

        base_instance_url = get_keys["SERVICENOW_BASE_URL"]
        api_url = f"{base_instance_url}/api/now/table/incident"

        username = get_keys["SERVICENOW_USERNAME"]
        password = get_keys["SERVICENOW_PASSWORD"]

        payload = {
        "short_description": "Tuk tuk test incident creation",
        "description": "This is a test incident created for automated testing purposes",
        "urgency": "2",   
        "impact": "2",   
        "priority": "3",  
        "category": "software"
        }

        try:
            response = requests.post(
            api_url,
            auth=(username, password),
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload)
        )

            assert response.status_code in [200, 201], f"Failed to create incident. Got: {response.status_code}"
            data = response.json()

        # Extract sys_id or number for validation
            if "result" in data:
                sys_id = data["result"].get("sys_id")
                number = data["result"].get("number")
            else:
                raise ValueError("No result found in response")

        except Exception as e:
            traceback.print_exc()
            assert False, f"Incident creation test failed: {str(e)}"
