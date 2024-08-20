import pytest, json

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

google_api_python_code = """
def executor(context):
    clients = context["clients"]
    print(clients)
    client = clients["docs_v1"]
    
    # The ID of a sample document.
    DOCUMENT_ID = "195j9eDD3ccgjQRttHhJPymLJUCOUjs-jmwTrekvdjFE"
    try:
        document = client.documents().get(documentId=DOCUMENT_ID).execute()

        return document  # Replace with your actual return logic
    except BaseException as err:
        return [{
            "error": str(err)
        }]
"""


class TestClassGoogle_api:
    # def test_google_api_steampipe_task(
    #     self,
    #     get_keys,
    #     sample_integration_dict,
    #     sample_steampipe_task,
    #     test_result_format,
    # ):
    #     with open(get_keys["GCP_TOKEN_PATH"]) as f:
    #         creds = json.load(fp=f)
    #     tokens = {"credentials": creds}
    #     integration = sample_integration_dict("google_api", tokens)
    #     google_api_query = "select * from google_api_my_repository"
    #     task = sample_steampipe_task(integration, query=google_api_query)
    #     result = handle_task(task)
    #     test_result_format(result)

    def test_google_api_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        with open(get_keys["GCP_TOKEN_PATH"]) as f:
            creds = json.load(fp=f)
        tokens = {"credentials": creds}
        integration = sample_integration_dict("google_api", tokens)
        task = sample_python_task(
            integration, code=google_api_python_code, clients=["docs_v1"]
        )
        result = handle_task(task)
        print(result.model_dump_json(indent=2))
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        with open(get_keys["GCP_TOKEN_PATH"]) as f:
            creds = json.load(fp=f)
        tokens = {"credentials": creds}
        integration = sample_integration_dict("google_api", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        with open(get_keys["GCP_TOKEN_PATH"]) as f:
            creds = json.load(fp=f)
        
        for k, v in creds.items():
            creds[k] = "invalid"
        tokens = {"credentials": creds}
        integration = sample_integration_dict("google_api", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
