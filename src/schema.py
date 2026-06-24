from __future__ import annotations

from typing import Literal, TypedDict, Union


class SearchResult(TypedDict):
    """One result entry returned by search_web()."""
    title: str
    url: str
    content: str


class ToolResultMessage(TypedDict):
    """A single tool result fed back to Claude in the conversation."""
    type: Literal["tool_result"]
    tool_use_id: str
    content: str  # JSON-encoded list for search results; plain string for fetch_page


class UserMessage(TypedDict):
    role: Literal["user"]
    content: Union[str, list[ToolResultMessage]]


class AssistantMessage(TypedDict):
    role: Literal["assistant"]
    content: list  # Anthropic SDK content blocks (TextBlock, ToolUseBlock, …)


Message = Union[UserMessage, AssistantMessage]


class ResearchSession(TypedDict):
    """Persisted state for one research run, written to state/sessions.json."""
    session_id: str
    topic: str
    messages: list[Message]
    report: str | None   # None until agent produces its final end_turn response
    created_at: str      # ISO 8601 timestamp, e.g. "2026-06-23T14:00:00Z"
