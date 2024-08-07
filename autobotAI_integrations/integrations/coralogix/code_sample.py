# Import your modules here
import json

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

    client = clients["dataPrimeApiClient"]

    # Example to fetch logs between certain dates
    # for more information about the use of api,
    # visit: https://coralogix.com/docs/direct-query-http-api/

    # data = client.run_query(**{
    #     "query": "source logs | limit 1",
    #     "metadata": {
    #         "tier": "TIER_FREQUENT_SEARCH",
    #         "syntax": "QUERY_SYNTAX_DATAPRIME",
    #         "startDate": "2024-08-05T11:20:00.00Z",
    #         "endDate": "2024-08-07T11:30:00.00Z",
    #         "defaultSource": "logs",
    #     },
    # })

    # # Your logic to proccess data
    # return data
