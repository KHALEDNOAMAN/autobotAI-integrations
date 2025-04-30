import importlib
import shutil
import os
import subprocess
import sys
import inspect
import platform
import json
from copy import deepcopy
import traceback
from enum import Enum
from os import path
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable, Union

import requests
import yaml
from pydantic import BaseModel
from autobotAI_integrations.integration_schema import ConnectionTypes, IntegrationSchema, IntegrationStates
from autobotAI_integrations.models import *
from autobotAI_integrations.open_api_schema import OpenAPIAction
from autobotAI_integrations.payload_schema import PayloadTask, Payload, Param
from autobotAI_integrations.utils.logging_config import logger
from autobotAI_integrations.utils import (
    list_of_unique_elements,
    load_mod_from_string,
    run_mod_func,
    oscf_based_steampipe_json,
    transform_steampipe_compliance_resources,
    change_keys,
    transform_inventory_resources,
    open_api_parser,
    get_restapi_validated_params,
)
from autobotAI_integrations.utils.security_measures import SecurityError


class BaseService:

    def __init__(self, ctx: dict, integration: BaseSchema):
        """
        Integration should have all the data regarding the integration
        """
        self.integration = integration
        self.ctx = ctx

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.PYTHON_SDK]

    @staticmethod
    def get_forms():
        """
        Returns a list of Forms Represented in JSON format for UI
        - success: bool
        - error: str
        """
        raise NotImplementedError()

    def _test_integration(self) -> dict:
        """
        Returns a dictionary with the following keys:
        - success: bool
        - error: str
        """
        raise NotImplementedError()

    def is_active(self):
        result = self._test_integration()
        if result["success"]:
            self.integration.integrationState = IntegrationStates.ACTIVE
        else:
            self.integration.integrationState = IntegrationStates.INACTIVE
            self.on_test_integration_failure()
        logger.info(f"Integration accountId: {self.integration.accountId} And State: {self.integration.integrationState}")
        return result

    def on_test_integration_failure(self):
        pass

    def get_integration_specific_details(self) -> dict:
        return {}

    @classmethod
    def get_integration_type(cls):
        system_os = platform.system()
        if system_os == "Windows":
            sep = "\\"
        else:
            sep = "/"
        integration_type = os.path.dirname(inspect.getfile(cls)).split(sep)[-1]
        return integration_type

    @classmethod
    def get_code_sample(cls):
        base_path = os.path.dirname(inspect.getfile(cls))
        try:
            code_file = open(path.join(base_path, "code_sample.py"))
            code = code_file.read()
        except FileNotFoundError:
            code = """# import your modules here...
# Don't import client related modules

def executor(context):
    params = context["params"]    
    clients = context["clients"]
    
    # <> Your Code goes here.
    
    # Always return a list
    return []
"""
        return code

    @classmethod
    def load_compliance_data(cls):
        base_path = os.path.dirname(inspect.getfile(cls))
        try:
            clients_data = open(path.join(base_path, "compliance.json"))
            data = json.loads(clients_data.read())
            integration_type = cls.get_integration_type()
            return data[integration_type]["benchmarks"]
        except FileNotFoundError:
            return []

    @classmethod
    def get_compliance_meta(cls, compliance_data):
        benchmarks = cls.load_compliance_data()
        compliance_details = []
        for compliance in benchmarks:
            if compliance["name"] in compliance_data:
                compliance_details.append(compliance)
        return compliance_details

    @classmethod
    def get_compliance_meta_names(cls):
        benchmarks = cls.load_compliance_data()
        compliance_names = []
        for compliance in benchmarks:
            compliance_names.append(compliance['name'])
        return compliance_names

    @classmethod
    def get_steampipe_tables(cls) -> List[dict]:
        if ConnectionInterfaces.STEAMPIPE not in cls.supported_connection_interfaces():
            return []
        base_path = os.path.dirname(inspect.getfile(cls))
        integration_type = cls.get_integration_type()
        with open(path.join(base_path, 'inventory.json')) as f:
            clients_data = f.read()
            data = json.loads(clients_data)
        return data[integration_type]

    @classmethod
    def get_all_python_sdk_clients(cls,integration_type=None):
        if ConnectionInterfaces.PYTHON_SDK not in cls.supported_connection_interfaces():
            return []
        base_path = os.path.dirname(inspect.getfile(cls))
        if integration_type!=None:
            base_path = base_path + f'/integrations/{integration_type}'
            print("base path is ",base_path)
        with open(path.join(base_path, ".", 'python_sdk_clients.yml')) as f:
            return yaml.safe_load(f)

    @classmethod
    def get_all_rest_api_actions(cls) -> List[OpenAPIAction]:
        if ConnectionInterfaces.REST_API not in cls.supported_connection_interfaces():
            return []
        base_path = os.path.dirname(inspect.getfile(cls))
        parser = open_api_parser.OpenApiParser()
        open_api_actions = []
        if not os.path.exists(os.path.join(base_path, "open_api.json")):
            logger.info(f"File open_api.json not found for {cls.get_integration_type()}")
            return open_api_actions
        try:
            parser.parse_file(os.path.join(base_path, "open_api.json"))
            open_api_actions = parser.get_actions(cls.get_integration_type())
        except Exception as e:
            logger.exception(f"Error occurred while parsing open api file: {e}")
        finally:
            return open_api_actions

    @staticmethod
    def get_schema() -> BaseSchema:
        raise NotImplementedError()

    @classmethod
    def get_details(cls):
        try:
            return {
                "python_code_sample": cls.get_code_sample(),
                "fetcher_supported": ["code", "no_code"],
                "listener_supported": False,
                "supported_interfaces": cls.supported_connection_interfaces(),
                "supported_execution_types": cls.supported_connection_interfaces(),
                "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
                "supported_executor": "ecs",
                "compliance_supported": False
            }
        except Exception as e:
            logger.exception(f"Error occurred while fetching details for {cls.__name__}: {e}")
            return {}

    def generate_steampipe_creds(self) -> SteampipeCreds:
        raise NotImplementedError()

    def generate_rest_api_creds(self) -> RestAPICreds:
        raise NotImplementedError()

    def generate_python_sdk_creds(self) -> SDKCreds:
        raise NotImplementedError()

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        raise NotImplementedError()

    def build_python_exec_combinations(self, payload_task: PayloadTask):
        client_definitions = self.find_client_definitions(payload_task.clients)
        current_installation = set()

        # Check if running in a frozen state (e.g., bundled with PyInstaller for linux integration).
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # attempt to locate the system's Python executable.
            python_exec = shutil.which("python3") or shutil.which("python")
            exec_mode = "frozen"
            if not python_exec:
                raise RuntimeError("Python executable not found on the system.")
        else:
            python_exec = sys.executable
            exec_mode = "source"  

        # Installation dir by 'idx' to prevent packages co-interference
        for idx, client in enumerate(client_definitions):
            if client.pip_package_names and not set(client.pip_package_names).issubset(current_installation):
                logger.info(f"Installing {client.pip_package_names} with python_exec {python_exec} and exec_mode {exec_mode}")
                try:
                    # prevents the reinstallation of the same package for different tasks
                    if exec_mode == "frozen":
                        subprocess.check_call(
                            [
                                python_exec, "-m", "pip", "show", " ".join(client.pip_package_names)
                            ],
                            env={**os.environ, "PYTHONPATH": f"/tmp/{idx}/"}
                        )
                        sys.path.insert(1,  f"/tmp/{idx}/") 
                    else:
                        subprocess.check_call(
                            [
                                "pip", "show", " ".join(client.pip_package_names)
                            ],
                        )       
                    logger.info(f"Requirements already installed for {client.pip_package_names}")
                except subprocess.CalledProcessError:
                    subprocess.check_call(
                        [
                             python_exec, "-m",
                            "pip", "install", " ".join(client.pip_package_names),
                            "-t", f"/tmp/{idx}/", "--no-cache-dir", "--upgrade"
                        ]
                    )
                    sys.path.insert(1,  f"/tmp/{idx}/")
                    current_installation.update(client.pip_package_names)
                except Exception as e:
                    logger.exception(f"Error occurred while installing packages: {e}")

        return self.build_python_exec_combinations_hook(payload_task, client_definitions)

    def find_client_definitions(self, client_name_list,integration_type=None) -> List[SDKClient]:
        all_clients = self.get_all_python_sdk_clients(integration_type)
        client_details = []
        for client in client_name_list:
            client_def = next(item for item in all_clients if item["name"] == client)
            client_details.append(SDKClient(**client_def))
        return client_details

    def python_sdk_processor(self, payload_task: PayloadTask) -> (List[Dict[str, Any]], List[str]):  # type: ignore                
        if payload_task.creds and payload_task.creds.envs:
            for key, value in payload_task.creds.envs.items():
                if key and value:
                    os.environ[key] = value

        results = []
        errors = []
        combinations = self.build_python_exec_combinations(payload_task)
        for combo in combinations:
            try:
                result, error = self._execute_python_sdk_code(combo, payload_task)
                results.extend(result)
                if error:
                    errors.append(
                        {
                            "message": error,
                            "other_details": {
                                "execution_details": payload_task.context.execution_details
                            },
                        }
                    )
            except:
                errors.append({
                    "message": traceback.format_exc(chain=True, limit=1),
                    "other_details": {
                        "execution_details": payload_task.context.execution_details
                    }
                })

        return results, errors

    @classmethod
    def prepare_params(cls, params: List[Param]):
        flattened_params = {}
        for param in params:
            if not isinstance(param, Param) and isinstance(param, dict):
                flattened_params[param["name"]] = param["values"]
            else:
                flattened_params[param.name] = param.values
        return flattened_params

    @classmethod
    def _execute_python_sdk_code(cls, combination, payload_task: PayloadTask):
        mod = None
        try:
            mod = load_mod_from_string(
                payload_task.executable,
                payload_task.externalExecutable,
                connection_type=payload_task.context.integration.connection_type,
            )
        except SecurityError as e:
            return [], str(e)
        context = {**payload_task.context.model_dump(), **combination}
        result, error = run_mod_func(mod.executor, context=context)
        resources = []
        if result:
            default_data = {
                "user_id": payload_task.context.execution_details.caller.user_id,
                "root_user_id": payload_task.context.execution_details.caller.root_user_id
            }
            if payload_task.context.integration.category not in [IntegrationCategory.AI.value] and payload_task.context.integration.cspName not in ["python"]:
                default_data["integration_id"] = payload_task.context.integration.accountId
                default_data["integration_type"] = payload_task.context.integration.cspName
            if not isinstance(result, list):
                result = [result]
            for r in result:
                if isinstance(r, dict):
                    resources.append(
                        {
                            **r,
                            **combination.get("metadata", {}),
                            **default_data
                        }
                    )
                else:
                    resources.append(
                        {"result": r, **combination.get("metadata", {}), **default_data}
                    )
        resources = change_keys(resources)
        return resources, error

    def _get_steampipe_config_path(self, plugin_name):
        home_dir = Path.home()
        config_path = os.path.join(
            home_dir, ".steampipe/config/", "{}.spc".format(plugin_name.split("/")[-1])
        )
        return config_path

    def set_steampipe_spc_config(self, config_str, plugin_name):
        config_path = self._get_steampipe_config_path(plugin_name)
        logger.info(f"Setting {plugin_name}.spc file to PATH: {config_path}")
        logger.info(f"SPC Config {plugin_name}.spc file is: {config_str}")
        with open(config_path, 'w') as f:
            f.write(config_str)

    def clear_steampipe_spc_config(self, plugin_name):
        config_path = self._get_steampipe_config_path(plugin_name)
        try:
            os.remove(config_path)
            logger.info("file removed successfully!")
        except FileNotFoundError:
            logger.info("File Not Found on path {}".format(config_path))

    # Handle Compliance Executions
    def _execute_steampipe_compliance(self, payload_task: PayloadTask):
        mods_dir = "/tmp/mods/compliances"
        if not os.path.exists(mods_dir):
            os.makedirs(mods_dir)

        path = os.path.join(
            mods_dir,
            "steampipe-mod-{}-compliance".format(payload_task.creds.plugin_name),
        )
        if os.path.exists(path):
            logger.info("Mod already exists, Trying to fetch latest version.")
            subprocess.run(
                ["git", "pull"],
                cwd=path
            )
        else:
            subprocess.run(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    f"https://github.com/turbot/steampipe-mod-{payload_task.creds.plugin_name}-compliance.git",
                ],
                cwd=mods_dir,
            )

        # Set Env Variables for creds.
        env = os.environ.copy()
        if payload_task.creds and payload_task.creds.envs:
            for key, value in payload_task.creds.envs.items():
                if key and value:
                    env[key] = value    

        logger.info("Starting Steampipe Service...")    
        subprocess.run(["steampipe", "service", "start"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

        logger.info(f"Running Benchmark...") 
        process = subprocess.run(
            ["powerpipe", "benchmark", "run", "{}".format(payload_task.executable), "--output", "json"],
            cwd=path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )

        logger.info("Stopping Steampipe Service...")  
        subprocess.run(["steampipe", "service", "stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

        return process

    def execute_steampipe_task(self, payload_task: PayloadTask):
        logger.info("Running Steampipe Task")

        logger.info(f"Installing the plugin {payload_task.creds.plugin_name}")
        subprocess.run(
            ["steampipe", "plugin", "install", payload_task.creds.plugin_name]
        )

        logger.info(f"Updating the plugin {payload_task.creds.plugin_name}")
        subprocess.run(
            ["steampipe", "plugin", "update", payload_task.creds.plugin_name]
        )
        self.set_steampipe_spc_config(
            config_str=payload_task.creds.config,
            plugin_name=payload_task.creds.plugin_name
        )
        execution_mode = None

        logger.debug("Checking for Query type")
        if payload_task.executable.startswith(f"{payload_task.creds.plugin_name}_compliance"):
            execution_mode = "compliance"
        elif payload_task.executable.lower().startswith("select"):
            execution_mode = "query"
        else:
            raise ValueError("Execution mode is not supported.")

        if execution_mode == "compliance":
            logger.info(f"Running compliance benchmark: '{payload_task.executable}'")
            process = self._execute_steampipe_compliance(payload_task)

        else:
            logger.info(f"Running query: '{payload_task.executable}'")
            process = subprocess.run(
                ["/usr/local/bin/steampipe", "query", "{}".format(payload_task.executable), "--output", "json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, **payload_task.creds.envs}
            )

        self.clear_steampipe_spc_config(plugin_name=payload_task.creds.plugin_name)

        stdout = process.stdout.decode("utf-8")
        error_str = process.stderr.decode("utf-8")        
        logger.error(f"Possible error running the steampipe query: {error_str}")
        stderr = []
        # Get the Error if query fails
        if error_str:
            try:
                stderr.append(
                    {
                        "message": str(error_str),
                        "other_details": {
                            "execution_details": payload_task.context.execution_details
                        },
                    }
                )
            except BaseException as e:
                logger.exception(e)

        try:
            stdout = json.loads(stdout)
        except json.decoder.JSONDecodeError:
            if stdout == "None" or not stdout or stdout == "null":
                stdout = []
        except BaseException as e:
            stderr = [{
                "message": traceback.format_exc(),
                "other_details": {
                    "non_json_output": stdout,
                    "stderr": error_str
                }
            }]

        logger.info(f"Transforming Output for {execution_mode}")
        logger.debug(f"Stdout: {stdout}")
        if execution_mode == "compliance":
            stdout = transform_steampipe_compliance_resources(stdout)
            stdout = change_keys(stdout)
            stdout = oscf_based_steampipe_json(
                stdout,
                integration_type=payload_task.creds.connection_name,
                integration_id=payload_task.context.integration.accountId,
                query=payload_task.executable,
            )
        # Transforming the output
        elif isinstance(stdout, dict) and "rows" in stdout:
            stdout = transform_inventory_resources(stdout, payload_task)

        # Covering Edge Cases
        if not isinstance(stdout, list):
            logger.error(f"Failed Output as List: {stdout}")
            stdout = list(stdout)

        logger.debug(f"Transformed Output: {stdout}")
        return stdout, stderr

    def rest_api_processor(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        timeout: int = 10,
        verify_ssl: bool = True,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        logger.info(f"Making {method} request to {url}")
        logger.debug(f"Headers: {headers}, Params: {params}, JSON: {json_data}")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers if headers else None,
                params=params if params else None,
                json=json_data if json_data else None,
                timeout=timeout,
                verify=verify_ssl,
            )

            logger.info(f"Response Status Code: {response.status_code}")
            logger.debug(f"Response Text: {response.text}")

            # Check for HTTP errors
            response.raise_for_status()

            # Handle no content responses (204)
            if response.status_code == 204:
                return {}

            # If response is empty but successful
            if not response.content:
                return {}

            content_type = response.headers.get("Content-Type", "").lower()

            # Check if the response content is JSON (more flexible check)
            if "application/json" in content_type:
                try:
                    return response.json()
                except json.decoder.JSONDecodeError:
                    logger.error("Failed to decode JSON response")
                    return {
                        "abAI-client-error": "Invalid JSON response",
                        "text": response.text,
                    }
                except ValueError:
                    logger.error("Unexpected JSON structure")
                    return {
                        "abAI-client-error": "Unexpected JSON structure",
                        "text": response.text,
                    }
            else:
                # Handle non-JSON responses
                try:
                    # Try to parse as JSON even if content-type is not JSON
                    # (some APIs might send incorrect content-type)
                    if response.text and response.text.strip():
                        try:
                            return response.json()
                        except json.decoder.JSONDecodeError:
                            pass

                    # Handle empty or null responses
                    if not response.text or response.text.strip() in ["None", "null"]:
                        return {}

                    # If it's not JSON and not empty, return as text
                    return {"content": response.text, "content_type": content_type}

                except Exception as e:
                    logger.error(f"Error processing response: {str(e)}")
                    return {
                        "abAI-client-error": "Error processing response",
                        "text": response.text,
                    }

        except requests.exceptions.Timeout:
            logger.error("Request timed out")
            return {"abAI-client-error": "Request timed out"}

        except requests.exceptions.ConnectionError:
            logger.error("Connection error occurred")
            return {"abAI-client-error": "Connection error"}

        except requests.exceptions.TooManyRedirects:
            logger.error("Too many redirects")
            return {"abAI-client-error": "Too many redirects"}

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {"abAI-client-error": f"Request failed: {e}"}

    def execute_rest_api_task(self, payload_task: PayloadTask):
        logger.info("Running Rest API Task")
        results = []
        errors = []
        try:
            logger.info("Validating Rest API parameters...")
            params = get_restapi_validated_params(payload_task.params)

            logger.info("Creating request url..")
            request_url = payload_task.executable.format(
                base_url=payload_task.creds.base_url.strip("/"),
                # Filling path params,
                **params.get("path_parameters", {}),
            )
            logger.info(f"Request URL: {request_url}")

            logger.info("Making request..")
            response = self.rest_api_processor(
                url=request_url,
                method=params.get("method", "GET"),
                headers={
                    **params.get("headers", {}),
                    "Content-Type": "application/json",
                    **payload_task.creds.headers,
                },
                params={
                    **payload_task.creds.query_params,
                    **params.get("query_parameters", None),
                },
                json_data=params.get("json_data", None),
                timeout=params.get("timeout", 10),
                verify_ssl=payload_task.creds.verify_ssl,
            )
            logger.debug(f"Response: {response}")

            # In the response handling section:
            if isinstance(response, dict) and not response:
                response = {
                    "status": "success",
                    "message": "Operation completed successfully",
                }

            if isinstance(response, dict) and response.get("abAI-client-error"):
                errors.append(
                    {
                        "message": str(response["abAI-client-error"])
                        + " "
                        + str(response.get("text", "")),
                        "other_details": {
                            "execution_details": payload_task.context.execution_details
                        },
                    }
                )
                return results, errors

            # Transforming results
            if not isinstance(response, list):
                response = [response]
            
            response = change_keys(response)
            
            for row in response:
                if not isinstance(row, dict):
                    row = {"result": row}
                results.append(
                    {
                        **row,
                        "integration_id": payload_task.context.integration.accountId,
                        "integration_type": payload_task.context.integration.cspName,
                        "user_id": payload_task.context.execution_details.caller.user_id,
                        "root_user_id": payload_task.context.execution_details.caller.root_user_id,
                    }
                )
        except Exception as e:
            logger.exception(str(e))
            errors.append(
                {
                    "message": traceback.format_exc(chain=True, limit=1),
                    "other_details": {
                        "execution_details": payload_task.context.execution_details
                    },
                }
            )
        return results, errors


class AIBaseService(BaseService):
    @staticmethod
    def ai_prompt_python_template():
        raise NotImplementedError()

    def langchain_authenticator(self,model):
        raise NotImplementedError()

    def prompt_executor(self, model=None, prompt=None, options: dict = {}, messages: List[Dict[str, Any]] = []):
        raise NotImplementedError()
    
    def get_pydantic_agent(self, model: str, tools, system_prompt: str, options: dict = {}):
        raise NotImplementedError()
    
    def load_embedding_model(self, model_name: str):
        """
        Returns Langchaain Embedding model object and model dimensions as tuple
        """
        raise NotImplementedError()
