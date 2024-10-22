import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

okta_python_code = """
import asyncio

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    params = context["params"]
    clients = context["clients"]

    # Placeholder for retrieving the integration-specific client if needed
    okta_client = clients["okta"]  # Supports only one client

    # example of usage, list all users first name and last name
    async def main():
        users, resp, err = await okta_client.list_users()
        res = []
        for user in users:
            res.append(
                {"First Name": user.profile.first_name, "Last Name": user.profile.last_name}
            )
        return res

    loop = asyncio.get_event_loop()
    return loop.run_until_complete(main())
"""


class TestClassOkta:
    def test_okta_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "host_url": get_keys["OKTA_CLIENT_ORGURL"],
            "token": get_keys["OKTA_CLIENT_TOKEN"],
        }
        integration = sample_integration_dict("okta", tokens)
        okta_query = "select * from okta_user"
        task = sample_steampipe_task(integration, query=okta_query)
        result = handle_task(task)
        test_result_format(result)

    def test_okta_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "host_url": get_keys["OKTA_CLIENT_ORGURL"],
            "token": get_keys["OKTA_CLIENT_TOKEN"],
        }
        integration = sample_integration_dict("okta", tokens)
        task = sample_python_task(
            integration, code=okta_python_code, clients=["okta"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "host_url": get_keys["OKTA_CLIENT_ORGURL"],
            "token": get_keys["OKTA_CLIENT_TOKEN"],
        }
        integration = sample_integration_dict("okta", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "host_url": get_keys["OKTA_CLIENT_ORGURL"],
            "token": get_keys["OKTA_CLIENT_TOKEN"][:-2],
        }
        integration = sample_integration_dict("okta", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
