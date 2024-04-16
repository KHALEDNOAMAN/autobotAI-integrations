import subprocess
import os
import json
from tempfile import TemporaryDirectory

from autobotAI_integrations.payload_schema import Payload
from task_executor import TaskExecutor
# run_env = os.environ.get('RUN_ENV', app_env)
# run_env = os.environ.get('RUN_ENV', "non-local")
# If run_env = app_env
# run it here
# else do not execute defined source

dir_prrefix = "TempTaskDir"
temp_dir_path = os.getcwd()  # Set None if you want to use default temp dir


def handle(payload: Payload):
    tmpdir = TemporaryDirectory(prefix=dir_prrefix, dir=temp_dir_path)
    executor = TaskExecutor(dir_path=tmpdir.name)

    for task in payload.tasks:
        task_input_file = os.path.join(tmpdir.name, "{}.json".format(task.task_id))
        task_ouput_file = os.path.join(
            tmpdir.name, "{}-output.json".format(task.task_id)
        )

        with open(task_input_file, "w") as task_file:
            task_file.write(task.model_dump_json())

        executor.run(task.task_id)

        with open(task_ouput_file) as ouput_file:
            print(json.loads(ouput_file.read()))

    tmpdir.cleanup()
