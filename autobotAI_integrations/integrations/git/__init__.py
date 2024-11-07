import uuid
from typing import List, Type, Union
import importlib
import platform, subprocess

from autobotAI_integrations import list_of_unique_elements
from autobotAI_integrations.models import *
from autobotAI_integrations.models import List
from autobotAI_integrations import BaseSchema, SDKCreds, CLICreds, \
    BaseService, ConnectionInterfaces, PayloadTask, SDKClient


class GitIntegration(BaseSchema):
    category: Optional[str] = IntegrationCategory.CODE_REPOSITORY.value
    description: Optional[str] = (
        "Git is a free and open-source distributed version control system (DVCS) for tracking changes in computer code and other projects."
    )


class GitService(BaseService):

    def __init__(self, ctx: dict, integration: Union[GitIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, GitIntegration):
            integration = GitIntegration(**integration)
        super().__init__(ctx, integration)

    def _test_integration(self, user_initiated_request: bool = False) -> dict:
        if not self._is_git_installed():
            self._install_git_with_python()
            if not self._is_git_installed():
                return {"success": False, "error": str("git is not installed on machine")}
        return {"success": True}

    @staticmethod
    def get_forms():
        return {
            "label": "Git Integration",
            "type": "form",
            "children": []
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return GitIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample(),
        }

    def _is_git_installed(self):
        """Checks if Git is installed on the system."""
        try:
            # Attempt to run the git version command
            subprocess.run(["git", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def _install_git_with_python(self):
        """Installs Git using the appropriate package manager based on OS."""
        os_name = platform.system()
        if os_name == "Linux":
            package_manager = subprocess.check_output(
                "which apt-get || which yum || which dnf",
                shell=True
            ).decode("utf-8").strip()
            if package_manager:
                subprocess.run(
                    [package_manager.split()[0],"install", "git"]
                )
            else:
                print("Error: Could not identify a suitable package manager for Linux.")
        elif os_name == "Darwin":  # macOS
            if subprocess.run(
                ["brew", "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            ) == 0:
                subprocess.run(["brew", "install", "git"])
            else:
                print("Error: Could not install Git using Homebrew. Consider manual installation.")
        else:
            print(f"Warning: Installing Git on {os_name} is not supported through this script. Consider manual installation.")

    def build_python_exec_combinations_hook(
            self, payload_task: PayloadTask, client_definitions: List[SDKClient]
    ) -> list:
        if not self._is_git_installed():
            self._install_git_with_python()

        client = importlib.import_module(client_definitions[0].import_library_names[0], package=None)
        return [
            {
                "clients": {
                    "git": client,
                },
                "params": self.prepare_params(payload_task.params),
                "context": payload_task.context
            }
        ]

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        envs = {}
        return SDKCreds(creds={}, envs=envs)

    @staticmethod
    def supported_connection_interfaces():
        return [
            ConnectionInterfaces.PYTHON_SDK,
        ]

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()
