from setuptools import setup, find_packages

setup(
    name="autobotAI_integrations",
    version="1.2.0",
    author="ShunyEka Systems Private Limited",
    author_email="hello@shunyeka.com",
    description="A python package that contains all the integrations for autobotAI",
    packages=find_packages(),
    install_requires=[
        # Base requirements
        "boto3",
        "botocore",
        "pydantic",
        "PyYAML",
        "pydash",
        "requests",
    ],
    extras_require={
        "executable": [
            # Put your dependency here if it is required during python execution
            "google-cloud-storage",
            "google-auth",
            "azure-identity",
            "azure-mgmt-resource",
            "slack-sdk",
            "snowflake-connector-python",
            "opensearch-py",
        ],
        "full": [
            # Put you dependency here if it is only used in backend (core) through api
            "boto3",
            "botocore",
            "pydantic",
            "PyYAML",
            "pydash",
            "PyGithub",
            "kubernetes",
            "google-auth",
            "azure-identity",
            "python-dotenv",
            "pymsteams",
            "google-cloud-storage",
            "azure-mgmt-resource",
            "python-gitlab",
            "openai",
            "slack-sdk",
            "ollama",
            "jira",
            "snowflake-connector-python",
            "opensearch-py",
            "langchain_aws==0.2.23",
            "python-jose[cryptography]==3.4.0",
            "langchain_openai>=0.2.14",
            "pydantic-ai>=0.0.36",
            "llama-index-core==0.12.37",
            "llama-index-llms-openai==0.3.42",
            "llama-index-llms-bedrock-converse==0.5.6",
            "llama-index-embeddings-openai==0.3.1",
            "llama-index-embeddings-bedrock==0.5.0",
        ],
    },
    package_data={
        "": [
            "integrations/*/inventory.json",
            "integrations/*/python_sdk_clients.yml",
            "integrations/*/compliance.json",
            "integrations/*/open_api.json",
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
