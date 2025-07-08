from datetime import datetime, timedelta
from time import sleep
import boto3
from botocore.exceptions import ClientError
from autobotAI_integrations.utils import fromisoformat
import os

app_env = os.environ.get('APP_ENV', 'local')
run_env = os.environ.get('RUN_ENV', app_env)

regions = [
    {'id': 'us-east-1', 'name': 'Virginia'},
    {'id': 'ap-south-1', 'name': 'Mumbai'},
    {'id': 'ap-southeast-1', 'name': 'Singapore'},
    {'id': 'us-east-2', 'name': 'Ohio'},
    {'id': 'us-west-1', 'name': 'California'},
    {'id': 'us-west-2', 'name': 'Oregon'},
    {'id': 'ca-central-1', 'name': 'Canada'},
    {'id': 'eu-west-1', 'name': 'Ireland'},
    {'id': 'eu-central-1', 'name': 'Frankfurt'},
    {'id': 'eu-west-2', 'name': 'London'},
    {'id': 'ap-northeast-1', 'name': 'Tokyo'},
    {'id': 'ap-northeast-2', 'name': 'Seoul'},
    # {'id': 'ap-northeast-3', 'name': 'Osaka-Local'},
    {'id': 'ap-southeast-2', 'name': 'Sydney'},
    {'id': 'eu-west-3', 'name': 'Paris'},
    {'id': 'sa-east-1', 'name': 'Sao Paulo(South America)'},
    # {'id': 'cn-north-1', 'name': 'Beijing(China)'},
    # {'id': 'cn-northwest-1', 'name': 'China(Ningxia)'},
    # {'id': 'ap-east-1', 'name': 'Asia Pacific (Hong Kong)'},
    {'id': 'eu-north-1', 'name': 'EU (Stockholm)'},
    # {'id': 'me-south-1', 'name': 'Middle East (Bahrain)'},
]


class Boto3Helper:

    def __init__(self, rctx, autobot_resources: bool = False, integration=None):
        self.ctx = rctx
        self.autobot_resources = autobot_resources
        self.csp = integration
        if not autobot_resources:
            self.refresh_sts_creds()

    @staticmethod
    def get_autobot_ai_region():
        autobot_region = os.environ.get('AUTOBOT_REGION', os.environ.get('AWS_REGION', 'us-east-1'))
        return autobot_region

    def get_aws_resource(self, resource_type: str, region_name: str = None):
        if not region_name:
            region_name = self.get_autobot_ai_region()
        session = self.get_session()
        resource = session.resource(resource_type, region_name=region_name)
        return resource

    def get_session(self):
        self.ctx.logger.debug("get_session called for %s", str(self.autobot_resources))
        session = None
        if session is None:
            if not self.autobot_resources or run_env == "local":
                session = boto3.Session(
                    aws_access_key_id=self.get_access_key(),
                    aws_secret_access_key=self.get_secret_key(),
                    region_name=self.get_autobot_ai_region(),
                    aws_session_token=self.get_session_token()
                )
            else:
                session = boto3.Session(region_name=self.get_autobot_ai_region())
        return session

    def get_client(self, resource, region_name=None, endpoint_url=None):
        if region_name is None:
            region_name = self.get_autobot_ai_region()
        self.ctx.logger.debug("get_client called for resource=%s, region=%s, autobot_resource=%s", resource,
                              region_name, str(self.autobot_resources))
        client = None
        region = region_name if region_name else self.get_autobot_ai_region()
        if not self.autobot_resources or run_env == "local":
            if resource == "s3":
                client = boto3.client(resource,
                                      endpoint_url=f"https://s3.{region}.amazonaws.com",
                                      aws_access_key_id=self.get_access_key(),
                                      aws_secret_access_key=self.get_secret_key(),
                                      region_name=region_name if region_name else self.get_autobot_ai_region(),
                                      aws_session_token=self.get_session_token()
                                      )
            else:
                client = boto3.client(resource,
                                      endpoint_url=endpoint_url,
                                      aws_access_key_id=self.get_access_key(),
                                      aws_secret_access_key=self.get_secret_key(),
                                      region_name=region_name if region_name else self.get_autobot_ai_region(),
                                      aws_session_token=self.get_session_token()
                                      )
        else:
            if resource == "s3":
                client = boto3.client(resource, region_name=region, endpoint_url=f"https://s3.{region}.amazonaws.com")
            else:
                client = boto3.client(resource, region_name=region, endpoint_url=endpoint_url)
        return client

    def get_dynamo_db_table(self, table_name, live=False):
        self.ctx.logger.debug("Called with table=%s, autobot_resources=%s", table_name, str(self.autobot_resources))
        dynamodb = self.get_aws_resource('dynamodb')
        table_name = app_env + "_" + table_name
        # workspace_name = os.environ.get("SUBDOMAIN", None)
        # if workspace_name and workspace_name not in ["live", "backend", "trendrpa"]:
        #     table_name = workspace_name + "_" + table_name
        table = dynamodb.Table(table_name)
        self.ctx.logger.debug("Returning dynamo table")
        return table

    def get_access_key(self):
        self.ctx.logger.debug("Called with autobot_resources=%s", str(self.autobot_resources))
        if self.autobot_resources:
            return self.ctx.config["ACCESS_KEY"]
        else:
            self.refresh_sts_creds()
            return self.credentials["AccessKeyId"]

    def refresh_sts_creds(self):
        while True:
            try:
                arn = self.csp.get('roleArn', None)
                if arn and arn != 'None':
                    sts_client = self.ctx.autobot_aws_context.boto3_helper.get_client('sts',
                                                                                        region_name='us-east-1',
                                                                                        endpoint_url="https://sts.us-east-1.amazonaws.com"
                                                                                      )
                    assumerole = sts_client.assume_role(
                        RoleArn=self.csp['roleArn'],
                        RoleSessionName=arn[13:25] + arn[31:],
                        ExternalId=self.csp['externalId'],
                        DurationSeconds=3600
                    )

                else:
                    sts_client = boto3.client(
                        'sts',
                        aws_access_key_id=self.csp['access_key'],
                        aws_secret_access_key=self.csp['secret_key'],
                        aws_session_token=self.csp["session_token"] or None,
                        region_name='us-east-1',
                        endpoint_url="https://sts.us-east-1.amazonaws.com"
                    )

                    # Get temporary credentials
                    assumerole = sts_client.get_session_token()
                self.credentials = assumerole['Credentials']
                self.credentials["stsCredsGeneratedOn"] = datetime.now().isoformat()
                self.ctx.logger.info(f" [Integrations] Using Access Key with ID: {self.credentials['AccessKeyId']}, Session Token: {self.credentials['SessionToken']} and Expiration: {self.credentials['Expiration']}")
            except ClientError as e:
                if "ThrottlingException" in str(e):
                    sleep(3)
                    continue
                raise
            return


    def get_secret_key(self):
        self.ctx.logger.debug("Called with autobot_resources=%s", str(self.autobot_resources))
        if self.autobot_resources:
            return self.ctx.config["SECRET_KEY"]
        else:
            return self.credentials["SecretAccessKey"]

    def get_session_token(self):
        self.ctx.logger.debug("Called with autobot_resources=%s", str(self.autobot_resources))
        if self.autobot_resources:
            return None
        else:
            return self.credentials["SessionToken"]

    def get_all_regions(self):
        client = self.get_client("ec2")
        return [region['RegionName'] for region in client.describe_regions()['Regions']]
