import uuid
import pytest
from dotenv import dotenv_values
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.models import ConnectionInterfaces
from autobotAI_integrations.payload_schema import PayloadTask, PayloadTaskContext

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
