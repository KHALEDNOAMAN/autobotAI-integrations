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

    Metadata cache (display name, description, category, logo, supported
    interfaces) is populated on demand for filtering in
    ``get_service_details``.
    """

    def __init__(self) -> None:
        self._services_dict: Optional[dict] = None
        self._ai_services_dict: Optional[dict] = None
        self._init_lock = threading.Lock()
        self._metadata_cache: Optional[dict] = None
        self._cache_built: bool = False
        self._metadata_lock = threading.Lock()

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
    # Lazy metadata cache (powers filtering in get_service_details)
    # ------------------------------------------------------------------
    def _ensure_metadata_cache(self) -> None:
        """Build the metadata cache once, lazily, on first filtered access."""
        if self._cache_built:
            return
        with self._metadata_lock:
            if self._cache_built:
                return
            cache: dict = {}
            for integration_type, service_cls in self._services.items():
                try:
                    integration_schema = service_cls.get_schema()

                    display_name = (
                        integration_schema.model_fields.get("name").default
                        or integration_type.replace("_", " ").title()
                    )
                    description = (
                        integration_schema.model_fields.get("description").default or ""
                    )
                    category = integration_schema.model_fields.get("category").default
                    logo = integration_schema.model_fields.get("logo").default

                    supported_interfaces = []
                    if hasattr(service_cls, "supported_connection_interfaces"):
                        try:
                            interfaces = service_cls.supported_connection_interfaces()
                            supported_interfaces = [
                                str(iface.value) if hasattr(iface, "value") else str(iface)
                                for iface in interfaces
                            ]
                        except Exception:
                            pass

                    cache[integration_type] = {
                        "module_name": integration_type,
                        "name": integration_type,
                        "displayName": display_name,
                        "description": description,
                        "category": category,
                        "logo": logo,
                        "supported_interfaces": supported_interfaces,
                    }
                except Exception as e:
                    # One bad integration shouldn't break the whole factory.
                    print(
                        f"Warning: Failed to build metadata cache for {integration_type}: {e}"
                    )
                    continue
            self._metadata_cache = cache
            self._cache_built = True

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

    def get_service_details(self, q=None, include_details=True):
        """
        Get service details with enhanced filtering capabilities.

        Args:
            q (dict, optional): Filter query with the following supported keys:
                - integration_type (str): Specific integration to retrieve
                - category (str): Filter by category
                - name (str): Partial match on display name (case-insensitive)
                - search (str): Search across name and description (case-insensitive)
                - exclude_types (list): List of integration types to exclude
                - supported_interfaces (list): Filter by supported connection interfaces
            include_details (bool): If True, includes full details from get_details().
                                   If False, returns only cached metadata (faster).
                                   Default: True for backward compatibility.

        Returns:
            list: List of integration details matching the filter criteria
        """
        # Triggers lazy registry load + lazy metadata cache build.
        self._ensure_metadata_cache()

        candidate_types = list(self._services.keys())

        if q:
            if q.get("integration_type"):
                candidate_types = [q["integration_type"]]

            if q.get("exclude_types"):
                exclude_set = set(q["exclude_types"])
                candidate_types = [t for t in candidate_types if t not in exclude_set]

            if q.get("category"):
                candidate_types = [
                    t for t in candidate_types
                    if self._metadata_cache.get(t, {}).get("category") == q["category"]
                ]

            if q.get("name"):
                search_term = q["name"].lower()
                candidate_types = [
                    t for t in candidate_types
                    if search_term in self._metadata_cache.get(t, {}).get("displayName", "").lower()
                ]

            if q.get("search"):
                search_term = q["search"].lower()
                candidate_types = [
                    t for t in candidate_types
                    if (search_term in self._metadata_cache.get(t, {}).get("displayName", "").lower()
                        or search_term in self._metadata_cache.get(t, {}).get("description", "").lower())
                ]

        details_list = []
        for integration_type in candidate_types:
            if integration_type not in self._services:
                continue

            temp = self._metadata_cache.get(integration_type, {}).copy()

            if include_details:
                srvic_cls = self.get_service_cls(integration_type)
                details = srvic_cls.get_details()
                temp.update(details)

            if q and q.get("supported_interfaces"):
                required_interfaces = set(q["supported_interfaces"])
                integration_interfaces = set(temp.get("supported_interfaces", []))
                if not required_interfaces.intersection(integration_interfaces):
                    continue

            details_list.append(temp)

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


# Module-level singleton. Construction is now cheap (just a few attribute
# assignments + Locks); the 70+ vendor-SDK imports happen on the first
# method call that needs the registry.
integration_service_factory = IntegrationServiceFactory()
