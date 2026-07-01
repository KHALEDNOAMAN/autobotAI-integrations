"""Lightweight single-shot LLM call utility.

No agent state, no tools, no memory. Uses LLMConfig from deep_agent_schema so
the same credentials work across the deep agent and utility call sites (goal
classifier, notification generator, etc.).
"""
from __future__ import annotations

import logging
from typing import Optional, Type, TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.settings import ModelSettings

from autobotAI_integrations.deep_agent_schema import LLMConfig

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _build_model(llm_config: LLMConfig):
    """Map LLMConfig → a pydantic-ai model instance.

    Delegates to each integration class's build_model_from_credentials() so
    the provider-specific pydantic-ai construction lives in one place (the
    integration file) instead of being duplicated here. anthropic and
    google_genai have no integration class in this repo (they're only used
    via quick_llm_call), so they stay inline below.
    """
    provider = llm_config.provider
    credentials = {
        "api_key": llm_config.api_key,
        "base_url": llm_config.base_url,
        "region": llm_config.region,
        "access_key": llm_config.access_key,
        "secret_key": llm_config.secret_key,
        "session_token": llm_config.session_token,
    }

    if provider == "openai":
        from autobotAI_integrations.integrations.openai import OpenAIService

        return OpenAIService.build_model_from_credentials(llm_config.model, credentials)

    if provider == "azure_foundry_openai":
        from autobotAI_integrations.integrations.azure_foundry_openai import AzureOpenAIService

        return AzureOpenAIService.build_model_from_credentials(llm_config.model, credentials)

    if provider == "openrouter":
        from autobotAI_integrations.integrations.openrouter import OpenRouterService

        return OpenRouterService.build_model_from_credentials(llm_config.model, credentials)

    if provider == "aws_bedrock":
        from autobotAI_integrations.integrations.aws_bedrock import AWSBedrockService

        return AWSBedrockService.build_model_from_credentials(llm_config.model, credentials)

    raise ValueError(
        f"Unsupported LLM provider: {provider!r}. "
        "Supported: openai, anthropic, aws_bedrock, azure_foundry_openai, "
        "google_genai, openrouter"
    )


async def quick_llm_call(
    prompt: str,
    llm_config: LLMConfig,
    *,
    output_schema: Optional[Type[T]] = None,
    system_prompt: Optional[str] = None,
    max_tokens: int = 500,
    temperature: float = 0.1,
) -> "T | str":
    """Single lightweight LLM call — no agent state, no tools, no memory.

    Uses the same LLMConfig as the deep agent so no separate credential
    management is needed. When output_schema is provided, pydantic-ai injects
    the JSON schema into the prompt and retries automatically on parse failure.

    Args:
        prompt: The user message.
        llm_config: Provider credentials and model selection.
        output_schema: Optional Pydantic model class for structured output.
        system_prompt: Optional system instruction.
        max_tokens: Hard cap on response length. Default 500 keeps utility
            call costs low — increase only for longer free-text outputs.
        temperature: Sampling temperature. Defaults to 0.1 for deterministic
            structured calls (classifiers, intent extraction, etc.).

    Returns:
        Validated Pydantic instance when output_schema is provided, else str.
    """
    model = _build_model(llm_config)
    agent: Agent = Agent(
        model,
        output_type=output_schema if output_schema is not None else str,
        system_prompt=system_prompt or "",
        model_settings=ModelSettings(
            max_tokens=max_tokens,
            temperature=temperature,
        ),
    )
    result = await agent.run(prompt)
    return result.output
