from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

databricks_python_code = """
# Import your modules here
import json

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    clients = context["clients"]
    workspace_client = clients["WorkspaceClient"]

    # Example: List All Users directory inside workspace
    res = []
    for user in workspace_client.workspace.list('/Users'):
        res.append(user.as_dict())
    
    return res
"""


class TestClassSnowflake:
    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "account_host": get_keys["DATABRICKS_ACCOUNT_HOST"],
            "account_id": get_keys["DATABRICKS_ACCOUNT_ID"],
            "workspace_host": get_keys["DATABRICKS_HOST"],
            "client_id": get_keys["DATABRICKS_CLIENT_ID"],
            "client_secret": get_keys["DATABRICKS_CLIENT_SECRET"],
        }
        integration = sample_integration_dict("databricks", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "account_host": get_keys["DATABRICKS_ACCOUNT_HOST"],
            "account_id": get_keys["DATABRICKS_ACCOUNT_ID"],
            "workspace_host": get_keys["DATABRICKS_HOST"],
            "client_id": get_keys["DATABRICKS_CLIENT_ID"],
            "client_secret": get_keys["DATABRICKS_CLIENT_SECRET"][:-2],
        }
        integration = sample_integration_dict("databricks", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_databricks_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "account_host": get_keys["DATABRICKS_ACCOUNT_HOST"],
            "account_id": get_keys["DATABRICKS_ACCOUNT_ID"],
            "workspace_host": get_keys["DATABRICKS_HOST"],
            "client_id": get_keys["DATABRICKS_CLIENT_ID"],
            "client_secret": get_keys["DATABRICKS_CLIENT_SECRET"],
        }
        integration = sample_integration_dict("databricks", tokens)
        snowflake_query = "select * from databricks_workspace;"
        task = sample_steampipe_task(integration, query=snowflake_query)
        result = handle_task(task)
        test_result_format(result)

    def test_databricks_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "account_host": get_keys["DATABRICKS_ACCOUNT_HOST"],
            "account_id": get_keys["DATABRICKS_ACCOUNT_ID"],
            "workspace_host": get_keys["DATABRICKS_HOST"],
            "client_id": get_keys["DATABRICKS_CLIENT_ID"],
            "client_secret": get_keys["DATABRICKS_CLIENT_SECRET"],
        }
        integration = sample_integration_dict("databricks", tokens)
        task = sample_python_task(
            integration, code=databricks_python_code, clients=["WorkspaceClient"]
        )
        result = handle_task(task)
        test_result_format(result)
