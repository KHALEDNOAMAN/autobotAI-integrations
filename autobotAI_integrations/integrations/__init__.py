import importlib
import platform
import inspect
import os

from pydantic import BaseModel

from autobotAI_integrations import BaseService


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

    def get_service_details(self):
        details_list = []
        for integration_type in list(self._services.keys()):
            int_s = integration_service_factory.get_service_cls(
                integration_type)
            temp = int_s.get_details()
            temp["name"] = integration_type
            details_list.append(temp)
        return details_list

    def get_service(self, ctx, integration):
        cls = self._services.get(integration.cspName)
        if not cls:
            raise ValueError(integration.cspName)
        if isinstance(integration, BaseModel) and not isinstance(integration, cls.get_schema()):
            return cls(ctx, integration.model_dump())
        return cls(ctx, integration)


    @staticmethod
    def _get_subclasses():
        # get current working directory
        directory = os.path.dirname(os.path.abspath(__file__))
        # get folder names
        integrations_list = [
            f.name 
            for f in os.scandir(directory) 
            if f.is_dir() 
            and not f.name.startswith(".")
            and not f.name.startswith("__")
        ]

        system_os = platform.system()
        if system_os == "Windows":
            sep = "\\"
        else:
            sep = "/"
        # import integration service folder
        for filename in integrations_list:
            importlib.import_module(f"autobotAI_integrations.integrations.{filename}", package=None)
        result = []
        for x in BaseService.__subclasses__():
            module_name = os.path.dirname(inspect.getfile(x)).split(sep)[-1]
            subclass = x
            result.append({"module_name": module_name, "subclass": subclass})
        return result


class InvalidIntegration(Exception):
    """Base class for other exceptions"""
    pass


integration_service_factory = IntegrationServiceFactory()
