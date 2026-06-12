"""Contract test for the allow_user_interaction field on DeepAgentPayload.

This field is the cross-repo switch consumed by autobotAI-core (producer) and
autobotAI-agents (runtime). It must default to True (interactive) and be
distinct from `autonomous`.
"""

from autobotAI_integrations.deep_agent_schema import DeepAgentPayload


def _payload(**overrides):
    base = dict(job_id="j", tasks=[], user_prompt="hi")
    base.update(overrides)
    return DeepAgentPayload(**base)


def test_defaults_to_interactive():
    assert _payload().allow_user_interaction is True


def test_explicit_false_is_headless():
    assert _payload(allow_user_interaction=False).allow_user_interaction is False


def test_independent_of_autonomous():
    # The two flags are orthogonal: a headless run can still be autonomous,
    # and an interactive run can require approve-before-act.
    p = _payload(autonomous=False, allow_user_interaction=True)
    assert p.autonomous is False
    assert p.allow_user_interaction is True
