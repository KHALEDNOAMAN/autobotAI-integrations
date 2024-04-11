from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations import ConnectionInterfaces
from autobotAI_integrations.integrations.kubernetes import KubernetesIntegration
from autobotAI_integrations.payload_schema import (
    Payload,
    PayloadTask,
    PayloadTaskContext
)
from autobotAI_integrations.integration_schema import IntegrationSchema
import os, uuid

agent_json = {
    "userId": "amit@shunyeka.com*",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
    "integrationState": "INACTIVE",
    "cspName": "kubernetes",
    "alias": "test-gcp-integrationsv2",
    "groups": ["gcp", "shunyeka", "integrations-v2"],
    "agent_ids": ["some_id1", "some_id2"],
    "accessToken": "",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": False,
    "lastUsed": None,
    "resource_type": "integration",
}

gcp_config_str = """
connection "kubernetes" {
  plugin         = "kubernetes"
  config_path    = "~/.kube/config"
}
"""

k8s_code = """
def executor(context):
    config = context['clients']['config']
    config.load_kube_config()
    
    kbs_client = context['clients']['client']
    
    v1 = kbs_client.CoreV1Api()
    namespace = "default"
    pod_list = v1.list_namespaced_pod(namespace)

    # Prepare the return list of pod information
    return_list = []
    for pod in pod_list.items:
        return_list.append({
            'id': pod.metadata.uid,
            'name': pod.metadata.name
        })

    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        print(i.status.pod_ip, i.metadata.namespace, i.metadata.name)

    result = [{"result": return_list}]
    return result
"""

context = {
    "execution_details": {
        "execution_id": "660275c610755f71b634e572",
        "bot_id": "660274d5fa724e7537a4c0c5",
        "bot_name": "K8s Worker",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "amit@shunyeka.com", "root_user_id": "amit@shunyeka.com"},
    },
    "node_steps": {},
}


def generate_k8s_steampipe_payload(agent_json=agent_json) -> Payload:
    k8s_integration = KubernetesIntegration(**agent_json)
    k8s_service = integration_service_factory.get_service(None, k8s_integration)
    creds = k8s_service.generate_steampipe_creds()
    creds.config = gcp_config_str
    aws_task_dict = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.STEAMPIPE,
        "executable": "select name, namespace, phase, creation_timestamp, pod_ip from kubernetes_pod",
        "context": PayloadTaskContext(**context, **{"integration": k8s_integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**aws_task_dict)]}
    payload = Payload(**payload_dict)
    return payload


def generate_k8s_python_payload(agent_json=agent_json):
    k8s_integration = KubernetesIntegration(**agent_json)
    k8s_service = integration_service_factory.get_service(None, k8s_integration)
    creds = k8s_service.generate_python_sdk_creds()
    
    # Add code executable for python
    k8s_python_task = {
        "task_id": uuid.uuid4().hex,
        "creds": creds,
        "connection_interface": ConnectionInterfaces.PYTHON_SDK,
        "executable": k8s_code,
        "clients": ["config", "client"],
        "params": {},
        "node_details": {"filter_resources": False},
        "context": PayloadTaskContext(**context, **{"integration": k8s_integration}),
        "resources": [],
    }
    payload_dict = {
        "job_id": uuid.uuid4().hex,
        "tasks": [PayloadTask(**k8s_python_task)],
    }
    payload = Payload(**payload_dict)
    return payload

if __name__ == '__main__':
    k8s_steampipe_payload = generate_k8s_steampipe_payload(agent_json)
    for task in k8s_steampipe_payload.tasks:
        integration = IntegrationSchema.model_validate(task.context.integration)
        service = integration_service_factory.get_service(None, integration)
        output = service.execute_steampipe_task(task, job_type="query")
        print(output)

    # k8s_python_payload = generate_k8s_python_payload(agent_json)
    # for task in k8s_python_payload.tasks:
    #     integration = IntegrationSchema.model_validate(task.context.integration)
    #     service = integration_service_factory.get_service(None, integration)
    #     output = service.python_sdk_processor(payload_task=task)
    #     print(output)



# Kubernetes deployment in local
# Define a deployment object
# try:
#     deployment = kbs_client.AppsV1Api().create_nam    espaced_deployment(
#     body = {
#             'apiVersion': 'apps/v1',
#             'kind': 'Deployment',
#             'metadata': {
#             'name': 'my-app',
#             },
#             'spec': {
#             'replicas': 3,
#             'selector': {
#                 'matchLabels': {
#                 'app': 'my-app'
#                 }
#             },
#             'template': {
#                 'metadata': {
#                 'labels': {
#                     'app': 'my-app'
#                 }
#                 },
#                 'spec': {
#                 'containers': [{
#                     'name': 'my-app',
#                     'image': 'nginx:latest'
#                 }]
#                 }
#             }
#             }
#         },
#         namespace='default'
#     )