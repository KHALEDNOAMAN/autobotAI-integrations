"""Unit tests for the opt-in refreshable AWS credentials path.

The integrations library normally builds boto3 clients with static
credentials.  When the autobotAI agent runs a long session it sets a
``contextvars.ContextVar`` holding a refresh callable; the AWS service
checks that var and switches to ``botocore.RefreshableCredentials``.

These tests cover the primitive only — the AWS service-side integration
(``AWSService.build_python_exec_combinations_hook``) is exercised via
the agent's smoke tests.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from autobotAI_integrations.utils.refreshable_creds import (
    build_refreshable_aws_session,
    current_aws_creds_resolver,
)


def _expiry(seconds_from_now: int) -> str:
    return (
        datetime.now(timezone.utc) + timedelta(seconds=seconds_from_now)
    ).isoformat()


class TestBuildRefreshableAWSSession:
    def test_session_uses_resolver_credentials(self):
        def resolver(task_id):
            return {
                "access_key": "AKIA-A",
                "secret_key": "SEC-A",
                "token": "TOK-A",
                "expiry_time": _expiry(3500),
            }

        session = build_refreshable_aws_session(
            resolver, task_id="t1", region_name="us-east-1"
        )
        frozen = session.get_credentials().get_frozen_credentials()
        assert frozen.access_key == "AKIA-A"
        assert frozen.secret_key == "SEC-A"
        assert frozen.token == "TOK-A"

    def test_refresh_callback_is_invoked_on_expiry(self):
        state = {"generation": 0}

        def resolver(task_id):
            state["generation"] += 1
            return {
                "access_key": f"AKIA-{state['generation']}",
                "secret_key": f"SEC-{state['generation']}",
                "token": f"TOK-{state['generation']}",
                "expiry_time": _expiry(3500),
            }

        session = build_refreshable_aws_session(resolver, task_id="t1")
        creds_obj = session.get_credentials()

        # First read pulls from initial metadata (generation=1).
        first = creds_obj.get_frozen_credentials()
        assert first.access_key == "AKIA-1"

        # Force a refresh.
        creds_obj._expiry_time = datetime.now(timezone.utc) - timedelta(
            seconds=10
        )
        second = creds_obj.get_frozen_credentials()
        assert second.access_key == "AKIA-2"

    def test_resolver_accepts_env_var_shape(self):
        """Some callers find it cleaner to return AWS_* env var keys; the
        builder should normalise these too."""

        def resolver(task_id):
            return {
                "AWS_ACCESS_KEY_ID": "AKIA",
                "AWS_SECRET_ACCESS_KEY": "SEC",
                "AWS_SESSION_TOKEN": "TOK",
                "expiry_time": _expiry(3500),
            }

        session = build_refreshable_aws_session(resolver, task_id="t1")
        frozen = session.get_credentials().get_frozen_credentials()
        assert frozen.access_key == "AKIA"

    def test_empty_creds_first_call_raises(self):
        def resolver(task_id):
            return None

        with pytest.raises(ValueError):
            build_refreshable_aws_session(resolver, task_id="t1")


class TestContextVar:
    def test_default_is_none(self):
        # Each test runs in a fresh contextvar scope.
        assert current_aws_creds_resolver.get() is None

    def test_set_and_reset(self):
        def resolver(task_id):
            return {
                "access_key": "x",
                "secret_key": "y",
                "expiry_time": _expiry(3500),
            }

        token = current_aws_creds_resolver.set(resolver)
        try:
            assert current_aws_creds_resolver.get() is resolver
        finally:
            current_aws_creds_resolver.reset(token)
        assert current_aws_creds_resolver.get() is None
