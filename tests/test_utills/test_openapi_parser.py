import pytest
import json
from autobotAI_integrations.models import ConnectionInterfaces
from autobotAI_integrations.utils.open_api_parser import OpenApiParser
from autobotAI_integrations.open_api_schema import OpenAPISchema, OpenAPIAction
from autobotAI_integrations.integrations import integration_service_factory

@pytest.fixture
def sample_openapi_json():
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0"
        },
        "servers": [
            {"url": "https://api.example.com/v1"}
        ],
        "paths": {
            "/users": {
                "get": {
                    "summary": "Get users",
                    "operationId": "getUsers",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer"}
                        }
                    ]
                },
                "post": {
                    "summary": "Create user",
                    "operationId": "createUser",
                    "parameters": []
                }
            }
        }
    }

@pytest.fixture
def parser():
    return OpenApiParser()

def test_parse_file(tmp_path, sample_openapi_json, parser):
    # Create a temporary JSON file
    spec_file = tmp_path / "openapi.json"
    with open(spec_file, 'w') as f:
        json.dump(sample_openapi_json, f)
    
    parser.parse_file(str(spec_file))
    assert isinstance(parser.open_api_schema, OpenAPISchema)
    assert len(parser.open_api_schema.paths) > 0

def test_parse_from_dict(sample_openapi_json, parser):
    parser.parse_from_dict(sample_openapi_json)
    assert isinstance(parser.open_api_schema, OpenAPISchema)
    assert len(parser.open_api_schema.paths) > 0

def test_get_base_url(sample_openapi_json, parser):
    parser.parse_from_dict(sample_openapi_json)
    base_url = parser.base_url
    assert base_url == "https://api.example.com/v1"

def test_get_base_url_no_servers(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {}
    }
    parser.parse_from_dict(spec)
    base_url = parser.base_url
    assert base_url == "{base_url}"

def test_get_actions(sample_openapi_json, parser):
    parser.parse_from_dict(sample_openapi_json)
    actions = parser.get_actions("test_integration")
    
    assert isinstance(actions, list)
    assert len(actions) == 2  # get and post methods
    
    for action in actions:
        assert isinstance(action, OpenAPIAction)
        assert action.integration_type == "test_integration"
        assert action.executable_type == "rest_api"

def test_action_properties(sample_openapi_json, parser):
    parser.parse_from_dict(sample_openapi_json)
    actions = parser.get_actions("test_integration")
    # TODO

def test_parse_file_not_found(parser):
    with pytest.raises(FileNotFoundError):
        parser.parse_file("nonexistent.json")

@pytest.mark.parametrize("file_content,expected_error", [
    ("{invalid json}", json.JSONDecodeError),
    ("not even json", json.JSONDecodeError),
])
def test_parse_invalid_json(tmp_path, parser, file_content, expected_error):
    spec_file = tmp_path / "invalid.json"
    with open(spec_file, 'w') as f:
        f.write(file_content)
    
    with pytest.raises(expected_error):
        parser.parse_file(str(spec_file))

def test_complex_parameters(parser):
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/complex": {
                "post": {
                    "operationId": "complexOperation",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        },
                        {
                            "name": "filter",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "array", "items": {"type": "string"}}
                        },
                        {
                            "name": "X-API-Key",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ]
                }
            }
        }
    }
    
    parser.parse_from_dict(spec)
    actions = parser.get_actions("test_integration")
    
    action = actions[0]
    params = action.parameters_definition

    assert len(params) == 3 + 1 # method as param
    
    path_param = next(p for p in params if p.in_ == "path")
    assert path_param.name == "id"
    assert path_param.required is True
    
    query_param = next(p for p in params if p.in_ == "query")
    assert query_param.name == "filter"
    assert query_param.required is False
    
    header_param = next(p for p in params if p.in_ == "header")
    assert header_param.name == "X-API-Key"
    assert header_param.required is True

    method_param = next(p for p in params if p.in_ == "method")
    assert method_param.name == "method"
    assert method_param.required is True
    assert method_param.params_type == "str"
    assert method_param.values == "POST"

def test_existing_integration(parser):
    integrations = integration_service_factory.get_service_details()
    for integration in integrations:
        service_cls = integration_service_factory.get_service_cls(integration.get("name"))

        actions = service_cls.get_all_rest_api_actions()

        if actions:
            actions = [action.model_dump() for action in actions]
            # TODO