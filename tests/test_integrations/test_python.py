import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

python_code = """
# Import your modules here
import json
import matplotlib

def executor(context):
    pass
    return {"data": "Hi"}
"""


class TestClassPython:
    def test_python_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "packages": "matplotlib",
        }
        integration = sample_integration_dict("python", tokens)
        task = sample_python_task(
            integration, code=python_code, clients=[]
        )
        result = handle_task(task)
        test_result_format(result)
        print(result.model_dump_json(indent=2))
        # Uncomment to see the output
        # assert False 

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "packages": "matplotlib",
        }
        integration = sample_integration_dict("python", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]
        # these is no key so this test is not required
        # tokens = {
        #     "packages": "matplotlib",
        # }
        # integration = sample_integration_dict("python", tokens)
        # service = integration_service_factory.get_service(None, integration)
        # res = service.is_active()
        # assert not res["success"]
