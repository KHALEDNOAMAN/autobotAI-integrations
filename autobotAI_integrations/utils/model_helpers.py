"""Model-specific helper functions and compatibility checks for LLM calls."""

_LLAMA_PROMPT_MARKERS = (
    "<|begin_of_text|>",
    "<|eot_id|>",
    "<|start_header_id|>user<|end_header_id|>",
    "<|start_header_id|>assistant<|end_header_id|>",
)


def is_meta_llama_model(model: str) -> bool:
    if not model:
        return False
    normalized = model.lower()
    for prefix in ("global.", "us.", "eu.", "apac."):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break
    return normalized.startswith("meta.llama")


def bedrock_model_rejects_temperature(model: str) -> bool:
    """Claude Sonnet 5 rejects temperature in Bedrock Converse requests."""
    if not model:
        return False
    normalized = model.lower()
    for prefix in ("global.", "us.", "eu.", "apac."):
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :]
            break
    return "claude-sonnet-5" in normalized


def format_prompt_for_model(prompt: str, model: str) -> str:
    """Keep Meta Llama chat tokens; strip them for other model families."""
    if is_meta_llama_model(model):
        return prompt
    cleaned = prompt
    for marker in _LLAMA_PROMPT_MARKERS:
        cleaned = cleaned.replace(marker, "")
    return cleaned.strip()
