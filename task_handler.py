# read the argument task_id
import json
import argparse
import os

from autobotAI_integrations import IntegrationSchema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.models import ConnectionInterfaces
from autobotAI_integrations.payload_schema import PayloadTask

parser = argparse.ArgumentParser(description="Task Executer File For Given Task Id")
parser.add_argument(
    "--task_id", "-tid", required=True, help="Provide unique taskId as an argument"
)
parser.add_argument(
    "--io_dir", "-io_d", required=True, help="Provide task input file path"
)

args = parser.parse_args()

task_id = str(args.task_id)
temp_dir_path = str(args.io_dir)

task_input_file = os.path.join(temp_dir_path, "{}.json".format(task_id))
task_ouput_file = os.path.join(temp_dir_path, "{}-output.json".format(task_id))

with open(task_input_file) as task_file:

    task = PayloadTask.model_validate_json(task_file.read(), strict=False)

    integration = IntegrationSchema.model_validate(task.context.integration)
    service = integration_service_factory.get_service(None, integration)

    result = None
    if task.connection_interface == ConnectionInterfaces.PYTHON_SDK:
        result = service.python_sdk_processor(task)
    elif task.connection_interface == ConnectionInterfaces.STEAMPIPE:
        result = service.execute_steampipe_task(task)
    else:
        print("Method is not implemented yet.")

    with open(task_ouput_file, "w") as output:
        output.write(json.dumps(result, default=str))
