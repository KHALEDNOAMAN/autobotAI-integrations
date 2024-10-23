import pytest

from autobotAI_integrations.integrations import integration_service_factory


class TestClassCrowdSec:
    def test_crowdsec_token(
        self,
        get_keys,
        sample_integration_dict,
        test_result_format,
    ):
        tokens = {
            "token": get_keys['CROWDSEC_API_KEY'],
        }
        integration = sample_integration_dict("crowdsec", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert res["success"]

        tokens = {
            "token": get_keys["CROWDSEC_API_KEY"][:-2],
        }
        integration = sample_integration_dict("crowdsec", tokens)
        service = integration_service_factory.get_service(None, integration)
        res = service.is_active()
        assert not res["success"]
