import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


class TestClassTrivy:
    def test_trivy_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {}
        integration = sample_integration_dict("trivy", tokens)
        trivy_query = "select * from trivy_scan_vulnerability where artifact_type = 'container_image' and artifact_name = 'turbot/steampipe'"
        task = sample_steampipe_task(integration, query=trivy_query)
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {}
        integration = sample_integration_dict("trivy", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
