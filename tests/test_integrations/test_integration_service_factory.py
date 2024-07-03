import pytest, os
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
        ]
        cls.services = integration_service_factory._services

    @classmethod
    def teardown_class(cls):
        pass

    def test_service_object(self):
        assert len(self.integrations) == len(self.services.keys())
        integration_set = set(self.integrations)
        services_set = set(self.services.keys())
        assert integration_set == services_set
        for service in self.services.keys():
            assert service in integration_set

    def test_get_services(self):
        pass

    def test_get_service_details(self):
        pass
    
    def test_get_service(self):
        pass
