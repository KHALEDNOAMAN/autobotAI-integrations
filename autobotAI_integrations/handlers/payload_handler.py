from autobotAI_integrations.payload_schema import Payload, JobResult, PayloadTaskContext
from .task_handler import handle_task
import requests
from io import BytesIO
from autobotAI_integrations.utils.logging_config import logger, set_unset_log_ids


def handle_payload(
    payload: Payload, return_results: bool = False, print_output: bool = False
):
    if isinstance(payload, dict):
        payload = Payload(**payload)
    if (getattr(payload, "extra_details") or {}).get("exc_id"):
        set_unset_log_ids(logger, "Preserve", (getattr(payload, "extra_details") or {}).get("exc_id"))
    logger.info(f"Started handle_payload with Payload Id: {payload.job_id}")

    if not isinstance(payload, Payload):
        raise Exception("Payload must be of type Payload or dict")

    results = JobResult(job_id=payload.job_id, task_results=[])

    for task in payload.tasks:
        logger.debug("Running Task: {}".format(task.task_id))
        if payload.common_params:
            task.params = task.params or []
            task.params.extend(payload.common_params)
        if payload.common_context:
            task_context_dict = task.context.model_dump()
            common_context_dict = payload.common_context.model_dump()
            task_context_dict.update(common_context_dict)
            task.context = PayloadTaskContext(**task_context_dict)
        results.task_results.append(handle_task(task))
        del task.params
        del task.context

    logger.info("All tasks completed!")

    if payload.output_url is not None:
        result_file = BytesIO()
        result_file.write(bytes(results.model_dump_json(), encoding="utf-8"))
        result_file.seek(0)
        files = {'file': result_file}
        response = requests.post(
            payload.output_url["url"],
            data=payload.output_url['fields'],
            files=files
        )
        

        if response.status_code == 204:
            logger.info("File uploaded successfully!")
        else:
            logger.error(f"Error uploading file: {response.status_code}")

    if print_output:
        logger.info(results.model_dump_json(indent=2))

    if return_results:
        return {
            "success": True,
            "results": results.model_dump()
        }

    return {"success": True}
