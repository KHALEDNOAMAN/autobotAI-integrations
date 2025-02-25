import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

coralogix_python_code = """
import traceback

def executor(context):
    print("in execute")
    try:
        client = context["clients"]["python_http_requests"]
        # method: str, endpoint: str, headers: dict = dict()
        response = client.request("GET","/integrations")
        print(response.json())
        return response.json()
    except Exception as e:
        print(traceback.format_exc())
    return {"success": True}
"""


class TestClassPythonHTTP:
    def test_http_request_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "api_url": get_keys["PYTHON_HTTP_API_URL"],
            "headers_json": get_keys["PYTHON_HTTP_HEADERS"],
            "ignore_ssl" : str(get_keys["PYTHON_HTTP_IGNORE_SSL"])
        }
        integration = sample_integration_dict("python_http_requests", tokens)
        task = sample_python_task(
            integration, code=coralogix_python_code, clients=["python_http_requests"]
        )
        result = handle_task(task)
        test_result_format(result)
        
        print(result.model_dump_json(indent=2))
        assert False

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "api_url": get_keys["PYTHON_HTTP_API_URL"],
            "headers_json": get_keys["PYTHON_HTTP_HEADERS"],
            "ignore_ssl" : str(get_keys["PYTHON_HTTP_IGNORE_SSL"])
        }
        integration = sample_integration_dict("python_http_requests", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]
        tokens = {
            "api_url": get_keys["PYTHON_HTTP_API_URL"][:-3],
            "headers_json": get_keys["PYTHON_HTTP_HEADERS"],
            "ignore_ssl" : str(get_keys["PYTHON_HTTP_IGNORE_SSL"])
        }
        integration = sample_integration_dict("python_http_requests", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
