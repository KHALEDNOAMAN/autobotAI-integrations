import traceback

from autobotAI_integrations.handlers.task_handler import handle_task
from autobotAI_integrations.integrations import integration_service_factory
from autobotAI_integrations.integrations.openrouter import (
    OPENROUTER_BASE_URL,
    OpenRouterIntegration,
    OpenRouterService,
)
from autobotAI_integrations.models import ConnectionInterfaces


class TestClassOpenRouter:
    def test_factory_registration(self):
        cls = integration_service_factory.get_service_cls("openrouter")
        assert cls is OpenRouterService
        assert "openrouter" in integration_service_factory.get_ai_services()

    def test_schema_and_forms(self, sample_integration_dict):
        integration_dict = sample_integration_dict("openrouter", {"api_key": "sk-or-test"})
        integration = OpenRouterIntegration(**integration_dict)
        assert integration.api_key == "sk-or-test"
        assert integration.name == "OpenRouter"

        form = OpenRouterService.get_forms()
        assert form["label"] == "OpenRouter"
        api_key_field = next(c for c in form["children"] if c["name"] == "api_key")
        assert api_key_field["required"] is True
        assert api_key_field["type"] == "text/password"

    def test_supported_interfaces(self):
        interfaces = OpenRouterService.supported_connection_interfaces()
        assert ConnectionInterfaces.REST_API in interfaces
        assert ConnectionInterfaces.PYTHON_SDK in interfaces

    def test_rest_api_creds(self, sample_integration_dict):
        integration = sample_integration_dict("openrouter", {"api_key": "sk-or-test"})
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_rest_api_creds()
        assert creds.base_url == OPENROUTER_BASE_URL
        assert creds.headers.get("Authorization") == "Bearer sk-or-test"

    def test_python_sdk_creds(self, sample_integration_dict):
        integration = sample_integration_dict("openrouter", {"api_key": "sk-or-test"})
        service = integration_service_factory.get_service(None, integration)
        creds = service.generate_python_sdk_creds()
        assert creds.envs["OPENROUTER_API_KEY"] == "sk-or-test"
        assert creds.envs["OPENROUTER_BASE_URL"] == OPENROUTER_BASE_URL

    def test_integration_specific_details(self, sample_integration_dict):
        integration = sample_integration_dict("openrouter", {"api_key": "sk-or-test"})
        service = integration_service_factory.get_service(None, integration)
        details = service.get_integration_specific_details()
        assert "models" in details
        assert isinstance(details["models"], list)
        assert len(details["models"]) > 0
        # Multi-provider routing — names should be namespaced.
        assert any("/" in m for m in details["models"])

    def test_ai_prompt_python_template(self):
        template = OpenRouterService.ai_prompt_python_template()
        assert template["integration_type"] == "openrouter"
        assert template["ai_client"] == "openai"
        param_names = {p["name"] for p in template["param_definitions"]}
        assert {"prompt", "model", "resources"} <= param_names
        assert "def executor" in template["code"]

    def test_actions_generation(self):
        actions = OpenRouterService.get_all_rest_api_actions()
        assert len(actions) > 0
        names = set()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
            names.add(action.name)
        # Spot-check a few endpoints from open_api.json.
        assert any("chat" in n.lower() for n in names)

    def test_openrouter_token(self, get_keys, sample_integration_dict):
        if "OPENROUTER_API_KEY" not in get_keys:
            return
        tokens = {"api_key": get_keys["OPENROUTER_API_KEY"]}
        integration = sample_integration_dict("openrouter", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]

        tokens = {"api_key": get_keys["OPENROUTER_API_KEY"][:-3]}
        integration = sample_integration_dict("openrouter", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_actions_run(self, get_keys, sample_restapi_task, sample_integration_dict):
        if "OPENROUTER_API_KEY" not in get_keys:
            return
        tokens = {"api_key": get_keys["OPENROUTER_API_KEY"]}
        integration = sample_integration_dict("openrouter", tokens)
        service = integration_service_factory.get_service(None, integration)
        actions = service.get_all_rest_api_actions()
        for action in actions:
            try:
                task = sample_restapi_task(
                    integration, action.code, action.parameters_definition
                )
                result = handle_task(task)
                print(result.model_dump_json(indent=2))
            except Exception:
                traceback.print_exc()
