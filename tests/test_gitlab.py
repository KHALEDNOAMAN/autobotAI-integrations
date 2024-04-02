import unittest
from unittest.mock import MagicMock, patch
from autobotAI_integrations.integrations.gitlab import GitlabService, GitlabIntegration


class TestGitlabService(unittest.TestCase):

    def setUp(self):
        # Initialize GitlabService instance with mock data
        self.integration = {
            "base_url": "https://gitlab.com",
            "token": "YOUR_TOKEN"
        }
        self.service = GitlabService(MagicMock(), self.integration)

    def test_get_schema(self):
        # Test get_schema method
        schema = self.service.get_schema()
        self.assertIsInstance(schema, GitlabIntegration)

    @patch("autobotAI_integrations.BaseService.generic_rest_api_call")
    def test__test_integration_success(self, mock_generic_rest_api_call):
        # Mock generic_rest_api_call to return a successful response
        mock_generic_rest_api_call.return_value = {"user": "example_user"}

        # Call _test_integration method
        result = self.service._test_integration(self.integration)

        # Assert that the result indicates success
        self.assertTrue(result["success"])
        # You can also further assert on the specific behavior if needed

    @patch("autobotAI_integrations.BaseService.generic_rest_api_call")
    def test__test_integration_failure(self, mock_generic_rest_api_call):
        # Mock generic_rest_api_call to raise an exception (simulate failure)
        mock_generic_rest_api_call.side_effect = Exception("API call failed")

        # Call _test_integration method
        result = self.service._test_integration(self.integration)

        # Assert that the result indicates failure
        self.assertFalse(result["success"])
        # You can also further assert on the specific behavior if needed

    # Write similar test methods for other public methods in GitlabService class

if __name__ == '__main__':
    unittest.main()
