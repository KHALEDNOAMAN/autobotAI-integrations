"""Optional refreshable credentials for AWS python-SDK actions.

By default, ``AWSService.build_python_exec_combinations_hook`` builds boto3
clients with static credentials extracted from ``payload_task.creds.envs``.
Those credentials are STS-issued and expire after ~1 hour (role-chaining
cap), which is fine for short Lambda invocations but causes
``ExpiredTokenException`` mid-call in long-running agent sessions.

This module offers an *opt-in* refreshable-credentials path:

1. A caller (the autobotAI agent, in long-running mode) sets the contextvar
   ``current_aws_creds_resolver`` to a callable that returns fresh AWS env
   credentials on demand.
2. The AWS service checks the contextvar inside the python-SDK hook.  When
   set, it builds boto3 clients backed by ``botocore.RefreshableCredentials``
   whose refresh callback invokes the resolver.  Botocore re-reads
   credentials whenever the cached set is within ~15 minutes of expiry.
3. When the contextvar is unset (Lambda mode, standalone CLI use, tests),
   the existing static-credentials path is taken — fully backward
   compatible.

The resolver returns a dict shaped for botocore::

    {
        "access_key": "...",
        "secret_key": "...",
        "token": "...",          # optional
        "expiry_time": "<ISO-8601>",
    }
"""

from __future__ import annotations

import contextvars
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

if TYPE_CHECKING:
    import boto3

# Default fallback TTL when the resolver returns no ``expiry_time``.  Real
# STS sessions are 3600s; we use 3500s to leave a small margin between
# server-side issuance and consumption here.
_DEFAULT_TTL_SECONDS = 3500


# Callable signature: takes the task_id (so a single resolver can serve
# multiple tasks in the same process) and returns the botocore-shaped creds.
# When the resolver has no creds for the given task_id, returning ``None``
# tells the caller to fall through to the static-creds path.
AWSCredsResolver = Callable[[Optional[str]], Optional[Dict[str, Any]]]

current_aws_creds_resolver: "contextvars.ContextVar[Optional[AWSCredsResolver]]" = (
    contextvars.ContextVar("current_aws_creds_resolver", default=None)
)


def build_refreshable_aws_session(
    resolver: AWSCredsResolver,
    task_id: Optional[str],
    region_name: Optional[str] = None,
) -> "boto3.Session":
    """Return a boto3.Session whose credentials auto-refresh via *resolver*.

    Botocore calls the refresh callback whenever the cached creds are within
    ~15 minutes of expiry — so any client built from this session picks up
    rotated STS creds transparently on the next AWS API call.
    """
    import boto3
    from botocore.credentials import RefreshableCredentials
    from botocore.session import get_session as get_botocore_session

    def _refresh() -> Dict[str, Any]:
        snapshot = resolver(task_id) or {}
        # Ensure the shape botocore expects.  ``expiry_time`` is required —
        # synthesize one from "now + default TTL" when the resolver doesn't
        # provide it.
        access_key = snapshot.get("access_key") or snapshot.get("AWS_ACCESS_KEY_ID")
        secret_key = snapshot.get("secret_key") or snapshot.get("AWS_SECRET_ACCESS_KEY")
        token = snapshot.get("token") or snapshot.get("AWS_SESSION_TOKEN")
        expiry = snapshot.get("expiry_time")
        if not expiry:
            expiry = (
                datetime.now(timezone.utc) + timedelta(seconds=_DEFAULT_TTL_SECONDS)
            ).isoformat()
        return {
            "access_key": access_key,
            "secret_key": secret_key,
            "token": token,
            "expiry_time": expiry,
        }

    initial = _refresh()
    if not initial.get("access_key") or not initial.get("secret_key"):
        raise ValueError(
            "AWS creds resolver returned empty access/secret key on first call"
        )

    creds = RefreshableCredentials.create_from_metadata(
        metadata=initial,
        refresh_using=_refresh,
        method="autobotai-task-rotation",
    )

    botocore_session = get_botocore_session()
    botocore_session._credentials = creds
    if region_name:
        botocore_session.set_config_variable("region", region_name)
    return boto3.Session(botocore_session=botocore_session)
