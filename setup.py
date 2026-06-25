from setuptools import find_packages, setup

setup(
    name="autobotAI_integrations",
    version="1.2.3",
    author="ShunyEka Systems Private Limited",
    author_email="hello@shunyeka.com",
    description="A python package that contains all the integrations for autobotAI",
    packages=find_packages(),
    install_requires=[
        # Base requirements
        "boto3>=1.43.31",
        "botocore>=1.40.61",
        "pydantic>=2.13.4",
        "PyYAML>=6.0.3",
        "pydash>=8.0.6",
        "requests>=2.34.2",
        "tenacity>=9.1.4",
        "setuptools>=82.0.1",
        "PyJWT>=2.13.0",
        "jsonpath-ng>=1.8.0",
        "autobotai_library_addons @ git+https://github.com/shunyeka-spl/autobotai-library-addons.git",
    ],
    extras_require={
        "executable": [
            # Required during Python execution
            "google-cloud-storage>=3.12.0",
            "google-auth>=2.55.0",
            "azure-identity>=1.25.3",
            "azure-mgmt-resource>=25.0.0",
            "slack-sdk>=3.42.0",
            "snowflake-connector-python>=4.6.0",
            "opensearch-py>=3.2.0",
            "msgraph-sdk>=1.52.0",  # Adding to reduce latency in msgraph
            "msgraph-beta-sdk",  # Adding to reduce latency in msgraph
            "ark-sdk-python",
        ],
        "full": [
            # Used only in backend (core) via API
            "boto3>=1.43.31",
            "botocore>=1.43.31",
            "pydantic>=2.13.4",
            "PyYAML>=6.0.3",
            "pydash>=8.0.6",
            "PyGithub>=2.9.1",
            "google-auth>=2.55.0",
            "azure-identity>=1.25.3",
            "python-dotenv>=1.2.2",
            "pymsteams>=0.2.5",
            "google-cloud-storage>=3.12.0",
            "azure-mgmt-resource>=25.0.0",
            "python-gitlab>=8.4.0",
            "openai>=2.42.0",
            "slack-sdk>=3.42.0",
            "ollama>=0.6.2",
            "jira>=3.10.5",
            "snowflake-connector-python>=4.6.0",
            "opensearch-py>=3.2.0",
            # Use the slim distribution with only the provider extras we
            # actually consume (BedrockConverseModel, OpenAIModel/
            # OpenAIResponsesModel — ollama runs through the OpenAI client,
            # claude runs through Bedrock — plus MCPServerStreamableHTTP).
            # The meta-package "pydantic-ai" bundles every extra including
            # [mistral], which pulls in the `mistralai` PyPI distribution
            # that PyPI has quarantined; we have no code using it.
            "pydantic-ai-slim[bedrock,openai,mcp]>=1.107.0",
            "llama-index>=0.14.18",
            "llama-index-llms-openai>=0.7.3",
            "llama-index-llms-bedrock>=0.5.0",
            "llama-index-embeddings-openai>=0.6.0",
            "llama-index-embeddings-bedrock>=0.8.0",
            "ark-sdk-python",
            "zscaler-sdk-python>=1.9.31",
        ],
    },
    package_data={
        "": [
            "integrations/*/inventory.json",
            "integrations/*/python_sdk_clients.yml",
            "integrations/*/compliance.json",
            "integrations/*/open_api.json",
            "integrations/*/mcp_servers.json",
            # Slack-bot install wizard renders this to the FE; without
            # listing it explicitly, find_packages() drops the YAML from
            # the installed wheel even with include_package_data=True.
            "integrations/*/manifest_template.yaml",
        ]
    },
    classifiers=[
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    include_package_data=True,
)
