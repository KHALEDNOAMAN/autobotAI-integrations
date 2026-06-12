aws_bedrock_python_code = """
async def executor(context):
    agent_factory = context["clients"]["Agent"]
    agent = agent_factory('global.anthropic.claude-opus-4-6-v1')
    print('Agent type:', type(agent))
    print('Agent created successfully:', agent)
    response = await agent.run("Hello world")

    print("Response:", response)
    print(response.output)

    return [{"agent_created": True, "type": str(type(agent)), "response": str(response)}]
"""

from autobotAI_integrations.handlers.task_handler import handle_task


class TestAwsBedrock:
    def test_aws_bedrock_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "access_key": get_keys["AWS_ACCESS_KEY_ID"],
            "secret_key": get_keys["AWS_SECRET_ACCESS_KEY"],
            "session_token": get_keys.get("AWS_SESSION_TOKEN"),
            "region": get_keys["AWS_REGION"],
        }
        integration = sample_integration_dict("aws_bedrock", tokens)
        task = sample_python_task(
            integration, code=aws_bedrock_python_code, clients=["Agent"]
        )
        result = handle_task(task)
        test_result_format(result)
        assert False