import os
import uuid
import dotenv

from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations.uptimerobot import UptimeRobotIntegrations
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import (
    Payload,
    PayloadTask,
    PayloadTaskContext,
)
from autobotAI_integrations.handlers import handle_payload

dotenv.load_dotenv()

uptimerobot_json = {
    "userId": "ritin.tiwari001@gmail.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "cspName": "uptimerobot",
    "api_key": os.environ["UPTIMEROBOT_API_KEY"],
    "alias": "test-uptimerobot-integrations2*",
    "groups": ["uptimerobot", "shunyeka", "integrations-v2"],
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
}

context = {
    "execution_details": {
        "execution_id": "660275c610755f71b634e572",
        "bot_id": "660274d5fa724e7537a4c0c5",
        "bot_name": "Uptimeorbot Integrations-V2 Test",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "amit@shunyeka.com", "root_user_id": "amit@shunyeka.com"},
    },
    "node_steps": {},
    "global_variables": {},
}


def generate_uptimerobot_steampipe_payload(uptimerobot_json=uptimerobot_json):
    integration = UptimeRobotIntegrations(**uptimerobot_json)
    service = integration_service_factory.get_service(None, integration)
    print(service.is_active())
    creds = service.generate_steampipe_creds()
    linux_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select email from uptimerobot_account;",
        "context": PayloadTaskContext(**context, **{"integration": integration}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**linux_task_dict)],
    }
    payload = Payload(**payload_dict)
    return payload


if __name__ == "__main__":
    uptimerobot_steampipe_payload = generate_uptimerobot_steampipe_payload()
    handle_payload(uptimerobot_steampipe_payload, print_output=True)
