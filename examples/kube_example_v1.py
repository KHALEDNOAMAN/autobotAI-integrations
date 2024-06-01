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
import traceback
from autobotAI_integrations.payload_schema import TaskResult, PayloadTask, ResponseDebugInfo, ResponseError, JobResult
from autobotAI_integrations import utils

agent_json = {
    "userId": "user@email.com*",
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
    kbs_client = context['clients']['kubernetes']
    
    v1 = kbs_client.CoreV1Api()
    namespace = "default"
    # pod_list = v1.list_namespaced_pod(namespace)
    pod_list = v1.list_pod_for_all_namespaces(watch=False)
    # Prepare the return list of pod information
    return_list = []
    for pod in pod_list.items:
        return_list.append({
            'id': pod.metadata.uid,
            'name': pod.metadata.name,
            'namespace': pod.metadata.namespace,
            'creation_timestamp': pod.metadata.creation_timestamp,
            'pod_ip': pod.status.pod_ip,
            'phase': pod.status.phase
        })

    result = [{"result": return_list}]
    return result
"""

context = {
    "execution_details": {
        "execution_id": "660275c610755f71b634e572",
        "bot_id": "660274d5fa724e7537a4c0c5",
        "bot_name": "K8s Worker",
        "node_name": "Python-Code-Executor",
        "caller": {"user_id": "user@email.com", "root_user_id": "user@email.com"},
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
        # "executable": "kubernetes_compliance.benchmark.cis_v170",
        "executable": "select name, namespace, phase, creation_timestamp, pod_ip from kubernetes_pod",
        "context": PayloadTaskContext(**context, **{"integration": k8s_integration}),
    }
    payload_dict = {"job_id": uuid.uuid4().hex, "tasks": [PayloadTask(**aws_task_dict)]}
    payload = Payload(**payload_dict)
    # print(payload.model_dump_json(indent=2))
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
        "clients": ["kubernetes"],
        "params": [],
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

def create_inventory(task, service):
    integration_type = task.creds.connection_name
    integration_id = task.context.integration.accountId
    query = task.executable
    
    final_data = {
        "debug_info": {
            "executable": task.executable, 
            "job_type": "compliance", 
            "integration_type": task.creds.connection_name,
            "integration_id": task.context.integration.accountId, 
            "resource_type": task.context.integration.resource_type,
            "environs": None
            }, 
            "resources": [], 
            "errors": []}
    try:
        result = service.execute_steampipe_task(task)
        print("result :", result)
        if result.get("rows"):
            final_data["resources"] = result.get("rows")
        else:
            final_data.update(
                    {"resources": [], "errors": [ResponseError(message=result["output"]["message"], other_details={
                        "full_output": result["output"]
                    })]})
        return final_data
    except:
        trace = traceback.format_exc()
        final_data["errors"].append(ResponseError(message=trace))
    
    return final_data


if __name__ == '__main__':
    k8s_steampipe_payload = generate_k8s_steampipe_payload(agent_json)
    job_id = k8s_steampipe_payload.job_id
    for task in k8s_steampipe_payload.tasks:
        integration = IntegrationSchema.model_validate(task.context.integration)
        service = integration_service_factory.get_service(None, integration)

        if task.executable.startswith(f"{task.creds.plugin_name}_compliance"):
            task_results = []
            integration_type = task.creds.connection_name
            integration_id = task.context.integration.accountId
            query = task.executable
            debug_info = ResponseDebugInfo(executable=query, job_type="compliance", integration_type=integration_type,
                                                       integration_id=integration_id,
                                                       resource_type=task.context.integration.resource_type)
            final_data = create_inventory(task, service)
            pre_data = utils.transform_steampipe_compliance_resources(final_data)
            resources, errors = utils.oscf_based_steampipe_json(pre_data,
                integration_type=task.creds.connection_name,
                integration_id=task.context.integration.accountId,
                query=task.executable)
            
            task_result = TaskResult(
                task_id=task.task_id,
                integration_id=integration_id,
                integration_type=integration_type,
                resources=resources,
                errors=errors,
                debug_info=debug_info
            )
            task_results.append(task_result)
            job_result = JobResult(job_id=job_id, task_results=task_results).json()

            print("Compliance Results :", job_result)
        else:    
            result = create_inventory(task, service)
            final_data = utils.transform_inventory_resources(result, agent_id="83ur583823083354r")
        
    # k8s_python_payload = generate_k8s_python_payload(agent_json)
    # for task in k8s_python_payload.tasks:
    #     integration = IntegrationSchema.model_validate(task.context.integration)
    #     service = integration_service_factory.get_service(None, integration)
    #     output = service.python_sdk_processor(payload_task=task)
    #     print(output)
