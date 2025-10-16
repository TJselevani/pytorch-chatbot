"""
Transfer workflow for moving funds between fleets.
"""

import operator
import re
import logging
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage


# from ai_util.extractors import extract_amount, extract_fleet_number
from utils.validators import validate_amount, validate_fleet_number
from utils.language import MultilingualResponses

logger = logging.getLogger(__name__)


class TransferWorkflowState(TypedDict):
    messages: Annotated[list, operator.add]
    user_id: str
    language: str
    amount: float | None
    source_fleet: str | None
    dest_fleet: str | None
    details_complete: bool
    transfer_complete: bool
    error: str | None
    awaiting_input: str | None


def create_transfer_workflow(transfer_service, account_service, checkpointer):
    """Factory function to create transfer workflow."""

    def collect_transfer_details(state: TransferWorkflowState):
        """Extract transfer details from message."""
        if not state["messages"]:
            response = MultilingualResponses.get(
                "transfer", "request_details", state["language"]
            )
            return {
                **state,
                "awaiting_input": "details",
                "messages": [AIMessage(content=response)],
            }

        message = state["messages"][-1].content

        # Try to extract all details at once using regex
        pattern = r"transfer\s+(?:ksh\s*)?(\d+(?:,\d{3})*(?:\.\d{2})?)\s+from\s+([a-z]{2}\d{2,4})\s+to\s+([a-z]{2}\d{2,4})"
        match = re.search(pattern, message.lower())

        if match:
            amount_str = match.group(1).replace(",", "")
            amount = float(amount_str)
            source_fleet = match.group(2).upper()
            dest_fleet = match.group(3).upper()

            # Validate amount
            if not validate_amount(amount):
                return {
                    **state,
                    "awaiting_input": "details",
                    "error": "Invalid amount",
                    "messages": [
                        AIMessage(content="Amount must be between 1 and 1,000,000 KSh.")
                    ],
                }

            # Validate fleet numbers
            if not validate_fleet_number(source_fleet):
                return {
                    **state,
                    "awaiting_input": "details",
                    "error": "Invalid source fleet",
                    "messages": [
                        AIMessage(
                            content=f"Invalid source fleet number: {source_fleet}"
                        )
                    ],
                }

            if not validate_fleet_number(dest_fleet):
                return {
                    **state,
                    "awaiting_input": "details",
                    "error": "Invalid destination fleet",
                    "messages": [
                        AIMessage(
                            content=f"Invalid destination fleet number: {dest_fleet}"
                        )
                    ],
                }

            # Validate fleets exist (using account service)
            try:
                source_valid = account_service.validate_fleet(source_fleet)
                dest_valid = account_service.validate_fleet(dest_fleet)

                if not source_valid.get("valid"):
                    return {
                        **state,
                        "awaiting_input": "details",
                        "error": "Source fleet not found",
                        "messages": [
                            AIMessage(
                                content=f"Source fleet {source_fleet} not found in system."
                            )
                        ],
                    }

                if not dest_valid.get("valid"):
                    return {
                        **state,
                        "awaiting_input": "details",
                        "error": "Destination fleet not found",
                        "messages": [
                            AIMessage(
                                content=f"Destination fleet {dest_fleet} not found in system."
                            )
                        ],
                    }

                # All details are valid
                response = MultilingualResponses.get(
                    "transfer",
                    "confirm",
                    state["language"],
                    amount=amount,
                    source=source_fleet,
                    dest=dest_fleet,
                )

                return {
                    **state,
                    "amount": amount,
                    "source_fleet": source_fleet,
                    "dest_fleet": dest_fleet,
                    "details_complete": True,
                    "awaiting_input": "confirmation",
                    "error": None,
                    "messages": [AIMessage(content=response)],
                }

            except Exception as e:
                logger.error(f"Fleet validation error: {e}", exc_info=True)
                return {
                    **state,
                    "awaiting_input": "details",
                    "error": str(e),
                    "messages": [
                        AIMessage(
                            content="Failed to validate fleet numbers. Please try again."
                        )
                    ],
                }
        else:
            # Could not parse transfer details
            response = MultilingualResponses.get(
                "transfer", "request_details", state["language"]
            )
            return {
                **state,
                "awaiting_input": "details",
                "messages": [
                    AIMessage(
                        content=response + "\nExample: Transfer 500 from SM34 to SM45"
                    )
                ],
            }

    def execute_transfer(state: TransferWorkflowState):
        """Execute the transfer after confirmation."""
        if not state["messages"]:
            response = MultilingualResponses.get(
                "transfer",
                "confirm",
                state["language"],
                amount=state["amount"],
                source=state["source_fleet"],
                dest=state["dest_fleet"],
            )
            return {
                **state,
                "awaiting_input": "confirmation",
                "messages": [AIMessage(content=response)],
            }

        confirmation = state["messages"][-1].content.lower().strip()

        # Check for confirmation
        affirmative_words = [
            "yes",
            "confirm",
            "proceed",
            "ok",
            "ndio",
            "sawa",
            "endelea",
        ]
        negative_words = ["no", "cancel", "stop", "hapana", "sitisha"]

        if any(word in confirmation for word in negative_words):
            response = MultilingualResponses.get(
                "transfer", "cancelled", state["language"]
            )
            return {
                **state,
                "transfer_complete": False,
                "awaiting_input": None,
                "messages": [AIMessage(content=response)],
            }

        if any(word in confirmation for word in affirmative_words):
            try:
                # Process the transfer
                result = transfer_service.process_transfer(
                    user_id=state["user_id"],
                    source_fleet=state["source_fleet"],
                    dest_fleet=state["dest_fleet"],
                    amount=state["amount"],
                )

                if result.get("status") == "success":
                    response = MultilingualResponses.get(
                        "transfer",
                        "completed",
                        state["language"],
                        txn_id=result.get("transaction_id", "N/A"),
                    )
                    return {
                        **state,
                        "transfer_complete": True,
                        "awaiting_input": None,
                        "messages": [AIMessage(content=response)],
                    }
                else:
                    return {
                        **state,
                        "transfer_complete": False,
                        "error": result.get("message", "Transfer failed"),
                        "awaiting_input": None,
                        "messages": [
                            AIMessage(
                                content=f"Transfer failed: {result.get('message', 'Unknown error')}"
                            )
                        ],
                    }

            except Exception as e:
                logger.error(f"Transfer execution error: {e}", exc_info=True)
                return {
                    **state,
                    "transfer_complete": False,
                    "error": str(e),
                    "awaiting_input": None,
                    "messages": [
                        AIMessage(content="Transfer failed. Please try again later.")
                    ],
                }
        else:
            # Unclear response
            return {
                **state,
                "awaiting_input": "confirmation",
                "messages": [
                    AIMessage(
                        content="Please reply 'yes' to confirm or 'no' to cancel."
                    )
                ],
            }

    # Routing logic
    def should_execute_transfer(state: TransferWorkflowState) -> str:
        if state.get("error") and not state.get("details_complete"):
            return END
        if state.get("awaiting_input") == "details":
            return END
        if state.get("awaiting_input") == "confirmation":
            return END
        if state.get("details_complete") and not state.get("transfer_complete"):
            return "execute_transfer"
        return "collect_details"

    def is_complete(state: TransferWorkflowState) -> str:
        return END

    # Build workflow
    workflow = StateGraph(TransferWorkflowState)

    workflow.add_node("collect_details", collect_transfer_details)
    workflow.add_node("execute_transfer", execute_transfer)

    workflow.add_edge(START, "collect_details")
    workflow.add_conditional_edges("collect_details", should_execute_transfer)
    workflow.add_conditional_edges("execute_transfer", is_complete)

    return workflow.compile(checkpointer=checkpointer)
