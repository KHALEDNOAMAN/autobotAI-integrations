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

    # Microsoft Uses Async Apis to get details with python
    async def me(client):
        res = []
        users = await client.users.get()
        if users and users.value:
            for user in users.value:
                res.append([user.id, user.display_name, user.mail])
        return res

    try:
        client = clients["msgraph"]
        return asyncio.run(me(client))
    except Exception as e:
        return {"error": e, "clients": context["clients"]}

    # return resources # Replace with your actual return logic
