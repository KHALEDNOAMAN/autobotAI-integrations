# Import your modules here

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.


async def executor(context):
    """
    Executes provided Python code within integrations.

    Args:
        context (dict): A dictionary containing information about the current execution.
            - params (dict): A dictionary containing parameters specified while creating action.
            - clients (dict): A dictionary that contains selected client objects while defining action.

    Returns:
        list: A list containing the results of the code execution.
    """

    clients = context["clients"]
    client = clients["msgraph"]

    res = []
    users = await client.users.get()
    if users and users.value:
        for user in users.value:
            res.append(
                {
                    "id": user.id,
                    "displayName": user.display_name,
                    "userPrincipalName": user.user_principal_name,
                }
            )

    return res
