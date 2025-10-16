from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
import traceback

python_code = """
# Import your modules here

def executor(context):
    clients = context["clients"]
    client = clients["perplexity"]  # Supports only one client

    # User's Python code execution logic goes here
    # (Replace this comment with the your actual code)

    # Example: Using chat completion model(for illustration purposes only)
    completion = client.chat.completions.create(
        model="sonar-pro",
        messages=[
            {"role": "user", "content": "What were the results of the 2025 French Open Finals?"}
        ]
    )

    # print(completion.choices[0].message)
    return [
        {
            "result": completion.choices[0].message.content
        }
    ]
"""

class TestClassPerplexity:
    def test_perplexity_token(
        self,
        get_keys,
        sample_integration_dict,
        test_result_format,
    ):
        tokens = {"api_key": get_keys.get("PERPLEXITY_API_KEY", "test_key")}
        integration = sample_integration_dict("perplexity", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        # Note: This will likely fail without a real API key
        assert res["success"]

        tokens = {"api_key": "invalid_key"}
        integration = sample_integration_dict("perplexity", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("perplexity")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
            print(action.model_dump_json(indent=2))
        assert len(actions) > 0

    # "Create a chat completion"
    def test_actions_run(
        self, get_keys, sample_restapi_task, test_result_format, sample_integration_dict
    ):
        tokens = {"api_key": get_keys.get("PERPLEXITY_API_KEY", "test_key")}
        integration = sample_integration_dict("perplexity", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            try:
                if action.name.lower() != "Create a chat completion".lower():
                    print(action.name)
                    continue
                # In most Cases this will fail as parameters_definition does not contains actual values
                params = action.parameters_definition
                for param in params:
                    if param.name == "body":
                        param.values = {
                            "model": "sonar",
                            "messages": [
                                {
                                    "role": "user",
                                    "content": "What are the major AI developments and announcements from today across the tech industry?",
                                }
                            ],
                        }
                action.parameters_definition = params
                task = sample_restapi_task(
                    integration, action.code, action.parameters_definition
                )
                result = handle_task(task)
                print(result.model_dump_json(indent=2))
                test_result_format(result)
                assert False
            except Exception as e:
                traceback.print_exc()
                assert False
    
    def test_perplexity_python_task(
        self, get_keys, sample_integration_dict, sample_python_task, test_result_format
    ):
        tokens = {"api_key": get_keys.get("PERPLEXITY_API_KEY", "test_key")}
        integration = sample_integration_dict("perplexity", tokens)
        task = sample_python_task(integration, code=python_code, clients=["perplexity"])
        result = handle_task(task)
        test_result_format(result)
        print(result.model_dump_json(indent=2))
        assert False