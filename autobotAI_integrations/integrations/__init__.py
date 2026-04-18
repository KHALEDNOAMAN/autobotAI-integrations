import importlib
import os
import threading
from typing import Optional


class IntegrationServiceFactory:
    """
    Registry of integration service classes.

    The heavy work — scanning the ``autobotAI_integrations/integrations``
    directory and importing 70+ vendor subpackages (each of which pulls
    in their own SDK, e.g. ``boto3``, ``google-cloud-*``, ``azure-*``,
    ``kubernetes``, ``snowflake-connector-python``, …) — is deferred
    until the first time the registry is actually read.

    Previously this class did all that work in ``__init__``, and a
    module-level ``integration_service_factory = IntegrationServiceFactory()``
    meant *every* import of anything in ``autobotAI_integrations.integrations``
    paid the full cost. Now the object exists immediately and only populates
    itself on first attribute access that needs the registry.
    """

    def __init__(self) -> None:
        self._services_dict: Optional[dict] = None
        self._ai_services_dict: Optional[dict] = None
        self._init_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Lazy registry
    # ------------------------------------------------------------------
    def _ensure_loaded(self) -> None:
        if self._services_dict is not None and self._ai_services_dict is not None:
            return
        with self._init_lock:
            if self._services_dict is not None and self._ai_services_dict is not None:
                return
            # Local imports: these themselves pull pydantic + our base
            # service classes, so we avoid them at module import time.
            from autobotAI_integrations import BaseService, AIBaseService

            services: dict = {}
            ai_services: dict = {}
            for obj in self._get_subclasses(BaseService):
                services[obj["module_name"]] = obj["subclass"]
            for obj in self._get_subclasses(AIBaseService):
                ai_services[obj["module_name"]] = obj["subclass"]
            # Publish atomically.
            self._services_dict = services
            self._ai_services_dict = ai_services

    # Backward-compat property access. Several call sites (and tests)
    # read ``integration_service_factory._services`` directly.
    @property
    def _services(self) -> dict:
        self._ensure_loaded()
        return self._services_dict  # type: ignore[return-value]

    @property
    def _ai_services(self) -> dict:
        self._ensure_loaded()
        return self._ai_services_dict  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Public API (unchanged signatures)
    # ------------------------------------------------------------------
    def get_service_cls(self, service):
        cls = self._services.get(service)
        if not cls:
            raise ValueError(service)
        return cls

    def get_services(self):
        return list(self._services.keys())

    def get_ai_services(self):
        return list(self._ai_services.keys())

    def get_service_details(self, q=None):
        details_list = []
        services = self._services  # triggers lazy load once
        if q and q.get("integration_type"):
            integration_types = [q["integration_type"]]
        else:
            integration_types = list(services.keys())
        for integration_type in integration_types:
            srvic_cls = self.get_service_cls(integration_type)
            integration_schema = srvic_cls.get_schema()
            temp = srvic_cls.get_details()

            # Used for frontend display
            temp["displayName"] = (
                integration_schema.model_fields.get("name").default
                or integration_type.replace("_", " ").title()
            )
            # Used for links and service creation
            temp["name"] = integration_type
            temp["logo"] = integration_schema.model_fields.get("logo").default
            temp["description"] = integration_schema.model_fields.get(
                "description"
            ).default
            temp["category"] = integration_schema.model_fields.get("category").default
            details_list.append(temp)
        if q and q.get("category"):
            details_list = [
                detail
                for detail in details_list
                if detail["category"] == q.get("category")
            ]
        return details_list

    def get_service(self, ctx, integration):
        # Local import of pydantic.BaseModel — avoids loading pydantic
        # merely by importing the integrations package.
        from pydantic import BaseModel

        if not isinstance(integration, BaseModel):
            csp_name = integration.get("cspName")
        else:
            csp_name = integration.cspName
        cls = self._services.get(csp_name)
        if not cls:
            raise ValueError(csp_name)

        if isinstance(integration, BaseModel) and not isinstance(
            integration, cls.get_schema()
        ):
            return cls(ctx, integration.model_dump())
        return cls(ctx, integration)

    # ------------------------------------------------------------------
    # Integration discovery
    # ------------------------------------------------------------------
    @staticmethod
    def _get_subclasses(serv):
        """Recursively discover subclasses of ``serv`` by importing every
        subdirectory of ``autobotAI_integrations/integrations``.

        NOTE: ``inspect`` and ``platform`` are imported lazily — they're
        only needed when we actually populate the registry.
        """
        import inspect
        import platform

        directory = os.path.dirname(os.path.abspath(__file__))
        integrations_list = [
            f.name
            for f in os.scandir(directory)
            if f.is_dir() and not f.name.startswith(".") and not f.name.startswith("__")
        ]

        sep = "\\" if platform.system() == "Windows" else "/"

        for filename in integrations_list:
            importlib.import_module(
                f"autobotAI_integrations.integrations.{filename}", package=None
            )
        result = []
        for x in serv.__subclasses__():
            module_name = os.path.dirname(inspect.getfile(x)).split(sep)[-1]
            if module_name == "autobotAI_integrations":
                result.extend(IntegrationServiceFactory._get_subclasses(x))
            else:
                subclass = x
                result.append({"module_name": module_name, "subclass": subclass})
        return result


class InvalidIntegration(Exception):
    """Base class for other exceptions."""

    pass


# Module-level singleton. Construction is now cheap (just a couple of
# ``None`` assignments + a Lock); the 70+ vendor-SDK imports happen on
# the first method call that needs the registry.
integration_service_factory = IntegrationServiceFactory()
