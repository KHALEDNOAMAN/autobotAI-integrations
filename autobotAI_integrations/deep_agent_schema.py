"""
Shared Pydantic models for the Deep Agent.

These types are the contract between autobotAI-core (server) and
autobotAI-agents (runtime). Keep this file the single source of truth — both
repos import from here so the payload format cannot drift.

``DeepAgentPayload`` extends the standard autobotAI ``Payload`` with fields
needed by the deep agent: LLM config, prompts, MCP servers, workspace URLs,
AppSync streaming, HITL mode, and skills.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from autobotAI_integrations.payload_schema import Payload, PayloadCommonContext


# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------


class LLMConfig(BaseModel):
    """Credentials and settings for the LLM provider."""

    provider: str = Field(
        ...,
        description="LLM provider: openai, anthropic, bedrock, google_genai",
    )
    model: str = Field(
        ...,
        description="Model identifier, e.g. gpt-5-mini, claude-sonnet-4-20250514",
    )
    api_key: Optional[str] = Field(
        None, description="API key (OpenAI, Anthropic, Google)"
    )
    base_url: Optional[str] = Field(None, description="Custom endpoint URL")
    region: Optional[str] = Field(None, description="AWS region (for Bedrock)")
    access_key: Optional[str] = Field(None, description="AWS access key (for Bedrock)")
    secret_key: Optional[str] = Field(None, description="AWS secret key (for Bedrock)")
    session_token: Optional[str] = Field(
        None, description="AWS session token (for Bedrock)"
    )
    temperature: float = Field(0.7, description="Sampling temperature")
    max_tokens: int = Field(8192, description="Maximum tokens in response")
    max_iterations: int | None = Field(50, description="Max number of iteration agent can do on single run.")


# ---------------------------------------------------------------------------
# MCP remote servers
# ---------------------------------------------------------------------------


class MCPRemoteServer(BaseModel):
    """Configuration for a remote MCP server (streamable HTTP transport)."""

    name: str = Field(..., description="Human-readable server name")
    url: str = Field(..., description="Streamable HTTP endpoint URL")
    headers: Dict[str, str] = Field(
        default_factory=dict, description="Additional HTTP headers"
    )


# ---------------------------------------------------------------------------
# AppSync streaming
# ---------------------------------------------------------------------------


class AppSyncConfig(BaseModel):
    """AppSync Events HTTP API configuration for real-time streaming.

    Authentication: provide either ``api_key`` (API_KEY mode) **or** the
    ``aws_*`` fields (AWS_IAM mode with SigV4 signing).  IAM credentials
    take priority when both are present.
    """

    http_endpoint: str = Field(..., description="AppSync Events HTTP endpoint")
    channel: str = Field(
        ...,
        description="Channel namespace for this execution (publish/subscribe)",
    )
    realtime_endpoint: Optional[str] = Field(
        None,
        description="AppSync realtime WebSocket endpoint (for HITL subscribe)",
    )

    # --- API Key auth (legacy) -----------------------------------------------
    api_key: Optional[str] = Field(None, description="API key for authentication")

    # --- IAM / SigV4 auth (preferred) ----------------------------------------
    aws_access_key_id: Optional[str] = Field(
        None, description="AWS temporary access key ID (for IAM auth)"
    )
    aws_secret_access_key: Optional[str] = Field(
        None, description="AWS temporary secret access key (for IAM auth)"
    )
    aws_session_token: Optional[str] = Field(
        None, description="AWS temporary session token (for IAM auth)"
    )
    aws_region: Optional[str] = Field(
        None, description="AWS region for SigV4 signing (e.g. us-east-1)"
    )


# ---------------------------------------------------------------------------
# Memory spaces
# ---------------------------------------------------------------------------


class MemorySpaceConfig(BaseModel):
    """Describes a single memory space available to the agent."""

    id: str = Field(..., description="Unique memory space identifier")
    name: str = Field(..., description="Human-readable memory space name")
    description: str = Field(
        "", description="What this memory space contains / is used for"
    )


# ---------------------------------------------------------------------------
# Skills lifecycle
# ---------------------------------------------------------------------------


class SkillAction(str, Enum):
    """Action to perform for a skill entry in the payload."""

    ADD = "add"
    REMOVE = "remove"


class SkillConfig(BaseModel):
    """Describes a single skill to install or remove in the workspace."""

    skill_id: str = Field(
        ...,
        description="Unique skill identifier; used as the folder name under skills/",
    )
    name: str = Field(..., description="Human-readable skill name")
    action: SkillAction = Field(
        SkillAction.ADD,
        description="'add' installs if absent; 'remove' deletes unconditionally",
    )
    presigned_url: Optional[str] = Field(
        None,
        description="Presigned GET URL for the skill content (.zip or single file)",
    )
    version: Optional[str] = Field(None, description="Informational version string")
    description: Optional[str] = Field(
        None, description="Skill description passed through to the agent"
    )


# ---------------------------------------------------------------------------
# User-attached files
# ---------------------------------------------------------------------------


class FileConfig(BaseModel):
    """A user-attached file made available to the agent in workspace/files/.

    The server generates a 1-hour presigned GET URL and ships filename +
    description so the agent can decide whether to download it. The file_id
    is the FileStore record ID; agents use it (or the filename) to detect
    that a file is already present and skip re-downloading.
    """

    file_id: str = Field(..., description="FileStore record ID")
    name: str = Field(
        ...,
        description=(
            "Original filename; used as the on-disk name under workspace/files/."
        ),
    )
    presigned_url: str = Field(
        ..., description="Presigned GET URL for the file (valid 1 hour)"
    )
    description: Optional[str] = Field(
        None,
        description=(
            "Optional human-readable description; surfaced to the agent so it "
            "can decide whether the file is relevant to the task."
        ),
    )


# ---------------------------------------------------------------------------
# Deep Agent payload — extends autobotAI Payload
# ---------------------------------------------------------------------------


class DeepAgentPayload(Payload):
    """
    Extends the standard autobotAI ``Payload`` with deep-agent-specific fields.

    Inherited from ``Payload``:
        job_id, state, tasks, output_url, api_key, api_url, job_size,
        common_params, common_context, extra_details
    """

    # --- LLM ---------------------------------------------------------------
    llm_config: Optional[LLMConfig] = Field(
        None, description="LLM provider and model configuration"
    )

    # --- Prompts -----------------------------------------------------------
    system_prompt: Optional[str] = Field(
        None, description="System prompt for the agent"
    )
    user_prompt: str = Field(..., description="Initial user prompt")
    # Note: Conversation history is handled automatically by LangGraph checkpoints.
    # No need for a messages field in the payload.

    # --- MCP servers -------------------------------------------------------
    mcp_servers: List[MCPRemoteServer] = Field(
        default_factory=list, description="Remote MCP servers to connect"
    )

    # --- Workspace S3 URLs -------------------------------------------------
    workspace_url: Optional[str] = Field(
        None, description="Presigned GET URL to download prior workspace archive"
    )
    workspace_upload_url: Optional[Dict[str, Any]] = Field(
        None,
        description="Presigned POST config (url + fields) to upload workspace archive",
    )

    # --- Streaming ---------------------------------------------------------
    appsync_config: Optional[AppSyncConfig] = Field(
        None, description="AppSync Events config for real-time streaming"
    )

    # --- Execution mode ----------------------------------------------------
    autonomous: bool = Field(
        True,
        description="True = autonomous execution, False = human-in-the-loop",
    )
    filesystem_enabled: bool = Field(
        True,
        description="Allow agent to read/write workspace files",
    )
    shell_access_enabled: bool = Field(
        False,
        description="Allow agent to execute shell commands",
    )

    # --- Memory spaces -----------------------------------------------------
    memory_spaces: List[MemorySpaceConfig] = Field(
        default_factory=list,
        description=(
            "Memory spaces available to the agent. When non-empty, their id/name/"
            "description are injected into the system prompt and a"
            " query_memory_space tool is added automatically."
        ),
    )

    # --- Skills ------------------------------------------------------------
    skills: Optional[List[SkillConfig]] = Field(
        None,
        description="Skills to install or remove in workspace/skills/ during setup",
    )

    # --- User-attached files -----------------------------------------------
    files: List[FileConfig] = Field(
        default_factory=list,
        description=(
            "User-attached files to materialise under workspace/files/ before "
            "the agent runs. Each entry carries a 1-hour presigned URL plus "
            "filename and (optional) description; the agent should skip "
            "re-downloading any file already present in the workspace."
        ),
    )

    # --- Timeout -----------------------------------------------------------
    max_timeout: int = Field(
        300,
        description="Maximum execution timeout in seconds",
    )

    # --- Session / Thread IDs -----------------------------------------------
    chat_session_id: Optional[str] = Field(
        None,
        description=(
            "Stable identifier for a user's chat session (conversation group). "
            "Drives the workspace S3 key — same chat_session_id → same workspace "
            "files are downloaded/uploaded, so files persist across threads."
        ),
    )
    chat_thread_id: Optional[str] = Field(
        None,
        description=(
            "Identifier for a specific conversation thread within a session. "
            "Used as the LangGraph thread_id — same chat_thread_id → same SQLite "
            "checkpoint is resumed, so the agent continues the same conversation. "
            "Different chat_thread_id → fresh SQLite thread → new conversation."
        ),
    )

    # --- HITL resume --------------------------------------------------------
    resume_decisions: Optional[List[Dict[str, Any]]] = Field(
        None,
        description=(
            "If set, the agent resumes from its checkpoint using these HITL decisions "
            "instead of starting a new run. Each entry is either "
            '{"type": "approve"} or {"type": "reject", "message": "reason"}.'
        ),
    )

    # --- Cache freshness ---------------------------------------------------
    expires_at: Optional[str] = Field(
        None,
        description=(
            "ISO-8601 UTC timestamp at which the ephemeral credentials in this "
            "payload (AppSync STS, presigned URLs) expire. Set by the payload "
            "builder to built_at + 60min. The agent should refuse to start if "
            "now > expires_at; the broker should rebuild the cached payload "
            "before this point (typically at expires_at - 16min)."
        ),
    )

    # Setting default to None — server-built payloads may omit it
    common_context: Optional[PayloadCommonContext] = None


# ---------------------------------------------------------------------------
# Response & streaming models
# ---------------------------------------------------------------------------


class DeepAgentStatus(str, Enum):
    """Agent execution status."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    AWAITING_INPUT = "awaiting_input"


class StreamEvent(BaseModel):
    """A single event published to AppSync."""

    job_id: str
    event_type: str  # message, tool_call, tool_result, status, error, awaiting_input
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[str] = None


class DeepAgentResponse(BaseModel):
    """Response returned by the orchestrator after agent execution."""

    job_id: str
    status: DeepAgentStatus
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Conversation history extracted from final state (for display/logging only). "
            "DO NOT send these back in the next payload - checkpoints handle history."
        ),
    )
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    workspace_uploaded: bool = False
    errors: List[str] = Field(default_factory=list)
    execution_metadata: Dict[str, Any] = Field(default_factory=dict)
    interrupt_data: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Present only when status=AWAITING_INPUT. Contains the raw HITLRequest "
            "from the agent interrupt: {action_requests: [...], review_configs: [...]}"
        ),
    )
