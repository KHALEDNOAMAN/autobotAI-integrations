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

    # OpenRouter is OpenAI-compatible; the client is exposed under "openai".
    client = clients["openai"]

    # User's Python code execution logic goes here
    # (Replace this comment with your actual code)

    # Example: chat completion through OpenRouter (for illustration purposes only)
    # completion = client.chat.completions.create(
    #     model="openai/gpt-4o-mini",
    #     messages=[
    #         {"role": "user", "content": "Explain the difference between TCP and UDP in one paragraph."}
    #     ],
    # )

    # return [{"result": completion.choices[0].message.content}]
