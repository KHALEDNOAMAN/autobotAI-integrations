import uuid

from autobotai_integrations.autobotai_integrations import BaseSchema, SteampipeCreds, RestAPICreds, SDKCreds, CLICreds, \
    BaseService


class GitlabIntegration(BaseSchema):
    base_url: str
    token: str

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)


class GitlabService(BaseService):

    def __init__(self, ctx, integration: dict):
        super().__init__(ctx, integration)
        self.base_url = integration["base_url"]
        self.token = integration["token"]

    @staticmethod
    def get_schema():
        return GitlabIntegration

    @staticmethod
    def test_integration(integration: dict):
        return {'success': True}

    def get_credentials(self):
        return {
            "base_url": self.base_url,
            "token": self.token
        }

    @staticmethod
    def get_all_python_sdk_clients():
        clients = {
            "gitlab": {
                "name": "gitlab",
                "code": "gitlab.Gitlab(os.getenv('GITLAB_ADDR'), private_token=os.getenv('GITLAB_TOKEN'))",
                "package_names": ["python-gitlab"],
                "library_names": ["gitlab"]
            }
        }
        return clients

    def generate_steampipe_creds(self) -> SteampipeCreds:
        envs = {
            "GITLAB_ADDR": self.base_url,
            "GITLAB_TOKEN": self.token,
        }
        conf_path = "~/.steampipe/config/gitlab.spc"

        return SteampipeCreds(envs=envs, plugin_name="theapsgroup/gitlab", connection_name="gitlab",
                              conf_path=conf_path)

    def generate_rest_api_creds(self) -> RestAPICreds:
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        return RestAPICreds(api_url=self.base_url, token=self.token, headers=headers)

    def generate_python_sdk_creds(self) -> SDKCreds:
        package_names = ["python-gitlab"]
        library_names = ["gitlab"]
        envs = {
            "GITLAB_ADDR": self.base_url,
            "GITLAB_TOKEN": self.token,
        }
        clients = self.get_all_python_sdk_clients()
        return SDKCreds(library_names=library_names, clients=clients, envs=envs, package_names=package_names)

    def generate_cli_creds(self) -> CLICreds:
        installer_check = "brew"
        install_command = "brew list glab || brew install glab"
        envs = {
            "GITLAB_HOST": self.base_url,
            "GITLAB_TOKEN": self.token,
        }
        return CLICreds(installer_check=installer_check, install_command=install_command, envs=envs)


"""def fetch(clients, test=False):
    if clients.get("Storage"):
        print("GCP Storage client found'")
        print(clients.get("Storage").list_buckets(0))
        return clients.get("Storage").list_buckets(0)
    if clients.get("ComputeManagementClient"):
        print("Azure Compute Management Client fond")
        print(clients.get("ComputeManagementClient").virtual_machines.list_all())
        return list(clients.get("ComputeManagementClient").virtual_machines.list_all())
    if clients.get("s3"):
        print("AWS S3 Client Found")
        print(clients.get("s3").list_buckets())
        return clients.get("s3").list_buckets()
    if clients.get("gitlab"):
        print("Gitlab Client Found")
        print(clients.get("gitlab").projects.list())
        return list(clients.get("gitlab").projects.list())"""

"""
{
    "userId": "amit@shunyeka.com",
    "accountId": "175c0fa813244bc5a1aa6264e7ba20cc",
    "integrationState": "INACTIVE",
    "cspName": "gitlab",
    "alias": "test-gitlab-integrationsv2",
    "connection_type": "DIRECT",
    "groups": [
        "gitlab",
        "shunyeka",
        "integrations-v2"
    ],
    "agent_ids": [],
    "accessToken": "",
    "createdAt": "2024-02-26T13:38:59.978056",
    "updatedAt": "2024-02-26T13:38:59.978056",
    "indexFailures": 0,
    "isUnauthorized": false,
    "lastUsed": null,
    "resource_type": "integration",
    "activeRegions": null
}
"""
"""
Fetcher = ObjectId("65defd146f1cc88d60ec857a")
"""
"""
BotV2 = ObjectId("65defe3c6795ab5c72c74f22")
"""