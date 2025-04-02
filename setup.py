from setuptools import setup, find_packages

import sys

base_package_data = []

extra_package_data = {
    "full": [
        "integrations/*/compliance.json",
        "integrations/*/open_api.json",
        "integrations/*/inventory.json",
        "integrations/*/python_sdk_clients.yml"
    ],
    "executable": [
        "integrations/*/python_sdk_clients.yml",
    ],
}

selected_extras = set(sys.argv) & {"full", "executable"}

if "full" in selected_extras:
    base_package_data.extend(extra_package_data["full"])

if "executable" in selected_extras:
    base_package_data.extend(extra_package_data["executable"])

setup(
    name="autobotAI_integrations",
    version="1.0.1a05",
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
            "langchain_aws>=0.2.10",
            "langchain_openai>=0.2.14",
            "pydantic-ai>=0.0.36",
        ],
    },
    package_data={
        "": base_package_data
    },
    classifiers=[
        "License :: Other/Proprietary LicenseOperating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.10",
    include_package_data=True,
)
