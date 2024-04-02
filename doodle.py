# import boto3
#
# aws_clients = [
#     {
#         "package": "boto3",
#         "name": "s3",
#         "is_regional": False,
#         "import": "boto3"
#     }
# ]
#
#
# def aws_client_generator(required_clients, regions):
#     clients = []
#     for client in required_clients:
#         if client.get("is_regional"):
#             clients.append(boto3.client(client["name"]))
#         else:
#             clients.append(boto3.client(client["name"], region_name="us-east-1"))
#
#
# azure_clients = [
#     {
#         "pkg": "azure-mgmt-network",
#         "module": "azure.mgmt.network",
#         "class": "NetworkManagementClient",
#         "name": "NetworkManagementClient",
#         "integration_type": "azure"
#     }
# ]
import traceback
from http.client import HTTPException
from autobotAI_integrations.integrations import integration_service_factory

# generate_aws_payload()


# def integration_details():
#     return integration_service_factory.get_service_details()
# import json
# print(json.dumps(integration_details()))


# def get_steampipe_meta():
#     integration_service = integration_service_factory.get_service_cls("gitlab")
#     resource_types = []
#     for rtype in integration_service.get_steampipe_tables():
#         resource_types.append({"name": rtype["name"], "is_regional": False})
#     return resource_types
#
# print(get_steampipe_meta())


def create_integration(json_data, integration_type):
    service_cls = integration_service_factory.get_service_cls(integration_type)
    schema = service_cls.get_schema()

    return schema(**json_data)


# print(create_integration(
#     {
#         "userId": "amit@shunyeka.com*",
#         "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
#         "integrationState": "INACTIVE*",
#         "cspName": "gitlab*",
#         "alias": "test-gitlab-integrationsv2*",
#         "connection_type": "DIRECT*",
#         "token": "xyz",
#         "base_url": "xyz",
#         "groups": [*
#             "gitlab",
#             "shunyeka",
#             "integrations-v2"
#         ],
#         "agent_ids": [],
#         "accessToken": "",
#         "createdAt": "2024-02-26T13:38:59.978056*",
#         "updatedAt": "2024-02-26T13:38:59.978056*",
#         "indexFailures": 0,
#         "isUnauthorized": False,
#         "lastUsed": None,
#         "resource_type": "integration*",
#         "activeRegions": None
#     }, "gitlab"))

gitlab_json = {
    "userId": "amit@shunyeka.com*",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "gitlab*",
    "alias": "test-gitlab-integrationsv2*",
    "connection_type": "DIRECT",
    "token": "xyz",
    "base_url": "xyz",
    "groups": ["gitlab", "shunyeka", "integrations-v2"],
    "agent_ids": [],
    "accessToken": "",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": False,
    "lastUsed": None,
    "resource_type": "integration",
    "activeRegions": [],
}

aws_json = {
    "userId": "amit@shunyeka.com*",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "aws",
    "acccess_key": "ahudfuusdfj",
    "secret_key": "ahudfuusdfj",
    "session_token": "abkfhlksf",
    "session_token": "abc",
    "alias": "test-gitlab-integrationsv2*",
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
    "activeRegions": [],
}

aws_json__with_arn = {
    "userId": "amit@shunyeka.com*",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc*",
    "integrationState": "INACTIVE",
    "cspName": "aws",
    "role_arn": "absolute",
    "session_token": "abkfhlksf",
    "alias": "test-gitlab-integrationsv2*",
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
    "activeRegions": [],
}

def printSchema(schma):
    for k, v in schma:
        print("{}: {}".format(k, v))
    print("--"*20)
        
printSchema(create_integration(gitlab_json, "gitlab"))

printSchema(create_integration(aws_json, "aws"))

printSchema(create_integration(aws_json__with_arn, "aws"))

