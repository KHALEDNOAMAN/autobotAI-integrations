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

import json
import os

import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory


def _env(get_keys, key: str, default=None):
    return get_keys.get(key) or os.environ.get(key) or default


def _get_bedrock_config(get_keys):
    access_key = _env(get_keys, "AWS_ACCESS_KEY_ID")
    secret_key = _env(get_keys, "AWS_SECRET_ACCESS_KEY")
    region = _env(get_keys, "AWS_REGION")
    if not all([access_key, secret_key, region]):
        return None

    tokens = {
        "access_key": access_key,
        "secret_key": secret_key,
        "region": region,
        "chat_model": _env(
            get_keys,
            "BEDROCK_CHAT_MODEL_ID",
            "global.amazon.nova-2-lite-v1:0",
        ),
        "json_model": _env(
            get_keys,
            "BEDROCK_JSON_MODEL_ID",
            "global.anthropic.claude-sonnet-4-6",
        ),
    }
    session_token = _env(get_keys, "AWS_SESSION_TOKEN")
    if session_token:
        tokens["session_token"] = session_token
    return tokens


class TestAwsBedrock:
    def test_prompt_executor_chat_mode(self, get_keys, sample_integration_dict):
        config = _get_bedrock_config(get_keys)
        if not config:
            pytest.skip(
                "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION "
                "must be set in .env or environment"
            )

        integration = sample_integration_dict(
            "aws_bedrock",
            {
                "access_key": config["access_key"],
                "secret_key": config["secret_key"],
                "session_token": config.get("session_token"),
                "region": config["region"],
            },
        )
        service = integration_service_factory.get_service(None, integration)

        result = service.prompt_executor(
            model=config["chat_model"],
            prompt="Reply with exactly: hello",
            params="chat",
        )

        assert isinstance(result, str)
        assert result.strip()
        if result.startswith("{"):
            payload = json.loads(result)
            assert "error" not in payload

    def test_prompt_executor_json_mode(self, get_keys, sample_integration_dict):
        config = _get_bedrock_config(get_keys)
        if not config:
            pytest.skip(
                "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION "
                "must be set in .env or environment"
            )

        integration = sample_integration_dict(
            "aws_bedrock",
            {
                "access_key": config["access_key"],
                "secret_key": config["secret_key"],
                "session_token": config.get("session_token"),
                "region": config["region"],
            },
        )
        service = integration_service_factory.get_service(None, integration)

        result = service.prompt_executor(
            model=config["json_model"],
            prompt='Return JSON only: {"status": "ok"}',
            params=None,
        )

        assert isinstance(result, str)
        assert result.strip()
        if result.startswith("{"):
            payload = json.loads(result)
            assert "error" not in payload

    def test_aws_bedrock_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        config = _get_bedrock_config(get_keys)
        if not config:
            pytest.skip(
                "AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION "
                "must be set in .env or environment"
            )

        tokens = {
            "access_key": config["access_key"],
            "secret_key": config["secret_key"],
            "session_token": config.get("session_token"),
            "region": config["region"],
        }
        integration = sample_integration_dict("aws_bedrock", tokens)
        task = sample_python_task(
            integration, code=aws_bedrock_python_code, clients=["Agent"]
        )
        result = handle_task(task)
        test_result_format(result)
        assert False