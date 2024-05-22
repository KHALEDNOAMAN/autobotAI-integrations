from autobotAI_integrations.payload_schema import Payload, JobResult
from .task_handler import handle_task
import requests
import tempfile


def handle_payload(
    payload: Payload, return_results: bool = False, print_output: bool = False
):
    if isinstance(payload, dict):
        payload = Payload(**payload)

    if not isinstance(payload, Payload):
        raise Exception("Payload must be of type Payload or dict")

    resutls = JobResult(job_id=payload.job_id, task_results=[])

    for task in payload.tasks:
        resutls.task_results.append(handle_task(task))

    if payload.output_url is not None:
        result_file = tempfile.NamedTemporaryFile()
        result_file.write(bytes(resutls.model_dump_json(), encoding="utf-8"))
        result_file.seek(0)
        files = {'file': result_file}
        response = requests.post(
            payload.output_url["url"],
            data=payload.output_url['fields'],
            files=files
        )
        result_file.close()

        if response.status_code == 204:
            print("File uploaded successfully!")
        else:
            print(f"Error uploading file: {response.status_code}")

    if print_output:
        print(resutls.model_dump_json(indent=2))

    if return_results:
        return {
            "success": True,
            "results": resutls.model_dump()
        }

    return {"success": True}
