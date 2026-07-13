import os

import pytest
from autobotAI_integrations.integrations import integration_service_factory


class TestClassISP:
    @classmethod
    def setup_class(cls):
        integrations_path = os.path.join(
            os.path.abspath(os.getcwd()), "autobotAI_integrations", "integrations"
        )
        cls.integrations = [
            integration
            for integration in os.listdir(integrations_path)
            if not integration.startswith("__")
            and os.path.isdir(os.path.join(integrations_path, integration))
        ]

    @classmethod
    def teardown_class(cls):
        pass

    def test_service_object(self):
        services = integration_service_factory._services
        assert len(self.integrations) == len(services)
        integration_set = set(self.integrations)
        services_set = set(services)
        assert integration_set == services_set
        for service in services:
            assert service in integration_set

    def test_lazy_single_type_load(self):
        factory = integration_service_factory
        before = set(factory._loaded_modules)
        cls = factory.get_service_cls("abuseipdb")
        assert cls is not None
        assert "abuseipdb" in factory._loaded_modules
        assert len(factory._loaded_modules - before) == 1

    def test_get_services_without_importing_vendors(self):
        before = set(integration_service_factory._loaded_modules)
        names = integration_service_factory.get_services()
        assert len(names) == len(self.integrations)
        assert integration_service_factory._loaded_modules == before

    def test_get_service_details(self):
        pass

    def test_get_service(self):
        pass
