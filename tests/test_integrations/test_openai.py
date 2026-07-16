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

import json
import os

import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


def _env(get_keys, key: str, default=None):
    return get_keys.get(key) or os.environ.get(key) or default


def _get_openai_config(get_keys):
    api_key = _env(get_keys, "OPENAI_API_KEY")
    if not api_key:
        return None
    return {
        "api_key": api_key,
        "model": _env(get_keys, "OPENAI_MODEL", "gpt-5.4"),
    }


class TestOpenAI:
    def test_prompt_executor_chat_mode(self, get_keys, sample_integration_dict):
        config = _get_openai_config(get_keys)
        if not config:
            pytest.skip("OPENAI_API_KEY not set in .env or environment")

        integration = sample_integration_dict("openai", {"api_key": config["api_key"]})
        service = integration_service_factory.get_service(None, integration)

        result = service.prompt_executor(
            model=config["model"],
            prompt="Reply with exactly: hello",
            params="chat",
        )

        assert isinstance(result, str)
        assert result.strip()
        assert "error" not in result.lower() or "hello" in result.lower()

    def test_prompt_executor_json_mode(self, get_keys, sample_integration_dict):
        config = _get_openai_config(get_keys)
        if not config:
            pytest.skip("OPENAI_API_KEY not set in .env or environment")

        integration = sample_integration_dict("openai", {"api_key": config["api_key"]})
        service = integration_service_factory.get_service(None, integration)

        result = service.prompt_executor(
            model=config["model"],
            prompt='Return JSON only: {"status": "ok"}',
            params=None,
        )

        assert isinstance(result, str)
        assert result.strip()
        if result.startswith("{"):
            payload = json.loads(result)
            assert "error" not in payload

    def test_openai_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        config = _get_openai_config(get_keys)
        if not config:
            pytest.skip("OPENAI_API_KEY not set in .env or environment")

        tokens = {"api_key": config["api_key"]}
        integration = sample_integration_dict("openai", tokens)
        task = sample_python_task(
            integration, code=openai_python_code, clients=["Agent"]
        )
        result = handle_task(task)
        test_result_format(result)
        assert False
