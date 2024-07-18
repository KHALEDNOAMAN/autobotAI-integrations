import pytest

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.payload_schema import Param

imap_python_code = """
# Import your modules here
import email, html

# **Security Note:** Client-related modules should not be directly imported here.
# Instead, they are passed as arguments and retrieved from a secure configuration.

def executor(context):
    params = context["params"]
    clients = context["clients"]

    # Placeholder for retrieving the integration-specific client if needed
    client = clients["imap_ssl_connection"]  # Supports only one client

    # User's Python code execution logic goes here
    # (Replace this comment with the your actual code)

    # Example: Code to list last 10 emails data (for illustration purposes only)
    client.select("Inbox")
    res = []
    try:
        tmp, data = client.search(None, "ALL")
        # Fetching last 10 emails
        count = 10
        for num in data[0].split()[::-1]:
            tmp, data = client.fetch(num, "(RFC822)")
            raw_email = data[0][1]
            res.append(raw_email)
            count -= 1
            if count == 0:
                break
        client.close()
        client.logout()
        return res
    except BaseException as e:
        return [{"result": str(e)}]
"""

smtp_code = """
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def executor(context):
    params = context["params"]
    clients = context["clients"]
    try:
        client = clients["smtp_client"]
        # Example: Code to Send email (for illustration purposes only)
        message = MIMEMultipart("alternative")
        message["Subject"] = "Automated generated Email"
        message["From"] = params.get("sender")
        message["To"] = params.get("receiver")

        # Create the plain-text and HTML version of your message
        html = \"\"\"<html>
        <body>
            <p>Hi,<br>
            How are you?<br>
            <a href="http://www.realpython.com">Real Python</a> 
            has many great tutorials.
            </p>
        </body>
        </html>\"\"\"

        message.attach(MIMEText(html, "html"))
        client.sendmail(params.get("sender"), params.get("receiver"), message.as_string())
        # terminating the session
        client.quit()
        return {
            "success": True,
            "message": "Email sent successfully"
        }
    except BaseException as e:
        return {
            "success": False,
            "message": str(e)
        }
"""

class TestClassIMAP:
    def test_email_steampipe_task(
        self,
        get_keys,
        sample_integration_dict,
        sample_steampipe_task,
        test_result_format,
    ):
        tokens = {
            "host": get_keys["IMAP_HOST"],
            "username": get_keys["IMAP_USERNAME"],
            "password": get_keys["IMAP_PASSWORD"]
        }
        integration = sample_integration_dict("email", tokens)
        imap_query = "select * from imap_message where mailbox='INBOX' and  timestamp > current_timestamp - interval '2 days'"
        task = sample_steampipe_task(integration, query=imap_query)
        result = handle_task(task)
        print(result.model_dump_json(indent=2))
        test_result_format(result)

    def test_email_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "host": get_keys["IMAP_HOST"],
            "username": get_keys["IMAP_USERNAME"],
            "password": get_keys["IMAP_PASSWORD"],
        }
        integration = sample_integration_dict("email", tokens)
        task = sample_python_task(
            integration, code=imap_python_code, clients=["imap_ssl_connection"]
        )
        result = handle_task(task)
        print(result.model_dump_json(indent=2))
        test_result_format(result)

    def test_integration_active(self, get_keys, sample_integration_dict):
        tokens = {
            "host": get_keys["IMAP_HOST"],
            "username": get_keys["IMAP_USERNAME"],
            "password": get_keys["IMAP_PASSWORD"],
        }
        integration = sample_integration_dict("email", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]
        tokens = {
            "host": get_keys["IMAP_HOST"],
            "username": get_keys["IMAP_USERNAME"],
            "password": get_keys["IMAP_PASSWORD"][:-2],
        }
        integration = sample_integration_dict("email", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]

    def test_email_smtp_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {
            "host": get_keys["IMAP_HOST"],
            "username": get_keys["IMAP_USERNAME"],
            "password": get_keys["IMAP_PASSWORD"],
            "smtp_host": get_keys["SMTP_HOST"]
        }
        param1 = Param(type="string", name="sender", values=get_keys["SENDER"])
        param2 = Param(type="string", name="receiver", values=get_keys["RECEIVER"])
        integration = sample_integration_dict("email", tokens)
        task = sample_python_task(
            integration, code=smtp_code, clients=["smtp_client"], params=[param1, param2]
        )
        result = handle_task(task)
        print(result.model_dump_json(indent=2))
        test_result_format(result)
