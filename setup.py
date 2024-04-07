from setuptools import setup, find_packages

setup(
    name='autobotAI_integrations',
    version='0.0.0a',
    author='ShunyEka Systems Private Limited',
    author_email='hello@shunyeka.com',
    description='A python package that contains all the integrations for autobotAI',
    packages=find_packages(),
    install_requires=[
        "boto3",
        "botocore",
        "pydantic",
        "PyYAML",
        "pydash"
    ],
    package_data={'': ['integrations/*/inventory.json', 'integrations/*/python_sdk_clients.yml']},
    classifiers=[
        'License :: Other/Proprietary License'
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.11'
    ],
    python_requires='>=3.11',
    include_package_data=True

)
