import importlib
import platform
import inspect
import os
from autobotai_integrations.autobotai_integrations import BaseService


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

    @staticmethod
    def _get_subclasses():
        # get current working directory
        directory = os.path.dirname(os.path.abspath(__file__))
        # get folder names
        integrations_list = [f.name for f in os.scandir(directory) if f.is_file() and f.name.endswith(".py")]

        system_os = platform.system()
        if system_os == "Windows":
            sep = "\\"
        else:
            sep = "/"

        # import each file in each folder where the file ends with 'service.py'
        for filename in integrations_list:
            importlib.import_module(f"autobotai_integrations.integrations.{filename[:-3]}", package=None)
        result = []
        for x in BaseService.__subclasses__():
            module_name = inspect.getfile(x).split(sep)[-1][:-3]
            subclass = x
            result.append({"module_name": module_name, "subclass": subclass})
        return result


class InvalidIntegration(Exception):
    """Base class for other exceptions"""
    pass


integration_service_factory = IntegrationServiceFactory()
print(integration_service_factory.get_services())
