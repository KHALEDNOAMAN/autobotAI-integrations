import re
from typing import List, Optional
import yaml
import json
from autobotAI_integrations.open_api_schema import OpenAPIAction, OpenAPIPathModel, OpenAPISchema
from autobotAI_integrations.payload_schema import OpenAPIPathParams

class OpenApiParser:
    def __init__(self) -> None:
        self._parsed_dict: dict = {}
        self.version: Optional[str] = None
        self.base_url: Optional[str] = None
        self.paths: Optional[List[OpenAPIPathModel]] = None
        self.tags: Optional[List[dict]] = None
        self.security: Optional[List[dict]] = None
        self.components: Optional[dict] = dict()
        self.open_api_schema: Optional[OpenAPISchema] = None

    def _parse_version_type(self) -> None:
        """Determine the type and version of the API specification."""
        if "openapi" in self._parsed_dict:
            self.version = f"openapi {self._parsed_dict['openapi']}"
        elif "swagger" in self._parsed_dict:
            self.version = f"swagger {self._parsed_dict['swagger']}"
        else:
            self.version = "unknown"

    def _parse_base_url(self):
        if "servers" in self._parsed_dict:
            self.base_url = self._parsed_dict.get("servers")[0].get("url")
        elif "host" in self._parsed_dict:
            self.base_url = "https://" + self._parsed_dict.get("host")
        else:
            self.base_url = "{base_url}"

    def _extract_parameter_type(self, parameter: dict):
        """parses the data type of the parameter"""
        if "schema" in parameter and "type" in parameter["schema"]:
            return parameter["schema"]["type"]
        elif "type" in parameter:
            return parameter["type"]
        elif parameter.get('in', "query") == "path":
            return "string"
        else:
            return "object"

    def _extract_parameter_default(self, parameter: dict):
        """parses the data type of the parameter"""
        if "schema" in parameter and "default" in parameter["schema"]:
            return parameter["schema"]["default"]
        elif "default" in parameter:
            return parameter["default"]

    def _generate_body_parameter(self, request_body: dict) -> dict:
        """Generate a parameter object for the request body."""
        param = {
            "name": "body",
            "in": "body",
            "description": request_body.get("description", "Request body"),
            "required": request_body.get("required", True),
        }
        if request_body.get("content", {}).get("application/json"):
            schema = request_body["content"]["application/json"].get("schema", {})
            if "$ref" in schema:
                ref_name = schema["$ref"].split("/")[-1]
                param["example"] = self.components.get(ref_name)
            elif "example" in schema:
                param["example"] = schema["example"]
            else:
                param["example"] = schema.get("properties", {})
        param["type"] = "handlebars-json"  # We Only Support Json content types
        return OpenAPIPathParams(**param)

    def _generate_path_parameters(
        self, method_details: dict
    ) -> List[OpenAPIPathParams]:
        """parses the path parameters for url using method details"""
        parameters_list = []
        if self.base_url == "{base_url}":
            parameters_list.append(
                OpenAPIPathParams(**{
                    "name": "base_url",
                    "in": "path",
                    "type": "string",
                    "required": True,
                    "description": "Base URL of the API",
                })
            )
        if "parameters" in method_details:
            for parameter in method_details["parameters"]:
                parameter = self._resolve_reference(parameter)
                try:
                    parameter_type = self._extract_parameter_type(parameter)
                    if isinstance(parameter_type ,list):
                        parameter_type = parameter_type[0]
                    parameters_list.append(
                        OpenAPIPathParams(
                            **{
                                "type": parameter_type,
                                "values": self._extract_parameter_default(parameter),
                                **parameter,
                            }
                        )
                    )
                except Exception as e:
                    print(e)
                    continue
        if method_details.get("requestBody"):
            parameters_list.append(
                self._generate_body_parameter(method_details["requestBody"])
            )
        return parameters_list

    def _parse_paths(self) -> List[OpenAPIPathModel]:
        open_api_path_models = []
        if "paths" in self._parsed_dict:
            for path_url, path_details in self._parsed_dict.get("paths").items():
                for method, method_details in path_details.items():
                    if "deprecated" in method_details and method_details["deprecated"]:
                        continue
                    method_details["parameters"] = self._generate_path_parameters(
                        method_details
                    )
                    api_path_url = path_url if path_url.startswith(('http://', 'https://')) else self.base_url + path_url
                    open_api_path_models.append(
                        OpenAPIPathModel(
                            path_url=api_path_url,
                            method=method,
                            **method_details,
                        )
                    )

        self.paths = open_api_path_models

    def _get_reference_to_dict(self, reference: str):
        value = self._parsed_dict
        for key in reference.split("/")[1:]:
            if isinstance(value, dict):
                value = value.get(key)
        return value

    def _resolve_reference(self, data, visited: Optional[set] = None):
        """Recursively resolve references in the specification data."""
        if visited is None:
            visited = set()
        if isinstance(data, dict):
            if "$ref" in data:
                ref = data["$ref"]
                if ref in visited:
                    return data  # Avoid circular reference
                visited.add(ref)
                ref_data = self._get_reference_to_dict(ref)
                if ref_data is not None:
                    del data["$ref"]
                    data.update(ref_data)
            for key, value in data.items():
                data[key] = self._resolve_reference(value, visited)
            return data
        elif isinstance(data, list):
            return [self._resolve_reference(item, visited) for item in data]
        else:
            return data

    def _parse_components(self):
        if not self._parsed_dict.get("components"):
            return
        if self._parsed_dict["components"].get("schemas"):
            self.components = {}
            for schema_name, schema in self._parsed_dict["components"][
                "schemas"
            ].items():
                self.components[schema_name] = self._parse_component_schema(schema)

        if self._parsed_dict["components"].get("securitySchemes"):
            securitySchemas = []
            for name, securitySchema in self._parsed_dict["components"]["securitySchemes"].items():
                securitySchemas.append(
                    {
                        "name": name,
                        **securitySchema
                    }
                )
            self.security = securitySchemas

    def _parse_component_schema(self, schema, visited: Optional[set] = None):
        if visited is None:
            visited = set()

        if schema is None:
            return "Unknown"
        
        # If this schema is already being processed, return a placeholder to break the cycle
        schema_id = id(schema)
        if schema_id in visited:
            return schema
        
        visited.add(schema_id)

        if schema.get("$ref"):
            ref_schema = self._get_reference_to_dict(schema["$ref"])
            return self._parse_component_schema(ref_schema, visited)
        
        if schema.get("type") == "object":
            _schema = {}
            for property_name, property_value in schema.get("properties", {}).items():
                if property_value.get("readOnly"):
                    continue
                if property_value.get("$ref"):
                    _schema[property_name] = self._parse_component_schema(property_value, visited)
                else:
                    _schema[property_name] = property_value.get("type")
        elif schema.get("type") == "array":
            _schema = [self._parse_component_schema(schema.get("items"), visited)]
        else:
            _schema = schema.get("type")
        
        # Remove from visited to allow separate branches to process the same schema independently if needed
        visited.remove(schema_id)
        if _schema is None:
            return schema
        return _schema

    def parse_file(self, file_path: str):
        """Parses the openapi or swagger file

        Args:
            file_path (str): path of the file
        """
        if file_path:
            file_content = None
            with open(file_path, "r") as file:
                file_content = file.read()
            if file_path.endswith(".yaml") or file_path.endswith(".yml"):
                self._parsed_dict = yaml.safe_load(file_content)
            elif file_path.endswith(".json"):
                self._parsed_dict = json.loads(file_content)
            else:
                raise Exception("Invalid file type")
            self.parse_from_dict(data=self._parsed_dict)
        else:
            raise Exception("Invalid file path")

    def parse_from_dict(self, data: dict = None) -> None:
        if data:
            self._parsed_dict = data

        self._parse_version_type()
        self._parse_base_url()
        self._parse_components()
        self._parse_paths()

        self.open_api_schema = OpenAPISchema(
            version=self.version,
            base_url=self.base_url,
            paths=self.paths,
            tags=self.tags,
            security=self.security,
            components=self.components,
        )

    def get_actions(self, integration_type) -> List[OpenAPIAction]:
        actions = []
        for path in self.paths:
            parameters = []
            parameters.append(
                OpenAPIPathParams(**{
                    "name": "method",
                    "in": "method",
                    "type": 'str',
                    "required": True,
                    "description": "HTTP Method",
                    "values": path.method
                })
            )

            # Removing unnecessary and integrations credentials related parameters
            for parameter in path.parameters:
                if (
                    getattr(parameter, "in_", None) == "header"
                    and parameter.name.lower() == "authorization"
                ):
                    continue
                elif (
                    getattr(parameter, "in_", None) == "path"
                    and parameter.name == "base_url"
                ):
                    continue
                if (
                    getattr(parameter, "in_", None) == "body"
                    and not parameter.values
                    and parameter.example
                ):
                    parameter.values = parameter.example
                parameters.append(parameter)

            action_name = path.summary
            if not action_name:
                action_name = (path.method or "").upper() + " Action " + path.path_url.replace("/", " ").replace("base_url", "")
            
            action_name = re.sub(r"[^A-Za-z0-9\- ]", "", str(action_name))
            action_name = re.sub(r"\s+", " ", action_name).strip()
            
            actions.append(
                OpenAPIAction(
                    name=action_name,
                    description=path.description
                    if path.description
                    else path.summary,
                    code=path.path_url,
                    integration_type=integration_type,
                    parameters_definition=parameters,
                    header_details=self.security,
                )
            )
        return actions