import copy
from typing import Optional, Type, Union

import requests
from pydantic import Field, field_validator

from autobotAI_integrations import BaseSchema, BaseService, ConnectionInterfaces
from autobotAI_integrations.models import IntegrationCategory, RestAPICreds
from autobotAI_integrations.payload_schema import PayloadTask

DEFAULT_API_PATH = (
    "/REST/Summit_RESTWCF.svc/RESTService/CommonWS_JsonObjCall"
)
DEFAULT_PROXY_ID = 0
DEFAULT_ORG_ID = 1


class SymphonySummitIntegration(BaseSchema):
    base_url: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None, exclude=True)

    name: Optional[str] = "Symphony Summit"
    category: Optional[str] = (
        IntegrationCategory.NOTIFICATIONS_AND_COMMUNICATIONS.value
    )
    description: Optional[str] = (
        "Symphony SummitAI ITSM platform — manage incidents, service requests, "
        "and service catalog via the Summit REST WCF API."
    )

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_base_url(cls, base_url) -> Optional[str]:
        if not base_url or base_url == "None":
            raise ValueError("Symphony Summit instance URL is required")
        url = str(base_url).strip().rstrip("/")
        if not url.startswith(("http://", "https://")):
            raise ValueError(
                f"Invalid Symphony Summit URL: {base_url}. "
                "Format: https://yourcompany.symphonysummit.com"
            )
        return url

    @property
    def api_url(self) -> str:
        if "CommonWS_JsonObjCall" in self.base_url:
            return self.base_url
        path = DEFAULT_API_PATH
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{self.base_url}{path}"

    def proxy_details(
        self,
        api_key: Optional[str] = None,
        org_id: Optional[int] = None,
    ) -> dict:
        """Build _ProxyDetails for Summit API requests.

        ProxyID and OrgID are required JSON fields per Summit docs; standard
        single-tenant deployments use 0 and 1 respectively — not separate creds.
        """
        return {
            "AuthType": "APIKEY",
            "APIKey": api_key if api_key is not None else self.api_key,
            "ProxyID": DEFAULT_PROXY_ID,
            "OrgID": org_id if org_id is not None else DEFAULT_ORG_ID,
            "ReturnType": "JSON",
            "TokenID": "",
        }


class SymphonySummitService(BaseService):
    _AUTH_ERROR_KEYWORDS = (
        "invalid api",
        "authentication",
        "unauthorized",
        "invalid key",
        "access denied",
        "not authorized",
    )

    def __init__(
        self, ctx: dict, integration: Union[SymphonySummitIntegration, dict]
    ):
        if not isinstance(integration, SymphonySummitIntegration):
            integration = SymphonySummitIntegration(**integration)
        super().__init__(ctx, integration)

    def _summit_envs(self) -> dict:
        return {
            "SYMPHONY_SUMMIT_BASE_URL": self.integration.base_url,
            "SYMPHONY_SUMMIT_API_URL": self.integration.api_url,
            "SYMPHONY_SUMMIT_API_KEY": self.integration.api_key,
            "SYMPHONY_SUMMIT_PROXY_ID": DEFAULT_PROXY_ID,
            "SYMPHONY_SUMMIT_ORG_ID": DEFAULT_ORG_ID,
        }

    def _inject_proxy_details(
        self, json_data: Optional[dict], envs: Optional[dict] = None
    ) -> Optional[dict]:
        if not json_data or not isinstance(json_data, dict):
            return json_data

        envs = envs or self._summit_envs()
        api_key = envs.get("SYMPHONY_SUMMIT_API_KEY")

        body = copy.deepcopy(json_data)
        obj_params = body.setdefault("objCommonParameters", {})
        user_proxy = obj_params.get("_ProxyDetails") or {}

        org_id = user_proxy.get("OrgID")
        if org_id is None:
            org_id = envs.get("SYMPHONY_SUMMIT_ORG_ID", DEFAULT_ORG_ID)
        try:
            org_id = int(org_id) if org_id is not None else None
        except (TypeError, ValueError):
            org_id = None

        obj_params["_ProxyDetails"] = {
            **self.integration.proxy_details(api_key=api_key, org_id=org_id),
            **{k: v for k, v in user_proxy.items() if k not in ("APIKey", "AuthType")},
            "APIKey": api_key,
            "AuthType": "APIKEY",
        }
        return body

    def _response_indicates_auth_failure(self, response, data) -> bool:
        if response.status_code in (401, 403):
            return True
        if not isinstance(data, dict):
            return False
        errors = str(
            data.get("Errors") or data.get("Error") or data.get("Message") or ""
        ).lower()
        return any(keyword in errors for keyword in self._AUTH_ERROR_KEYWORDS)

    def _build_auth_probe_body(self, envs: Optional[dict] = None) -> dict:
        """Minimal request whose only purpose is to trigger Summit auth validation."""
        return self._inject_proxy_details(
            {
                "ServiceName": "IM_GetIncidentDetailsAndChangeHistory",
                "objCommonParameters": {"TicketNo": 0},
            },
            envs=envs,
        )

    def _evaluate_auth_probe(self, response, data) -> dict:
        """Auth-only result — connected and API key accepted, or a specific failure."""
        content_type = response.headers.get("Content-Type", "").lower()

        if response.status_code in (404, 405):
            return {
                "success": False,
                "error": (
                    "Symphony Summit endpoint not found. "
                    "Check the instance URL and REST API path."
                ),
            }

        if "text/html" in content_type and not isinstance(data, dict):
            return {
                "success": False,
                "error": (
                    "Invalid endpoint — received HTML instead of a Summit API response. "
                    "Check the instance URL."
                ),
            }

        if self._response_indicates_auth_failure(response, data):
            return {
                "success": False,
                "error": "Authentication failed. Invalid API key or insufficient permissions.",
            }

        if response.status_code >= 500:
            return {
                "success": False,
                "error": f"Symphony Summit server error ({response.status_code}).",
            }

        # Auth passed — ignore business-level errors (e.g. ticket not found).
        if isinstance(data, dict) or response.status_code < 400:
            return {
                "success": True,
                "message": "Connected and authenticated successfully.",
            }

        return {
            "success": False,
            "error": (
                f"Connection check failed ({response.status_code}): "
                f"{response.text[:300]}"
            ),
        }

    def _test_integration(self) -> dict:
        """Auth-only check: endpoint reachable and API key accepted."""
        creds = self.generate_rest_api_creds()
        if not creds.envs.get("SYMPHONY_SUMMIT_API_KEY"):
            return {"success": False, "error": "API key is required."}

        try:
            response = requests.post(
                creds.base_url,
                json=self._build_auth_probe_body(envs=creds.envs),
                headers=creds.headers,
                timeout=15,
            )
            try:
                data = response.json()
            except ValueError:
                data = None

            return self._evaluate_auth_probe(response, data)
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection is unreachable"}
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Connection timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def execute_rest_api_task(self, payload_task: PayloadTask):
        envs = payload_task.creds.envs or self._summit_envs()
        updated_params = []
        for param in payload_task.params:
            if getattr(param, "name", None) == "body" and isinstance(
                param.values, dict
            ):
                param = param.model_copy(
                    update={
                        "values": self._inject_proxy_details(
                            param.values, envs=envs
                        ),
                    }
                )
            updated_params.append(param)
        return super().execute_rest_api_task(
            payload_task.model_copy(update={"params": updated_params})
        )

    @staticmethod
    def get_forms():
        return {
            "label": "Symphony Summit",
            "type": "form",
            "children": [
                {
                    "name": "base_url",
                    "type": "text/url",
                    "label": "Instance URL",
                    "placeholder": "https://yourcompany.symphonysummit.com",
                    "description": (
                        "Your Symphony SummitAI instance URL"
                    ),
                    "required": True,
                },
                {
                    "name": "api_key",
                    "type": "text/password",
                    "label": "API Key",
                    "placeholder": "Enter your SummitAI API Key",
                    "description": (
                        "Generate from Admin > Basic > Users — set Login Type to API Key."
                    ),
                    "required": True,
                },
            ],
        }

    @staticmethod
    def get_schema(ctx=None) -> Type[BaseSchema]:
        return SymphonySummitIntegration

    @classmethod
    def get_details(cls):
        details = super().get_details()
        details["preview"] = True
        return details

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.REST_API]

    def generate_rest_api_creds(self) -> RestAPICreds:
        return RestAPICreds(
            base_url=self.integration.api_url,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            envs=self._summit_envs(),
        )
