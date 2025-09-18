import traceback
import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

snowflake_python_code = """
# Import your modules here
import json

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    params = context["params"]
    clients = context["clients"]
    connection = clients["snowflake"]
    cursor = connection.cursor()
    res = dict()
    try:
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print("Databases:", databases)
        res['databases'] = databases
        # cursor.execute("SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE()")
        # role_warehouse = cursor.fetchone()
        # print("Current Role and Warehouse:", role_warehouse)

        # cursor.execute("SHOW TABLES IN DATABASE <Your-database>")
        # tables = cursor.fetchall()
        # print("Tables in Database:", tables)
    finally:
        cursor.close()
    return res
"""


class TestClassSnowflake:
    # def test_snowflake_steampipe_task(
    #     self,
    #     get_keys,
    #     sample_integration_dict,
    #     sample_steampipe_task,
    #     test_result_format,
    # ):
    #     tokens = {
    #         "account": get_keys["SNOWFLAKE_ACCOUNT"],
    #         "username": get_keys["SNOWFLAKE_USERNAME"],
    #         "password": get_keys["SNOWFLAKE_PASSWORD"],
    #         "region": get_keys["SNOWFLAKE_REGION"],
    #         "account_locator": get_keys["SNOWFLAKE_ACCOUNT_LOCATOR"],
    #     }
    #     integration = sample_integration_dict("snowflake", tokens)
    #     snowflake_query = "select * from snowflake_warehouse_metering_history;"
    #     task = sample_steampipe_task(integration, query=snowflake_query)
    #     result = handle_task(task)
    #     test_result_format(result)

    def test_snowflake_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "account": get_keys["SNOWFLAKE_ACCOUNT"],
            "username": get_keys["SNOWFLAKE_USERNAME"],
            "password": get_keys["SNOWFLAKE_PASSWORD"],
        }
        integration = sample_integration_dict("snowflake", tokens)
        task = sample_python_task(
            integration, code=snowflake_python_code, clients=["snowflake"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "account": get_keys["SNOWFLAKE_ACCOUNT"],
            "username": get_keys["SNOWFLAKE_USERNAME"],
            "password": get_keys["SNOWFLAKE_PASSWORD"],
        }
        integration = sample_integration_dict("snowflake", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]
        tokens = {
            "account": get_keys["SNOWFLAKE_ACCOUNT"],
            "username": get_keys["SNOWFLAKE_USERNAME"],
            "password": get_keys["SNOWFLAKE_PASSWORD"][:-2],
        }
        integration = sample_integration_dict("snowflake", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    # "List databases."
    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {
            "account": get_keys["SNOWFLAKE_ACCOUNT"],
            "username": get_keys["SNOWFLAKE_USERNAME"],
            "password": get_keys["SNOWFLAKE_PASSWORD"],
        }
        integration = sample_integration_dict("snowflake", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            if action.name == "List databases":
                try:
                    task = sample_restapi_task(
                        integration, action.code, action.parameters_definition
                    )
                    result = handle_task(task)
                    print(result.model_dump_json(indent=2))
                    test_result_format(result)
                    assert False
                except Exception as e:
                    traceback.print_exc()
                    assert False

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("snowflake")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0
