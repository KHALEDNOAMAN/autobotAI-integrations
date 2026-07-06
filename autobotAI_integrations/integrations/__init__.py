import importlib
import inspect
import os
import threading
from typing import Any, Dict, List, Optional


class IntegrationServiceFactory:
    """
    Registry of integration service classes with per-type lazy loading.

    Only the requested integration package (e.g. ``integrations.aws``) is imported
    when ``get_service_cls`` / ``get_service`` is called. Listing integration
    slugs via ``get_services`` uses directory scan only — no vendor SDK imports.

    Metadata for ``get_service_details`` is built per type on demand instead of
    importing every integration up front.
    """

    _INTEGRATIONS_PACKAGE = "autobotAI_integrations.integrations"

    def __init__(self) -> None:
        self._services_dict: Dict[str, type] = {}
        self._ai_services_dict: Dict[str, type] = {}
        self._init_lock = threading.Lock()
        self._metadata_cache: Dict[str, dict] = {}
        self._metadata_lock = threading.Lock()
        self._loaded_modules: set[str] = set()

    # ------------------------------------------------------------------
    # Discovery (no vendor imports)
    # ------------------------------------------------------------------
    @classmethod
    def _integrations_dir(cls) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    @classmethod
    def list_integration_module_names(cls) -> List[str]:
        return sorted(
            f.name
            for f in os.scandir(cls._integrations_dir())
            if f.is_dir() and not f.name.startswith(".") and not f.name.startswith("__")
        )

    # ------------------------------------------------------------------
    # Per-type loading
    # ------------------------------------------------------------------
    def _ensure_module_loaded(self, module_name: str) -> None:
        if module_name in self._loaded_modules:
            return
        with self._init_lock:
            if module_name in self._loaded_modules:
                return
            importlib.import_module(f"{self._INTEGRATIONS_PACKAGE}.{module_name}")
            self._register_classes_from_module(module_name)
            self._loaded_modules.add(module_name)

    def _register_classes_from_module(self, module_name: str) -> None:
        from autobotAI_integrations.base import AIBaseService, BaseService

        mod = importlib.import_module(f"{self._INTEGRATIONS_PACKAGE}.{module_name}")
        service_cls = None
        ai_cls = None
        for obj in vars(mod).values():
            if not inspect.isclass(obj) or obj in (BaseService, AIBaseService):
                continue
            try:
                if issubclass(obj, AIBaseService):
                    if ai_cls is None:
                        ai_cls = obj
                elif issubclass(obj, BaseService):
                    if service_cls is None:
                        service_cls = obj
            except TypeError:
                continue
        if service_cls is not None:
            self._services_dict[module_name] = service_cls
        if ai_cls is not None:
            self._ai_services_dict[module_name] = ai_cls

    def _ensure_all_loaded(self) -> None:
        for name in self.list_integration_module_names():
            self._ensure_module_loaded(name)

    # Backward-compat: accessing ``_services`` loads every integration module.
    @property
    def _services(self) -> dict:
        self._ensure_all_loaded()
        return self._services_dict

    @property
    def _ai_services(self) -> dict:
        self._ensure_all_loaded()
        return self._ai_services_dict

    # ------------------------------------------------------------------
    # Lazy metadata (P3)
    # ------------------------------------------------------------------
    def _get_metadata_for_type(self, integration_type: str) -> dict:
        if integration_type in self._metadata_cache:
            return self._metadata_cache[integration_type]
        with self._metadata_lock:
            if integration_type in self._metadata_cache:
                return self._metadata_cache[integration_type]
            self._ensure_module_loaded(integration_type)
            service_cls = self._services_dict.get(integration_type)
            if service_cls is None:
                service_cls = self._ai_services_dict.get(integration_type)
            if service_cls is None:
                raise ValueError(integration_type)
            entry = self._build_metadata_entry(integration_type, service_cls)
            self._metadata_cache[integration_type] = entry
            return entry

    @staticmethod
    def _build_metadata_entry(integration_type: str, service_cls: type) -> dict:
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
            return {
                "module_name": integration_type,
                "name": integration_type,
                "displayName": display_name,
                "description": description,
                "category": category,
                "logo": logo,
                "supported_interfaces": supported_interfaces,
            }
        except Exception as e:
            print(
                f"Warning: Failed to build metadata cache for {integration_type}: {e}"
            )
            return {
                "module_name": integration_type,
                "name": integration_type,
                "displayName": integration_type.replace("_", " ").title(),
                "description": "",
                "category": None,
                "logo": None,
                "supported_interfaces": [],
            }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_service_cls(self, service: str):
        self._ensure_module_loaded(service)
        cls = self._services_dict.get(service) or self._ai_services_dict.get(service)
        if not cls:
            raise ValueError(service)
        return cls

    def get_services(self):
        return self.list_integration_module_names()

    def get_ai_services(self):
        self._ensure_all_loaded()
        return list(self._ai_services_dict.keys())

    def get_service_details(self, q=None, include_details=True):
        candidate_types = self.list_integration_module_names()

        if q:
            if q.get("integration_type"):
                candidate_types = [q["integration_type"]]

            if q.get("exclude_types"):
                exclude_set = set(q["exclude_types"])
                candidate_types = [t for t in candidate_types if t not in exclude_set]

        details_list = []
        for integration_type in candidate_types:
            try:
                meta = self._get_metadata_for_type(integration_type)
            except ValueError:
                continue

            if q and q.get("category") and meta.get("category") != q["category"]:
                continue
            if q and q.get("name"):
                search_term = q["name"].lower()
                if search_term not in meta.get("displayName", "").lower():
                    continue
            if q and q.get("search"):
                search_term = q["search"].lower()
                if not (
                    search_term in meta.get("displayName", "").lower()
                    or search_term in meta.get("description", "").lower()
                ):
                    continue

            temp = meta.copy()
            if include_details:
                srvic_cls = self.get_service_cls(integration_type)
                temp.update(srvic_cls.get_details())

            if q and q.get("supported_interfaces"):
                required_interfaces = set(q["supported_interfaces"])
                integration_interfaces = set(temp.get("supported_interfaces", []))
                if not required_interfaces.intersection(integration_interfaces):
                    continue

            details_list.append(temp)

        return details_list

    def get_service(self, ctx, integration):
        from pydantic import BaseModel

        if not isinstance(integration, BaseModel):
            csp_name = integration.get("cspName")
        else:
            csp_name = integration.cspName
        cls = self.get_service_cls(csp_name)

        if isinstance(integration, BaseModel) and not isinstance(
            integration, cls.get_schema()
        ):
            return cls(ctx, integration.model_dump())
        return cls(ctx, integration)


class InvalidIntegration(Exception):
    """Base class for other exceptions."""

    pass


integration_service_factory = IntegrationServiceFactory()
