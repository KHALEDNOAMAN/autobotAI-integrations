from aws_payload import generate_aws_python_payload, generate_aws_steampipe_payload
from gitlab_payload import generate_gitlab_python_payload, generate_gitlab_steampipe_payload
from payload_handler import handle
from autobotAI_integrations.payload_schema import Payload
import uuid

aws_tokens = [
    # First account credentials
    {
        "AWS_ACCESS_KEY_ID":"",
        "AWS_SECRET_ACCESS_KEY":"",
        "AWS_SESSION_TOKEN":""
    },
    # Second account credentials
    {
        "AWS_ACCESS_KEY_ID": "",
        "AWS_SECRET_ACCESS_KEY": "",
        "AWS_SESSION_TOKEN": ""
    }
]

def get_aws_payload_token():
    for i in range(2):
        aws_json = {
            "userId": "amit@shunyeka.com*",
            "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
            "integrationState": "INACTIVE",
            "cspName": "aws",
            # don't commit your keys
            "access_key": aws_tokens[i]["AWS_ACCESS_KEY_ID"],
            "secret_key": aws_tokens[i]["AWS_SECRET_ACCESS_KEY"],
            "session_token": aws_tokens[i]["AWS_SESSION_TOKEN"],
            "alias": "test-aws-integrationsv2",
            "connection_type": "DIRECT",
            "groups": ["aws", "shunyeka", "integrations-v2"],
            "agent_ids": [],
            "accessToken": "",
            "createdAt": "2024-02-26T13:38:59.978056",
            "updatedAt": "2024-02-26T13:38:59.978056",
            "indexFailures": 0,
            "isUnauthorized": False,
            "lastUsed": None,
            "resource_type": "integration",
            "activeRegions": ["us-east-1", "ap-south-1"],
        }
        yield aws_json


def get_two_tasks_with_different_credentials():
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": []}
    
    # Setting AWS Tasks
    for token in get_aws_payload_token():
        payload1 = generate_aws_python_payload(token)
        payload2 = generate_aws_steampipe_payload(token)
        payload_dict['tasks'].append(payload1.tasks[0])
        payload_dict["tasks"].append(payload2.tasks[0])
    
    # Setting UP Gitlab Tasks
    gitlab_payload1 = generate_gitlab_python_payload()
    gitlab_payload2 = generate_gitlab_steampipe_payload()
    payload_dict['tasks'].append(gitlab_payload1.tasks[0])
    payload_dict["tasks"].append(gitlab_payload2.tasks[0])

    payload = Payload(**payload_dict)
    return payload

final_payload = get_two_tasks_with_different_credentials()

handle(final_payload)