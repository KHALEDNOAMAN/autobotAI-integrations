from typing import Optional

DEFAULT_AWS_SUB_INTEGRATION_REGION = "us-east-1"

AWS_DERIVED_INTEGRATION_TYPES = frozenset(
    {"aws_bedrock", "aws_ses", "aws_athena"}
)


def resolve_aws_sub_integration_region(
    requested_region: Optional[str] = None,
    *,
    stack_region: Optional[str] = None,
    parent_default_region: Optional[str] = None,
) -> str:
    """Resolve the AWS region for a derived integration (Bedrock, SES, Athena).

    Priority:
    1. Explicit region from the caller
    2. CloudFormation stack deployment region (IAM-role setup path)
    3. Parent AWS integration ``defaultRegion``
    4. ``us-east-1`` fallback for other integration methods
    """
    for candidate in (
        requested_region,
        stack_region,
        parent_default_region,
        DEFAULT_AWS_SUB_INTEGRATION_REGION,
    ):
        if candidate and str(candidate).strip():
            return str(candidate).strip()
    return DEFAULT_AWS_SUB_INTEGRATION_REGION
