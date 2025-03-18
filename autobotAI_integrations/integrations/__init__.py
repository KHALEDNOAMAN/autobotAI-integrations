import importlib
import platform
import inspect
import os

from pydantic import BaseModel

from autobotAI_integrations import BaseService, AIBaseService


class IntegrationServiceFactory:
    def __init__(self):
        self._services = {}
        self._ai_services = {}
        for obj in self._get_subclasses():
            self._services[obj["module_name"]] = obj["subclass"]
        for obj in self._get_subclasses(serv=AIBaseService):
            self._ai_services[obj["module_name"]] = obj["subclass"]

    def get_service_cls(self, service):
        cls = self._services.get(service)
        if not cls:
            raise ValueError(service)
        return cls

    def get_services(self):
        return list(self._services.keys())

    def get_ai_services(self):
        return list(self._ai_services.keys())

    def get_service_details(self, q=None):
        details_list = []
        if q and q.get("integration_type"):
            integration_types = [q["integration_type"]]
        else:
            integration_types = list(self._services.keys())
        for integration_type in integration_types:
            srvic_cls = integration_service_factory.get_service_cls(integration_type)
            integration_schema = srvic_cls.get_schema()
            temp = srvic_cls.get_details()

            # Used for frontend display
            temp["displayName"] = integration_schema.model_fields.get("name").default or integration_type.replace('_', ' ').title()
            # Used for links and service creation
            temp['name'] = integration_type
            temp["logo"] = integration_schema.model_fields.get("logo").default
            temp["description"] = integration_schema.model_fields.get(
                "description"
            ).default
            temp["category"] = integration_schema.model_fields.get("category").default
            details_list.append(temp)
        if q and q.get("category"):
            details_list = [
                detail for detail in details_list if detail["category"] == q.get("category")
            ]
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
