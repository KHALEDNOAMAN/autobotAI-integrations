import pytest, json

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory

google_api_python_code = """
def executor(context):
    clients = context["clients"]
    
    # The ID of a sample document.
    client = clients["drive_v3"]

    # The ID of a sample document.
    results = client.files().list().execute()
    return results
"""


class TestClassGoogle_api:
    def test_google_api_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        with open(get_keys["GCP_TOKEN_PATH"]) as f:
            creds = json.load(fp=f)

        tokens = {
            "scopes": """https://www.googleapis.com/auth/calendar.readonly, https://www.googleapis.com/auth/contacts.readonly,
https://www.googleapis.com/auth/contacts.other.readonly,
https://www.googleapis.com/auth/directory.readonly,
https://www.googleapis.com/auth/drive.readonly,
https://www.googleapis.com/auth/gmail.readonly""",
            "user_email": "ritin.tiwari@shunyeka.com",
            "credentials": creds,
        }
        integration = sample_integration_dict("google_api", tokens)
        google_api_query = "select name, id from googleworkspace_drive_my_file"
        task = sample_steampipe_task(integration, query=google_api_query)
        result = handle_task(task)
        test_result_format(result)

    def test_google_api_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        with open(get_keys["GCP_TOKEN_PATH"]) as f:
            creds = json.load(fp=f)
        tokens = {
            "scopes": [
                "https://www.googleapis.com/auth/contacts.other.readonly",
                "https://www.googleapis.com/auth/directory.readonly",
                "https://www.googleapis.com/auth/drive.readonly",
                "https://www.googleapis.com/auth/gmail.readonly"
            ],
            "user_email": get_keys["GCP_EMAIL"],
            "credentials": creds,
        }
        integration = sample_integration_dict("google_api", tokens)
        task = sample_python_task(
            integration, code=google_api_python_code, clients=["drive_v3"]
        )
        result = handle_task(task)
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        with open(get_keys["GCP_TOKEN_PATH"]) as f:
            creds = json.load(fp=f)
        tokens = {
            "scopes": """https://www.googleapis.com/auth/calendar.readonly, https://www.googleapis.com/auth/contacts.readonly,
https://www.googleapis.com/auth/contacts.other.readonly,
https://www.googleapis.com/auth/directory.readonly,
https://www.googleapis.com/auth/drive.readonly,
https://www.googleapis.com/auth/gmail.readonly""",
            "user_email": get_keys["GCP_EMAIL"],
            "credentials": creds,
        }
        integration = sample_integration_dict("google_api", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        with open(get_keys["GCP_TOKEN_PATH"]) as f:
            creds = json.load(fp=f)

        for k, v in creds.items():
            creds[k] = "invalid"
        tokens = {
            "scopes": """https://www.googleapis.com/auth/calendar.readonly, https://www.googleapis.com/auth/contacts.readonly,
https://www.googleapis.com/auth/contacts.other.readonly,
https://www.googleapis.com/auth/directory.readonly,
https://www.googleapis.com/auth/drive.readonly,
https://www.googleapis.com/auth/gmail.readonly""",
            "user_email": get_keys["GCP_EMAIL"],
            "credentials": creds,
        }
        integration = sample_integration_dict("google_api", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
