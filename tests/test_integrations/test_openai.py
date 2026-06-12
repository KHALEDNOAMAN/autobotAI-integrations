openai_python_code = """
async def executor(context):
    agent_factory = context["clients"]["Agent"]
    agent = agent_factory('gpt-5.4')
    print('Agent type:', type(agent))
    print('Agent created successfully:', agent)
    response = await agent.run("hi! how are you?")

    print("Response:", response)
    print(response.output)

    return [{"agent_created": True, "type": str(type(agent)), "response": str(response)}]
"""

from autobotAI_integrations.handlers.task_handler import handle_task


class TestOpenAI:
    def test_openai_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "api_key": get_keys["OPENAI_API_KEY"],
        }
        integration = sample_integration_dict("openai", tokens)
        task = sample_python_task(
            integration, code=openai_python_code, clients=["Agent"]
        )
        result = handle_task(task)
        test_result_format(result)
        assert False