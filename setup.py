from setuptools import setup, find_packages

setup(
    name="autobotAI_integrations",
    version="1.0.0",
    author="ShunyEka Systems Private Limited",
    author_email="hello@shunyeka.com",
    description="A python package that contains all the integrations for autobotAI",
    packages=find_packages(),
    install_requires=[
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
        "pygitguardian",
        "azure-mgmt-resource",
        "python-gitlab",
        "openai",
        "slack-sdk",
        "ollama",
        "jira"
    ],
    package_data={
        "": ["integrations/*/inventory.json", "integrations/*/python_sdk_clients.yml"]
    },
    classifiers=[
        "License :: Other/Proprietary License" "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.10",
    include_package_data=True,
)
