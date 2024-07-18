# payload input format
# payload output format
# output is returning and output is printing
import pytest
from autobotAI_integrations.handlers.payload_handler import handle_payload


class TestPayloadHandlerClass:

    def test_python_payload_run(
        self,
        sample_payload,
        sample_python_task,
        sample_integration_dict,
        test_result_format,
    ):
        integration = sample_integration_dict(cspName="git")
        # default args: code:str, clients:list
        task = sample_python_task(integration)
        payload = sample_payload([task])
        results = handle_payload(payload, return_results = True)
        assert results is not None
        assert isinstance(results, dict)
        assert results.get("success")
        assert results.get("results")
        assert isinstance(results.get("results"), dict)
        assert results.get("results").get("job_id")
        assert isinstance(results.get("results").get("task_results"), list)

        for result in results.get("results").get("task_results"):
            test_result_format(result)

    def test_steampipe_payload_run(
        self,
        sample_payload,
        sample_steampipe_task,
        sample_integration_dict,
        test_result_format,
    ):
        integration = sample_integration_dict()
        # default args: code:str, clients:list
        task = sample_steampipe_task(integration)
        payload = sample_payload([task])
        results = handle_payload(payload, return_results=True)
        assert results is not None
        assert isinstance(results, dict)
        assert results.get("success")
        assert results.get("results")
        assert isinstance(results.get("results"), dict)
        assert results.get("results").get("job_id")
        assert isinstance(results.get("results").get("task_results"), list)

        for result in results.get("results").get("task_results"):
            test_result_format(result)
