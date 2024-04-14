import os
import json

from autobotAI_integrations import IntegrationSchema
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.models import ConnectionInterfaces
from autobotAI_integrations.payload_schema import TaskResult, PayloadTask

class TaskExecutor:
    def __init__(self, dir_path=os.getcwd()) -> None:
        self.task_results = dict()
        self.input_dir = dir_path
    
    def get_task_result_by_id(self, task_id):
        if self.task_results.get(task_id, None):
            return self.task_results[task_id]
        raise KeyError("TaskID {} Not Found!".format(task_id))
    
    def get_all_results(self):
        return self.task_results
    
    def get_task(self, task_id):
        with open(os.path.join(self.input_dir, f"{task_id}.json"), 'r') as task_file:
            task = PayloadTask.model_validate_json(task_file.read(), strict=False)
            return task

    def dump_result(self, task_id):
        task_output_file = os.path.join(self.input_dir, f"{task_id}-output.json")
        with open(task_output_file, "w") as task_file:
            task_result = self.get_task_result_by_id(task_id=task_id)
            task_file.write(json.dumps(task_result, default=str))
        
    def run(self, task_id):
        task = self.get_task(task_id)
        integration = IntegrationSchema.model_validate(task.context.integration)
        service = integration_service_factory.get_service(None, integration)
        result = None
        if task.connection_interface == ConnectionInterfaces.PYTHON_SDK:
            result = service.python_sdk_processor(task)
        elif task.connection_interface == ConnectionInterfaces.STEAMPIPE:
            result = service.execute_steampipe_task(task)
        else:
            print("Method is not implemented yet.")
        self.task_results[task_id] = result
        self.dump_result(task_id)
