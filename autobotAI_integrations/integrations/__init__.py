import importlib
import platform
import inspect
import os

from pydantic import BaseModel

from autobotAI_integrations import BaseService
from autobotAI_integrations.integration_schema import IntegrationSchema


class IntegrationServiceFactory:
    def __init__(self):
        self._services = {}
        for obj in self._get_subclasses():
            self._services[obj["module_name"]] = obj["subclass"]

    def get_service_cls(self, service):
        cls = self._services.get(service)
        if not cls:
            raise ValueError(service)
        return cls

    def get_services(self):
        return list(self._services.keys())

    def get_service_details(self, q=None):
        details_list = []
        for integration_type in list(self._services.keys()):
            srvic_cls = integration_service_factory.get_service_cls(integration_type)
            integration_schema = srvic_cls.get_schema()
            temp = srvic_cls.get_details()

            temp["name"] = integration_type
            temp["logo"] = integration_schema.model_fields.get("logo").default
            temp["description"] = integration_schema.model_fields.get(
                "description"
            ).default
            temp["category"] = integration_schema.model_fields.get("category").default
            if not q or not q.get("category") or q.get("category") == temp["category"]:
                details_list.append(temp)
            details_list.append(temp)
        return details_list

    def get_service(self, ctx, integration):

        if not isinstance(integration, BaseModel):
            csp_name = integration.get("cspName")
        else:
            csp_name = integration.cspName
        cls = self._services.get(csp_name)
        if not cls:
            raise ValueError(csp_name)

        if isinstance(integration, BaseModel) and not isinstance(
            integration, cls.get_schema()
        ):
            return cls(ctx, integration.model_dump())
        return cls(ctx, integration)

    @staticmethod
    def _get_subclasses(serv: BaseService = BaseService):
        # get current working directory
        directory = os.path.dirname(os.path.abspath(__file__))
        # get folder names
        integrations_list = [
            f.name
            for f in os.scandir(directory)
            if f.is_dir() and not f.name.startswith(".") and not f.name.startswith("__")
        ]

        system_os = platform.system()
        if system_os == "Windows":
            sep = "\\"
        else:
            sep = "/"
        # import integration service folder
        for filename in integrations_list:
            importlib.import_module(
                f"autobotAI_integrations.integrations.{filename}", package=None
            )
        result = []
        for x in serv.__subclasses__():
            module_name = os.path.dirname(inspect.getfile(x)).split(sep)[-1]
            if module_name == "autobotAI_integrations":
                result.extend(IntegrationServiceFactory._get_subclasses(x))
            else:
                subclass = x
                result.append({"module_name": module_name, "subclass": subclass})
        return result


class InvalidIntegration(Exception):
    """Base class for other exceptions"""

    pass


integration_service_factory = IntegrationServiceFactory()
