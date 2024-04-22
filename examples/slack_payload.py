import os
import uuid
import dotenv

dotenv.load_dotenv()

from autobotAI_integrations import ConnectionInterfaces, IntegrationSchema
from autobotAI_integrations.integrations.slack import SlackIntegration
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Payload, PayloadTask, PayloadTaskContext
from autobotAI_integrations.handlers import handle_payload

code = """
import traceback

def executor(context):
    print("in execute")
    webclient = context["clients"]['WebClient']    
    try:
        response = webclient.chat_postMessage(channel='#random', text="How can i help you?")
        assert response["message"]["text"] == "Hello world!"
    except SlackApiError as e:
        print(f"Got an error: {e.response['error']}")
        return {
            "success": False
        }
    else:
        return str({
            "success": True
        })
"""

slack_config_str = """
connection "slack" {
  plugin = "slack"

  # The Slack app token used to connect to the API.
  # Can also be set with the SLACK_TOKEN environment variable.
  #token = "xoxp-YOUR_TOKEN_HERE"
}
"""
slack_json = {
    "userId": "ritin.tiwari001@gmail.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "slack",
    "alias": "test-slack-integrationsv2*",
    "connection_type": "DIRECT",
    "bot_token": os.environ["SLACK_BOT_TOKEN"],
    "workspace": "MyWorkSpace",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": False,
    "lastUsed": None,
    "resource_type": "integration",
}

context = {
    "execution_details": {
        "execution_id": "660275c610755f71b634e572",
        "bot_id": "660274d5fa724e7537a4c0c5",
        "bot_name": "AWS Integrations-V2 Test",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "amit@shunyeka.com", "root_user_id": "amit@shunyeka.com"},
    },
    "node_steps": {},
    "global_variables": {},
}

def generate_slack_python_payload(slack_json=slack_json) -> Payload:
    integration = SlackIntegration(**slack_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_python_sdk_creds()
    task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": code,
        "clients": ["WebClient"],
        "context": PayloadTaskContext(**context, **{"integration": slack_json}),
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**task_dict)]
    }
    payload = Payload(**payload_dict)
    return payload

def generate_slack_steampipe_payload(slack_json=slack_json):
    integration = SlackIntegration(**slack_json)
    service = integration_service_factory.get_service(None, integration)
    creds = service.generate_steampipe_creds()
    creds.config = slack_config_str
    slack_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select name, num_members from slack_conversation",
        "context": PayloadTaskContext(**context, **{"integration": integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**slack_task_dict)]}
    payload = Payload(**payload_dict)
    return payload

if __name__ == "__main__":
    slack_python_payload = generate_slack_python_payload()
    handle_payload(slack_python_payload, print_output=True)

    # slack_steampipe_payload = generate_slack_steampipe_payload()
    # handle_payload(slack_steampipe_payload, print_output=True)
