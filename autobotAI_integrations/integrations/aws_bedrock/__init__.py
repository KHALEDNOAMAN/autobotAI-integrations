import traceback
from typing import Type, Union

import boto3, uuid, json
from botocore.exceptions import ClientError
from pydantic import Field

from autobotAI_integrations import AIBaseService, BaseService, list_of_unique_elements, PayloadTask, Param
from autobotAI_integrations.models import *
from autobotAI_integrations.utils.boto3_helper import Boto3Helper
from autobotAI_integrations.utils.logging_config import logger

class AWSBedrockIntegration(BaseSchema):
    region: str
    access_key: Optional[str] = Field(default=None, exclude=True)
    secret_key: Optional[str] = Field(default=None, exclude=True)
    session_token: Optional[str] = Field(default=None, exclude=True)
    account_id: Optional[str] = None
    roleArn: Optional[str] = None
    externalId: Optional[str] = None

    category: Optional[str] = IntegrationCategory.AI.value
    description: Optional[str] = (
        "AWS Bedrock is a service that lets you use powerful AI models from various companies for your applications, all through one place."
    )

    def __init__(self, **kwargs):
        kwargs["accountId"] = str(uuid.uuid4().hex)
        super().__init__(**kwargs)

    def use_dependency(self, dependency):
        self.roleArn = dependency["roleArn"]
        self.access_key: dependency["access_key"]
        self.secret_key: dependency["secret_key"]
        self.session_token: dependency["session_token"]
        self.externalId = dependency["externalId"]


class AWSBedrockService(AIBaseService):
    def __init__(self, ctx: dict, integration: Union[AWSBedrockIntegration, dict]):
        """
        Integration should have all the data regarding the integration
        """
        if not isinstance(integration, AWSBedrockIntegration):
            integration = AWSBedrockIntegration(**integration)
        super().__init__(ctx, integration)

    def _get_aws_client(self, aws_client_name: str):
        if self.integration.roleArn:
            boto3_helper = Boto3Helper(self.ctx, integration=self.integration.dump_all_data())
            return boto3_helper.get_client(aws_client_name)
        else:
            return boto3.client(
                aws_client_name,
                aws_access_key_id=self.integration.access_key,
                aws_secret_access_key=self.integration.secret_key,
                aws_session_token=self.integration.session_token
            )

    def _test_integration(self) -> dict:
        try:
            bedrock_client = self._get_aws_client('bedrock')
            models = [
                {**model, "name": model["modelId"]}
                for model in bedrock_client.list_foundation_models()["modelSummaries"]
            ]
            sts_client = self._get_aws_client("sts")
            identity_data = sts_client.get_caller_identity()
            account_id = str(identity_data['Account'])
            self.integration.account_id = account_id
            return {'success': True}
        except ClientError as e:
            logger.error(traceback.format_exc())
            return {'success': False, 'error': traceback.format_exc()}

    def get_integration_specific_details(self) -> dict:
        try:
            bedrock_client = self._get_aws_client("bedrock")
            ec2_client = self._get_aws_client('ec2')
            regions = [region['RegionName'] for region in  ec2_client.describe_regions()["Regions"]]
            # Fetching the model
            # models = [model['modelId'] for model in bedrock_client.list_foundation_models()['modelSummaries']]
            models = [
                "amazon.titan-text-express-v1",
                "meta.llama3-8b-instruct-v1:0",
                "meta.llama3-70b-instruct-v1:0",
                "mistral.mistral-7b-instruct-v0:2",
            ]
            return {
                "integration_id": self.integration.accountId,
                "models": models,
                "available_regions": regions
            }
        except Exception as e:
            logger.error(e)
            logger.debug(traceback.format_exc())
            return {
                "error": "Details can not be fetched"
            }

    @staticmethod
    def get_forms():
        return {
            "label": "AWS Bedrock",
            "type": "form",
            "children": [
                {
                    "label": "IAM Role Integration",
                    "type": "form",
                    "children": [
                        {
                            "name": "roleArn",
                            "type": "text",
                            "label": "IAM Role ARN",
                            "placeholder": "Enter IAM role ARN",
                            "required": True,
                        },
                        {
                            "name": "region",
                            "type": "select",
                            "label": "Region",
                            "placeholder": "Select Region",
                            "required": True,
                        },
                    ],
                }
            ],
        }

    @staticmethod
    def ai_prompt_python_template():
        return {
            "integration_type": "openai",
            "param_definitions": [
                {
                    "name": "prompt",
                    "type": "str",
                    "description": "The prompt to use for the AI model",
                    "required": True,
                },
                {
                    "name": "model",
                    "type": "str",
                    "description": "The model to use for the AI model",
                    "required": True,
                },
                {
                    "name": "resources",
                    "type": "list",
                    "description": "The resources to use for the AI model",
                    "required": True,
                },
            ],
            "code": """import json
import traceback
def executor(context):
    bedrock = context['clients']['bedrock-runtime']
    prompt = context['params']['prompt']
    # Using "meta.llama3-8b-instruct-v1:0" here, 
    # template may vary based on model
    model = context['params']['model']
    resources = json.loads(json.dumps(context['params']['resources'], default=str))
    prompts = [
        f\"""<|start_header_id|>user<|end_header_id|>
        For each Input dict provided, return a dict with attributes such as, 'name': str name of the resource, 'action_required': boolean that shows is the action advisable or not, 'probability_score': integer that shows the probability of the result being correct, 'confidence_score': integrer that shows the confidence in judgement, 'reason': string that mentions the reason for the judgement, 'fields_evaluated': list of fields that were evaluted for the judgement, the evaluation criterion given is {prompt}. The output should be valid parseable json, do not use any markup language at all, the returned message content should be json parsable. Wait till all data is provided before starting
        \"""
    ]
    for resource in resources:
        prompts.append(
            \"""<|start_header_id|>user<|end_header_id|>
            json.dumps(resource, default=str)
            \"""
        )
    prompts.append(
        \"""<|start_header_id|>user<|end_header_id|>
        All resources are provided, return the result for each resource in the same order.
        \"""
    )
    formatted_prompt = f\"""
<|begin_of_text|>
{"\n".join(prompts)}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
\"""
    native_request = {
        "prompt": formatted_prompt,
        "temperature": 0.5,
    }
    request = json.dumps(native_request)
    counter = 0
    while counter < 5:  # 4 Retries
        counter = counter + 1
        response = client.invoke_model(modelId=model_id, body=request)
        model_response = json.loads(response["body"].read())
        try:
            message_content =  model_response["generation"]
            if message_content:
                if "```json" in message_content:
                    message_content = message_content.split("```json")[1].split("```")[0]
                if len(json.loads(message_content)) == len(resources):
                    for idx, response in enumerate(json.loads(message_content)):
                        if not resources[idx].get("name") or (resources[idx].get("name") and response["name"] == resources[idx]["name"]):
                            resources[idx]["decision"] = response
                        else:
                            for resource in resources:
                                if response["name"] == resource["name"]:
                                    resource["decision"] = response
                    break
        except:
            print(type(model_response["generation"]), model_response["generation"])
            traceback.print_exc()
    print("Completed Evaluation with ", counter, "tries.")
    return resources""",
        }

    @staticmethod
    def get_schema() -> Type[BaseSchema]:
        return AWSBedrockIntegration

    @classmethod
    def get_details(cls):
        return {
            "clients": list_of_unique_elements(cls.get_all_python_sdk_clients()),
            "supported_executor": "ecs",
            "compliance_supported": False,
            "supported_interfaces": cls.supported_connection_interfaces(),
            "python_code_sample": cls.get_code_sample(),
        }

    def build_python_exec_combinations_hook(self, payload_task: PayloadTask,
                                            client_definitions: List[SDKClient]) -> list:
        return [
            {
                "metadata": {
                    "region": self.integration.region
                },
                "clients": {
                    "bedrock": boto3.client("bedrock", region_name=self.integration.region),
                    "bedrock-runtime": boto3.client("bedrock-runtime", region_name=self.integration.region)
                },
                "params": self.prepare_params(self.filer_combo_params(payload_task.params, self.integration.region)),
                "context": payload_task.context
            }
        ]

    def filer_combo_params(self, params: List[Param], region):
        filtered_params = []
        for param in params:
            if not param.filter_relevant_resources or not param.values:
                filtered_params.append(param)
            else:
                filtered_values = []
                for value in param.values:
                    if isinstance(value, dict):
                        if value.get("region") == region:
                            filtered_values.append(value)
                    else:
                        filtered_values.append(value)
                filtered_params.append({"name": param.name, "values": filtered_values})
        return filtered_params

    def generate_python_sdk_creds(self, requested_clients=None) -> SDKCreds:
        creds = self._temp_credentials()
        return SDKCreds(envs=creds)

    @staticmethod
    def supported_connection_interfaces():
        return [ConnectionInterfaces.PYTHON_SDK]

    def generate_cli_creds(self) -> CLICreds:
        raise NotImplementedError()

    def _temp_credentials(self):
        if self.integration.roleArn:
            boto3_helper = Boto3Helper(self.ctx, integration=self.integration.model_dump())
            return {
                "AWS_ACCESS_KEY_ID": boto3_helper.get_access_key(),
                "AWS_SECRET_ACCESS_KEY": boto3_helper.get_secret_key(),
                "AWS_SESSION_TOKEN": boto3_helper.get_session_token(),
            }
        else:
            return {
                "AWS_ACCESS_KEY_ID": self.integration.access_key,
                "AWS_SECRET_ACCESS_KEY": self.integration.secret_key,
                "AWS_SESSION_TOKEN": self.integration.session_token,
            }

    def _get_bedrock_model_request(self, model: str, prompt: str, max_tokens=512, temperature=0.5, *args, **kwargs):
        if model.startswith("amazon.titan-text"):
            native_request = {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": int(max_tokens),
                    "temperature": float(temperature),
                },
            }
            request = json.dumps(native_request)
            return request
        elif model.startswith("meta.llama3"):
            formatted_prompt = f"""
<|begin_of_text|>
{prompt}
<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>"""
            native_request = {
                "prompt": formatted_prompt,
                "max_gen_len": int(max_tokens),
                "temperature": float(temperature),
            }
            request = json.dumps(native_request)
            return request
        elif model.startswith("mistral.mistral") or model.startswith("meta.llama2"):
            formatted_prompt = f"<s>[INST] {prompt} [/INST]"
            native_request = {
                "prompt": formatted_prompt,
                "max_gen_len": int(max_tokens),
                "temperature": float(temperature),
            }
            request = json.dumps(native_request)
            return request
        else:
            raise Exception(f"Model {model} not found in generate request")

    def prompt_executor(self, model=None, prompt=None, options: dict = {}):
        if not model or not prompt:
            raise Exception("Model and prompt are required")
        request = self._get_bedrock_model_request(model, prompt, **options)
        client = self._get_aws_client('bedrock-runtime')
        try:
            # Invoke the model with the request.
            response = client.invoke_model(modelId=model, body=request)

        except (ClientError, Exception) as e:
            print(f"ERROR: Can't invoke '{model}'. Reason: {e}")
            exit(1)

        # Decode the response body.
        model_response = json.loads(response["body"].read())
        return model_response
