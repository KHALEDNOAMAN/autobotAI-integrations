from setuptools import setup, find_packages

setup(
    name="autobotAI_integrations",
    version="1.2.1",
    author="ShunyEka Systems Private Limited",
    author_email="hello@shunyeka.com",
    description="A python package that contains all the integrations for autobotAI",
    packages=find_packages(),
    install_requires=[
        # Base requirements
        "boto3>=1.40.0",
        "botocore>=1.40.0",
        "pydantic>=2.11.7",
        "PyYAML>=6.0.2",
        "pydash>=8.0.5",
        "requests>=2.32.4",
        "tenacity>=8.5.0",
        "PyJWT",
        "jsonpath-ng",
        "autobotai_library_addons @ git+https://github.com/shunyeka-spl/autobotai-library-addons.git",
    ],
    extras_require={
        "executable": [
            # Required during Python execution
            "google-cloud-storage>=3.2.0",
            "google-auth>=2.40.3",
            "azure-identity>=1.23.1",
            "azure-mgmt-resource>=24.0.0",
            "slack-sdk>=3.36.0",
            "snowflake-connector-python>=3.16.0",
            "opensearch-py>=3.0.0",
            "msgraph-sdk",  # Adding to reduce latency in msgraph
            "msgraph-beta-sdk",  # Adding to reduce latency in msgraph
        ],
        "full": [
            # Used only in backend (core) via API
            "boto3>=1.40.0",
            "botocore>=1.40.0",
            "pydantic>=2.11.7",
            "PyYAML>=6.0.2",
            "pydash>=8.0.5",
            "PyGithub>=2.7.0",
            "kubernetes>=33.1.0",
            "google-auth>=2.40.3",
            "azure-identity>=1.23.1",
            "python-dotenv>=1.1.1",
            "pymsteams>=0.2.5",
            "google-cloud-storage>=3.2.0",
            "azure-mgmt-resource>=24.0.0",
            "python-gitlab>=6.2.0",
            "openai>=1.98.0",
            "slack-sdk>=3.36.0",
            "ollama>=0.5.1",
            "jira>=3.10.5",
            "snowflake-connector-python>=3.16.0",
            "opensearch-py>=3.0.0",
            "langchain_aws>=0.2.30",
            "langchain_openai>=0.3.28",
            "pydantic-ai>=0.4.10",
            "llama-index",
            "llama-index-llms-openai",
            "llama-index-llms-bedrock",
            "llama-index-embeddings-openai",
            "llama-index-embeddings-bedrock",
        ],
    },
    package_data={
        "": [
            "integrations/*/inventory.json",
            "integrations/*/python_sdk_clients.yml",
            "integrations/*/compliance.json",
            "integrations/*/open_api.json",
            "integrations/*/mcp_servers.json",
        ]
    },
    classifiers=[
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.10",
    include_package_data=True,
)
