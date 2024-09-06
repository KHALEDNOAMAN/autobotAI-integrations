import os
from autobotAI_integrations import IntegrationSchema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.models import ConnectionInterfaces
from autobotAI_integrations.payload_schema import TaskResult, PayloadTask, ResponseDebugInfo, ResponseError
from autobotAI_integrations.utils.logging_config import logger
import json


def handle_task(task: PayloadTask) -> TaskResult:
    logger.info("Started handle_task with Task Id: {}".format(task.task_id))
    if not isinstance(task, PayloadTask):
        logger.error("Task must be of type PayloadTask")

    logger.debug("Task: {}".format(task))
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

    logger.info(f"Checking For Connection Interface: {task.connection_interface}")

    if task.connection_interface == ConnectionInterfaces.PYTHON_SDK:
        output = service.python_sdk_processor(task)
    elif task.connection_interface == ConnectionInterfaces.STEAMPIPE:
        output = service.execute_steampipe_task(task)
    elif task.connection_interface == ConnectionInterfaces.REST_API:
        output = service.execute_rest_api_task(task)
    else:
        raise Exception("Invalid task.connection_interface = {}".format(task.connection_interface))

    logger.info(f"Task Completed With Id: {task.task_id}")
    logger.debug(f"Task Completed With Output: {output}")
    result = TaskResult(**result_json)
    try:
        formatted_result = json.dumps(output[0])
        formatted_result = json.loads(formatted_result)
    except TypeError as e:
        formatted_result = json.dumps(output[0], default=str)
        formatted_result = json.loads(formatted_result)
        result.resources = formatted_result
    else:
        result.resources = formatted_result

    result.errors = [ResponseError(**error) for error in output[1]]
    if result.errors:
        logger.error("Task Errors: {}".format(result.errors))

    return result
