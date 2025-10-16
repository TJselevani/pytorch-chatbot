"""
Base workflow classes and utilities.
"""

import operator
from typing import TypedDict, Annotated, Optional
from langchain_core.messages import AIMessage, HumanMessage


class BaseWorkflowState(TypedDict):
    """Base state for all workflows."""

    messages: Annotated[list, operator.add]
    user_id: str
    language: str
    awaiting_input: Optional[str]
    error: Optional[str]


def create_ai_response(content: str) -> AIMessage:
    """Helper to create AI message."""
    return AIMessage(content=content)


def create_human_message(content: str) -> HumanMessage:
    """Helper to create human message."""
    return HumanMessage(content=content)
