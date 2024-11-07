from typing import Type, Union
import uuid
from pydantic import model_validator
from autobotAI_integrations import BaseService, list_of_unique_elements, PayloadTask
from autobotAI_integrations.models import *


class Forms:
    pass


class PythonIntegration(BaseSchema):

    category: Optional[str] = IntegrationCategory.OTHERS.value
    description: Optional[str] = (
        "Python is a programming language that lets you work more quickly and integrate your systems more effectively."
    )
    def __init__(self, **kwargs):
        if not kwargs.get("accountId"):
            kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)

    @model_validator(mode="before")
    @classmethod
    def resource_type_validator(cls, values: Any) -> Any:
        if values.get("accountId", None):
            values["accountId"] = str(values["accountId"])
        return values


class PythonService(BaseService):

    def __init__(self, ctx: dict, integration: Union[PythonIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, PythonIntegration):
            integration = PythonIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self) -> dict:
        return {"success": True}

    @staticmethod
    def get_forms():
        return {
            "label": "Python",
            "type": "form",
            "children": [
                {
                    "label": "Base Integration Creator",
                    "type": "form",
                    "children": []
                }
            ]
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return PythonIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": [],
            "supported_executor": "lambda",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample()
        }

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        return [
            {
                "clients": {},
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = {}
        return SDKCreds(envs=creds)

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.PYTHON_SDK]
