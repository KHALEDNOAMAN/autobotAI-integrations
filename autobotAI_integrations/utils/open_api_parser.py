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
        self.components: Optional[dict] = None
        self.open_api_schema: Optional[OpenAPISchema] = None

    def _parse_version_type(self):
        if self._parsed_dict.get("openapi"):
            self.version = "openapi {}".format(self._parsed_dict.get("openapi"))
        elif self._parsed_dict.get("swagger"):
            self.version = "swagger {}".format(self._parsed_dict.get("openapi"))
        else:
            self.version = "unknown"

    def _parse_base_url(self):
        if "servers" in self._parsed_dict:
            self.base_url = self._parsed_dict.get("servers")[0].get("url")
        elif "host" in self._parsed_dict:
            self.base_url = "https://" + self._parsed_dict.get("host")
        else:
            self.base_url = "{base_url}"

    def _parse_param_data_type(self, parameter: dict):
        """parses the data type of the parameter"""
        if "schema" in parameter and "type" in parameter["schema"]:
            return parameter["schema"]["type"]
        elif "type" in parameter:
            return parameter["type"]
        elif parameter.get('in', "query") == "path":
            return "string"

    def _parse_param_default(self, parameter: dict):
        """parses the data type of the parameter"""
        if "schema" in parameter and "default" in parameter["schema"]:
            return parameter["schema"]["default"]
        elif "default" in parameter:
            return parameter["default"]

    def _create_body_parameter(self, request_body: dict) -> dict:
        open_api_path_param = {
            "name": "body",
            "in": "body",
            "type": "object",
            "description": "Request body",
        }
        open_api_path_param["required"] = request_body.get("required", True)
        # Supports only json for now
        if request_body.get("content", {}).get("application/json"):
            open_api_path_param["type"] = "json"
            schema = request_body["content"]["application/json"].get("schema")
            if "$ref" in schema:
                open_api_path_param["example"] = self.components.get(
                    schema["$ref"].split("/")[-1]
                )
            elif "example" in schema:
                open_api_path_param["example"] = schema["example"]
        return OpenAPIPathParams(**open_api_path_param)

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
                    parameters_list.append(
                        OpenAPIPathParams(**{
                            "type": self._parse_param_data_type(parameter),
                            "values": self._parse_param_default(parameter),
                            **parameter,
                        })
                    )
                except Exception as e:
                    print(e)
                    continue
        if method_details.get("requestBody"):
            parameters_list.append(
                self._create_body_parameter(method_details["requestBody"])
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
                    open_api_path_models.append(
                        OpenAPIPathModel(
                            path_url=self.base_url + path_url,
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

    def _resolve_reference(self, data):
        if isinstance(data, dict):
            if "$ref" in data:
                ref_data = self._get_reference_to_dict(data["$ref"])
                del data["$ref"]
                data.update(ref_data)
            for k, val in data.items():
                data[k] = self._resolve_reference(val)
            return data
        elif isinstance(data, list):
            return [self._resolve_reference(item) for item in data]
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

    def _parse_component_schema(self, schema):

        if schema.get("type") == "object":
            _schema = {}
            for property_name, property_value in schema.get("properties", {}).items():
                if property_value.get("readOnly"):
                    continue
                if property_value.get("$ref"):
                    property_value = self._get_reference_to_dict(property_value["$ref"])
                    _schema[property_name] = self._parse_component_schema(
                        property_value
                    )
                else:
                    _schema[property_name] = property_value.get("type")
        elif schema.get("type") == "array":
            _schema = [self._parse_component_schema(schema.get("items"))]
        else:
            _schema = schema.get("type")
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
            # Adding Method parameter
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
                elif getattr(parameter, 'in_', None) == "path" and parameter.name == "base_url":
                    continue

                if getattr(parameter, "in_", None) == "body" and not parameter.values:
                    if parameter.example:
                        parameter.values = parameter.example
                parameters.append(parameter)

            actions.append(
                OpenAPIAction(
                    name=path.summary,
                    description=path.description,
                    code=path.path_url,
                    integration_type=integration_type,
                    parameters_definition=parameters,
                    header_details=self.security,
                )
            )
        return actions
