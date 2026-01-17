"""
OTP authentication workflow implementation.
"""

import operator
import logging
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage


from utils.extractors import extract_phone_number, extract_fleet_number
from utils.validators import (
    validate_phone_number,
    validate_fleet_number,
    validate_otp_code,
)
from utils.language import MultilingualResponses
from langgraph.pregel import Pregel

logger = logging.getLogger(__name__)


class OTPWorkflowState(TypedDict):
    messages: Annotated[list, operator.add]
    user_id: str
    phone_number: str | None
    fleet_number: str | None
    language: str
    otp_sent: bool
    verified: bool
    error: str | None
    awaiting_input: str | None


def create_otp_workflow(account_service, checkpointer):
    """Factory function to create OTP workflow."""

    def collect_details(state: OTPWorkflowState):
        """Collect phone number and fleet number."""
        latest_message = state["messages"][-1].content if state["messages"] else ""

        # Extract information
        phone = extract_phone_number(latest_message)
        fleet = extract_fleet_number(latest_message)

        # Merge with existing state
        current_phone = phone or state.get("phone_number")
        current_fleet = fleet or state.get("fleet_number")

        updates = {**state, "messages": []}

        # Update state with found values
        if phone:
            updates["phone_number"] = current_phone
        if fleet:
            updates["fleet_number"] = current_fleet

        # Validate and determine what's missing
        if not current_phone and not current_fleet:
            response = MultilingualResponses.get(
                "otp", "request_details", state["language"]
            )
            return {
                **updates,
                "awaiting_input": "both",
                "messages": [AIMessage(content=response)],
            }
        elif not current_phone:
            response = MultilingualResponses.get(
                "otp", "request_phone", state["language"]
            )
            return {
                **updates,
                "awaiting_input": "phone",
                "messages": [AIMessage(content=response)],
            }
        elif not current_fleet:
            response = MultilingualResponses.get(
                "otp", "request_fleet", state["language"]
            )
            return {
                **updates,
                "awaiting_input": "fleet",
                "messages": [AIMessage(content=response)],
            }

        # Validate formats
        if not validate_phone_number(current_phone):
            return {
                **updates,
                "phone_number": None,
                "awaiting_input": "phone",
                "messages": [
                    AIMessage(
                        content="Invalid phone number format. Please provide a valid Kenyan number."
                    )
                ],
            }

        if not validate_fleet_number(current_fleet):
            return {
                **updates,
                "fleet_number": None,
                "awaiting_input": "fleet",
                "messages": [
                    AIMessage(
                        content="Invalid fleet number format. Please use format like SM34."
                    )
                ],
            }

        # All details collected and valid
        return {
            **updates,
            "phone_number": current_phone,
            "fleet_number": current_fleet,
            "awaiting_input": None,
        }

    def send_otp(state: OTPWorkflowState):
        """Send OTP to user's phone."""
        phone = state["phone_number"]

        try:
            # Validate fleet with service
            fleet_validation = account_service.validate_fleet(state["fleet_number"])
            if not fleet_validation.get("valid"):
                return {
                    **state,
                    "error": "Invalid fleet number",
                    "messages": [
                        AIMessage(content="Fleet number not found in system.")
                    ],
                }

            # Send OTP
            result = account_service.send_otp(phone)

            if result.get("status") == "success":
                response = MultilingualResponses.get(
                    "otp", "otp_sent", state["language"], phone=phone
                )
                return {
                    **state,
                    "otp_sent": True,
                    "awaiting_input": "otp",
                    "messages": [AIMessage(content=response)],
                }
            else:
                response = MultilingualResponses.get(
                    "otp", "otp_failed", state["language"]
                )
                return {
                    **state,
                    "error": result.get("message", "Failed to send OTP"),
                    "messages": [AIMessage(content=response)],
                }

        except Exception as e:
            logger.error(f"OTP send error: {e}", exc_info=True)
            response = MultilingualResponses.get("otp", "otp_failed", state["language"])
            return {**state, "error": str(e), "messages": [AIMessage(content=response)]}

    def verify_otp(state: OTPWorkflowState):
        """Verify OTP code."""
        if not state["messages"]:
            return {
                **state,
                "awaiting_input": "otp",
                "messages": [AIMessage(content="Please enter your OTP code.")],
            }

        otp_code = state["messages"][-1].content.strip()

        # Validate OTP format
        if not validate_otp_code(otp_code):
            return {
                **state,
                "awaiting_input": "otp",
                "messages": [
                    AIMessage(content="Invalid OTP format. Please enter 4-6 digits.")
                ],
            }

        try:
            result = account_service.verify_otp(state["phone_number"], otp_code)

            if result.get("status") == "success":
                response = MultilingualResponses.get(
                    "otp", "verified", state["language"]
                )
                return {
                    **state,
                    "verified": True,
                    "awaiting_input": None,
                    "messages": [AIMessage(content=response)],
                }
            else:
                response = MultilingualResponses.get(
                    "otp", "invalid_otp", state["language"]
                )
                return {
                    **state,
                    "awaiting_input": "otp",
                    "messages": [AIMessage(content=response)],
                }

        except Exception as e:
            logger.error(f"OTP verification error: {e}", exc_info=True)
            return {
                **state,
                "awaiting_input": "otp",
                "messages": [
                    AIMessage(content="Verification failed. Please try again.")
                ],
            }

    # Define routing logic
    def should_send_otp(state: OTPWorkflowState) -> str:
        if state.get("error"):
            return END
        if not state.get("phone_number") or not state.get("fleet_number"):
            return END  # stop until user provides input
        if not state.get("otp_sent"):
            return "send_otp"
        return END

    def should_verify(state: OTPWorkflowState) -> str:
        if state.get("verified"):
            return END
        if state.get("otp_sent") and not state.get("verified"):
            return "verify_otp"
        return END

    def is_complete(state: OTPWorkflowState) -> str:
        return END

    # Build workflow
    workflow = StateGraph(OTPWorkflowState)

    workflow.add_node("collect_details", collect_details)
    workflow.add_node("send_otp", send_otp)
    workflow.add_node("verify_otp", verify_otp)

    workflow.add_edge(START, "collect_details")
    workflow.add_conditional_edges("collect_details", should_send_otp)
    workflow.add_conditional_edges("send_otp", should_verify)
    workflow.add_conditional_edges("verify_otp", is_complete)

    # ✅ Compile workflow and wrap with Pregel
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    return compiled_graph

    # return workflow.compile(checkpointer=checkpointer)
