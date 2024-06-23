import pytest, os, shutil
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

class TestTaskHandlerClass:

    @classmethod
    def setup_class(cls):
        pass

    @classmethod
    def teardown_class(cls):
        cloned_path = os.path.join(os.path.abspath(os.getcwd()), "tree")
        if os.path.exists(cloned_path):
            shutil.rmtree(cloned_path)

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
                if result.integration_type == "linux":
                    assert "host" in resource
                    assert "stdout_output" in resource

    def test_python_task(self, sample_integration_dict, sample_python_task, test_result_format):
        integration = sample_integration_dict(cspName="git")
        # default args: code:str, clients:list
        task = sample_python_task(integration)
        result = handle_task(task)
        cloned_path = os.path.join(os.path.abspath(os.getcwd()), "tree")
        if integration["cspName"] == "git":
            assert os.path.exists(cloned_path)
        test_result_format(result)

    def test_compliance_task(self):
        pass
