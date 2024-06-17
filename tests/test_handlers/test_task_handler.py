import pytest
from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.payload_schema import TaskResult

# test cases
# 1. Steampipe Task --> Done
# 2. Python task --> Done
# 3. compliance task --> Pending
# It should run all of them and provide results

# if errors: task should have errors in list format
# if resource: task result should be in list format
# task result format: check if contains necessary keys

@pytest.fixture
def test_result_format():
    def _test_result_format(result):
        assert isinstance(result.resources, list)
        assert isinstance(result.errors, list)
        assert isinstance(result, TaskResult)
        if result.resources:
            for resource in result.resources:
                assert "id" in resource
                assert "name" in resource
                assert "integration_id" in resource
                assert "integration_type" in resource
                assert "user_id" in resource
                assert "root_user_id" in resource
        assert hasattr(result, "task_id")
        assert hasattr(result, "integration_id")
        assert hasattr(result, "integration_type")
        assert hasattr(result, "debug_info")
    return _test_result_format


class TestTaskHandlerClass:

    def test_steampipe_task(
        self, sample_integration_dict, sample_steampipe_task, test_result_format
    ):
        integration = sample_integration_dict()
        task = sample_steampipe_task(integration)
        result = handle_task(task)
        test_result_format(result)
        if result.resources:
            for resource in result.resources:
                assert 'id' in resource
                assert "name" in resource

    def test_python_task(self, sample_integration_dict, sample_python_task, test_result_format):
        integration = sample_integration_dict(cspName="git")
        # default args: code:str, clients:list
        task = sample_python_task(integration)
        result = handle_task(task)
        test_result_format(result)
        
    def test_compliance_task(self):
        pass
