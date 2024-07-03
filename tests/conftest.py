from typing import Union
import uuid
import pytest
from dotenv import dotenv_values
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.models import ConnectionInterfaces
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext, TaskResult
import json

@pytest.fixture
def keys():
    keys = dotenv_values(".env")
    return keys


@pytest.fixture
def sample_integration_dict():
    def _sample_integration_dict(cspName: str="linux", tokens: dict = {}):
        return {
            "userId": "test@pytest.com*",
            "accountId": uuid.uuid4().hex,
            "cspName": cspName.lower(),
            "alias": f"test-{cspName}-integration",
            **tokens,
        }
    return _sample_integration_dict


@pytest.fixture
def sample_context_data():
    return {
        "execution_details": {
            "execution_id": uuid.uuid4().hex,
            "bot_id": uuid.uuid4().hex,
            "bot_name": "test-bot",
            "node_name": "test-node",
            "caller": {
                "user_id": "test@pytest.com",
                "root_user_id": "test@pytest.com",
            },
        },
        "node_steps": {},
    }


@pytest.fixture
def sample_python_task(sample_context_data):
    def _sample_python_task(integration: dict, code= "", clients = ["git"]):
        service = integration_service_factory.get_service(None, integration)
        integration = service.integration
        creds = service.generate_python_sdk_creds()
        executable = """
def executor(context):
    git = context["clients"]["git"]
    repo_url = "https://github.com/gitpython-developers/QuickStartTutorialFiles.git"
    repo = git.Repo.clone_from(repo_url, "tree")
    return [{"result": True}]
"""
        if code != "":
            executable = code
        task_dict = {
            "task_id": uuid.uuid4().hex,
            "creds": creds,
            "connection_interface": ConnectionInterfaces.PYTHON_SDK,
            "executable": executable,
            "clients": clients,
            "context": PayloadTaskContext(
                **sample_context_data,
                **{"integration": service.integration},
            ),
        }
        return PayloadTask(**task_dict)

    return _sample_python_task


@pytest.fixture
def sample_steampipe_task(sample_context_data):
    def _sample_steampipe_task(integration: dict, config_str: str = ""):
        service = integration_service_factory.get_service(None, integration)
        integration = service.integration
        creds = service.generate_steampipe_creds()
        if config_str != "":
            creds.config = config_str
        task_dict = {
            "task_id": uuid.uuid4().hex,
            "creds": creds,
            "connection_interface": ConnectionInterfaces.STEAMPIPE,
            "executable": "select _ctx ->> 'connection_name' as host, stdout_output from exec_command where command = 'ls -la';",
            "context": PayloadTaskContext(
                **sample_context_data,
                **{"integration": service.integration},
            ),
        }
        return PayloadTask(**task_dict)
    return _sample_steampipe_task


@pytest.fixture
def test_result_format():
    def _test_result_format(result):
        if not isinstance(result, dict):
            result = result.model_dump()
        assert isinstance(result.get("resources"), list)
        assert isinstance(result.get("errors"), list)
        if result.get("resources"):
            for resource in result.get("resources"):
                assert "integration_id" in resource
                assert "integration_type" in resource
                assert "user_id" in resource
                assert "root_user_id" in resource
        assert "task_id" in result
        assert "integration_id" in result
        assert "integration_type" in result
        assert "debug_info" in result

    return _test_result_format


@pytest.fixture
def sample_payload():
    def _sample_payload(task: PayloadTask):
        payload = {
            "job_id": str(uuid.uuid4().hex),
            "tasks": [task],
        }
        payload = Payload(**payload).model_dump()
        json_payload = json.dumps(payload)
        payload = json.loads(json_payload)
        return payload
    return _sample_payload
