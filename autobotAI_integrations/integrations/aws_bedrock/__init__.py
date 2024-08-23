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

    name: Optional[str] = "AWS Bedrock"
    category: Optional[str] = IntegrationCategory.AI.value
    description: Optional[str] = (
        "AWS Bedrock is a service that lets you use powerful AI models from various companies for your applications, all through one place."
    )

    def __init__(self, **kwargs):
        kwargs["activeRegions"] = [kwargs['region']]
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
        if self.integration.roleArn not in ["None", None]:
            boto3_helper = Boto3Helper(
                self.ctx, integration=self.integration.dump_all_data()
            )
            return boto3_helper.get_client(aws_client_name)
        else:
            return boto3.client(
                aws_client_name,
                aws_access_key_id=str(self.integration.access_key),
                aws_secret_access_key=str(self.integration.secret_key),
                aws_session_token=(
                    str(self.integration.session_token)
                    if self.integration.session_token not in [None, "None"]
                    else None
                ),
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
            # Fetching the model
            # models = [model['modelId'] for model in bedrock_client.list_foundation_models()['modelSummaries']]
            ec2_client = self._get_aws_client("ec2")
            regions = [
                region["RegionName"]
                for region in ec2_client.describe_regions()["Regions"]
            ]
            models = [
                "amazon.titan-text-express-v1",
                "meta.llama3-8b-instruct-v1:0",
                "meta.llama3-70b-instruct-v1:0",
                "mistral.mistral-7b-instruct-v0:2",
            ]
            return {
                "integration_id": self.integration.accountId,
                "models": models,
                "available_regions": list(set([self.integration.region, *regions])),
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

    @staticmethod
    def ai_prompt_python_template():
        return {
            "integration_type": "aws_bedrock",
            "ai_client": "bedrock-runtime",
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
            "code": """
import json
def executor(context):
    sample_json=\"\"\"
        {
                "name":"string"(name of the resources)
                "action_required": 'Boolean',
                "probability_score": 'int',
                "confidence_score": 'int',
                "reason": 'string',
                "fields_evaluated": ["field 1", "field 2", "field 3", "field 4", "field n"],
        }
        \"\"\"
    user_prompt=f\"\"\"Description for each field that provides context and reason of above json fields.{sample_json}.Instructions \n 1.action_required : this field should be either true or false. It indicate that whether to go with automation or not, based on the  probability_score and confidence_score to  decide whether its feasible to take action or not. \n 2. probability_score :  this field provides probability of the decision for provided prompt. this score should be from 1 - 100. higher score is better indicator to decide if user should automate remediation / response operation for provided data. lower score indicates that manual operations feasible since task mining and process mining from given data indicates that automation of such operations can be overkill or operations overhead.\n 3. confidence_score :  if you (generative AI) need to take assumption because either prompt or given context data do not have enough information or provided json context do not have enough details. this data should be between 0 to 100. lower number means that AI has taken lot of assumptions and whether to automate violation or not that decision may not be accurate. \n 4.reason : this value provides justification to human user, on what basis above provided confidence_score and probability_score calculated by generative AI. this will help human user to improve decision making. \n 5. this value provides field names in fetcher output context json fields. this should be field name only and NOT be individual value of each records.
    \n. Return JSON in {sample_json} format for each and every prompt JSON 
    \"\"\"
    
    client = context["clients"]["bedrock-runtime"]
    prompt = context["params"]["prompt"]
    model = context["params"]["model"]
    resources = json.loads(json.dumps(context["params"]["resources"], default=str))
    extra_prompt = f'Return JSON for using {user_prompt} for each and every object which is there in {resources} and make the JSON should be accurate and proper it should not be same for every resource using this  {prompt}'
    final_prompt=f\"\"\"
            <|begin_of_text|>
            <|start_header_id|>user<|end_header_id|>
             Ensure all property names are enclosed in double quotes, and the JSON structure is clean and syntactically correct. Handle multiline strings appropriately to avoid any JSON errors. otherwise my application will fail
            {extra_prompt}
            strick warning - Generate a multiple JSON for each and every prompt dont omit any of the resources otherwise my application will fail
            respond using JSON. without any additional text. Response must not have any additional or tilt symbol (```) or  text except the JSON as JSON array . 
    \"\"\"
    native_request = {
        "prompt": final_prompt,
        "max_gen_len": 2048,
    }
    
    request = json.dumps(native_request)
    
    response = client.invoke_model(modelId=model, body=request)
    model_output = json.loads(response['body'].read())
    
    print("response is ",json.loads(model_output['generation']))
    return json.loads(model_output['generation'])
""",
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
            "preview": True,
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
        if self.integration.roleArn not in ["None", None]:
            boto3_helper = Boto3Helper(
                self.ctx, integration=self.integration.model_dump()
            )
            return {
                "AWS_ACCESS_KEY_ID": boto3_helper.get_access_key(),
                "AWS_SECRET_ACCESS_KEY": boto3_helper.get_secret_key(),
                "AWS_SESSION_TOKEN": boto3_helper.get_session_token(),
            }
        else:
            creds = {
                "AWS_ACCESS_KEY_ID": str(self.integration.access_key),
                "AWS_SECRET_ACCESS_KEY": str(self.integration.secret_key),
            }
            if self.integration.session_token not in [None, "None"]:
                creds["AWS_SESSION_TOKEN"] = str(self.integration.session_token)
            return creds

    def _get_bedrock_model_request(self, model: str, prompt: str, max_tokens=2048, temperature=0.1, *args, **kwargs):
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
        else:
            native_request = {
                "prompt": prompt,
                "max_gen_len": int(max_tokens),
                "temperature": float(temperature),
            }
            request = json.dumps(native_request)
            return request

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
