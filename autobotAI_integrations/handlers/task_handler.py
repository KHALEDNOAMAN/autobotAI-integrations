import os
from autobotAI_integrations import IntegrationSchema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.models import ConnectionInterfaces
from autobotAI_integrations.payload_schema import TaskResult, PayloadTask, ResponseDebugInfo, ResponseError
import json

def handle_task(task: PayloadTask) -> TaskResult:
    if not isinstance(task, PayloadTask):
        raise Exception("Task must be of type PayloadTask")

    integration = IntegrationSchema.model_validate(task.context.integration)
    service = integration_service_factory.get_service(None, integration)

    result_json = {
        "task_id": task.task_id,
        "integration_id": task.context.integration.accountId,
        "integration_type": task.context.integration.cspName,
        "resources": None,
        "errors": None,
        "debug_info": ResponseDebugInfo(**{
            "executable": task.executable,
            "job_type": "job_type_here",
            "resource_type": "",
            "environs": {**os.environ},
        }),
    }

    if task.connection_interface == ConnectionInterfaces.PYTHON_SDK:
        output = service.python_sdk_processor(task)
    elif task.connection_interface == ConnectionInterfaces.STEAMPIPE:
        output = service.execute_steampipe_task(task)
    else:
        raise Exception("Invalid task.connection_interface = {}".format(task.connection_interface))
    
    result = TaskResult(**result_json)
    try:
        formated_result = json.dumps(output[0])
    except TypeError as e:
        formated_result = json.dumps(output[0], default=str)
        result.resources = formated_result
    else:
        result.resources = formated_result

    result.errors = [ ResponseError(**error) for error in output[1] ]
    
    return result

