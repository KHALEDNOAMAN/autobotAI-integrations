from autobotAI_integrations.integrations import integration_service_factory


class TestClassSnyk:
    def test_snyk_token(
        self,
        get_keys,
        sample_integration_dict,
        test_result_format,
    ):
        tokens = {
            "base_url": get_keys["WAZUH_BASE_URL"],
            "username": get_keys['WAZUH_USERNAME'],
            "password": get_keys["WAZUH_PASSWORD"]
        }
        integration = sample_integration_dict("wazuh", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert res["success"]

        tokens = {
            "base_url": get_keys["WAZUH_BASE_URL"],
            "username": get_keys["WAZUH_USERNAME"],
            "password": get_keys["WAZUH_PASSWORD"][:-2],
        }
        integration = sample_integration_dict("wazuh", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        print(res)
        assert not res["success"]

    def test_actions_generation(self, get_keys):
        service = integration_service_factory.get_service_cls("wazuh")
        actions = service.get_all_rest_api_actions()
        for action in actions:
            assert action.name is not None
            assert action.name.strip() != ""
        assert len(actions) > 0
