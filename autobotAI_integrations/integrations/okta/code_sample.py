# Import your modules here
import asyncio

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


def executor(context):
    """
    Executes provided Python code within integrations.

    Args:
        context (dict): A dictionary containing information about the current execution.
            - params (dict): A dictionary containing parameters specified while creating action.
            - clients (dict): A dictionary that contain selected client objects while defining action. (The specific clients present and their usage depend on the specific action being executed.)

    Returns:
        list: Always returns an empty list (`[]`) or a list containing the results of the code execution. The specific content of the returned list depends on the code and how it interacts with the integration.
    """

    params = context["params"]
    clients = context["clients"]

    # Placeholder for retrieving the integration-specific client if needed
    okta_client = clients["okta"]  # Supports only one client

    # example of usage, list all users first name and last name
    # async def main():
    #     users, resp, err = await okta_client.list_users()
    #     res = []
    #     for user in users:
    #         res.append(
    #             {"First Name": user.profile.first_name, "Last Name": user.profile.last_name}
    #         )
    #     return res

    # loop = asyncio.get_event_loop()
    # return loop.run_until_complete(main())
