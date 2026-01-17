"""
Booking workflow implementation.
"""

import operator
import logging
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage


from utils.extractors import extract_location_pair
from utils.language import MultilingualResponses

logger = logging.getLogger(__name__)


class BookingWorkflowState(TypedDict):
    messages: Annotated[list, operator.add]
    user_id: str
    origin: str | None
    destination: str | None
    travel_date: str | None
    selected_route: str | None
    passenger_count: int
    language: str
    routes_shown: bool
    booking_confirmed: bool
    awaiting_input: str | None
    available_routes: list | None


def create_booking_workflow(route_service, checkpointer):
    """Factory function to create booking workflow."""

    def collect_trip_details(state: BookingWorkflowState):
        """Extract trip details from message."""
        if not state["messages"]:
            response = MultilingualResponses.get(
                "booking", "request_details", state["language"]
            )
            return {
                **state,
                "awaiting_input": "details",
                "messages": [AIMessage(content=response)],
            }

        message = state["messages"][-1].content

        # Extract locations
        origin, destination = extract_location_pair(message)

        # Merge with existing state
        current_origin = origin or state.get("origin")
        current_dest = destination or state.get("destination")

        updates = {**state, "messages": []}

        if current_origin:
            updates["origin"] = current_origin
        if current_dest:
            updates["destination"] = current_dest

        # Check if we have both
        if updates.get("origin") and updates.get("destination"):
            updates["awaiting_input"] = None
            return updates
        else:
            response = MultilingualResponses.get(
                "booking", "request_details", state["language"]
            )
            return {
                **updates,
                "awaiting_input": "details",
                "messages": [AIMessage(content=response)],
            }

    def search_routes(state: BookingWorkflowState):
        """Search for available routes."""
        try:
            result = route_service.search_routes(
                origin=state["origin"],
                destination=state["destination"],
                date=state.get("travel_date"),
            )

            if result["success"] and result.get("routes"):
                # Format routes display
                response = MultilingualResponses.get(
                    "booking",
                    "routes_found",
                    state["language"],
                    origin=state["origin"],
                    destination=state["destination"],
                )
                response += "\n\n"

                for idx, route in enumerate(result["routes"], 1):
                    response += f"{idx}. {route['company']} - "
                    response += f"KSh {route['fare']} "
                    response += f"(Departs: {route['departure']})\n"

                response += "\nReply with the number or company name to book."

                return {
                    **state,
                    "routes_shown": True,
                    "available_routes": result["routes"],
                    "awaiting_input": "selection",
                    "messages": [AIMessage(content=response)],
                }
            else:
                response = MultilingualResponses.get(
                    "booking", "no_routes", state["language"]
                )
                return {
                    **state,
                    "awaiting_input": None,
                    "messages": [AIMessage(content=response)],
                }

        except Exception as e:
            logger.error(f"Route search error: {e}", exc_info=True)
            return {
                **state,
                "awaiting_input": None,
                "messages": [
                    AIMessage(content="Failed to search routes. Please try again.")
                ],
            }

    def process_selection(state: BookingWorkflowState):
        """Process route selection and create booking."""
        if not state["messages"]:
            return {
                **state,
                "awaiting_input": "selection",
                "messages": [AIMessage(content="Please select a route.")],
            }

        selection = state["messages"][-1].content.lower()
        routes = state.get("available_routes", [])

        # Find selected route
        selected_route = None
        for idx, route in enumerate(routes, 1):
            if str(idx) in selection or route["company"].lower() in selection:
                selected_route = route
                break

        if not selected_route:
            return {
                **state,
                "awaiting_input": "selection",
                "messages": [
                    AIMessage(
                        content="Invalid selection. Please choose a valid route number or company name."
                    )
                ],
            }

        # Create booking
        try:
            result = route_service.create_booking(
                route_id=selected_route["id"],
                user_id=state["user_id"],
                passenger_count=state["passenger_count"],
            )

            if result.get("status") in ["success", "confirmed"]:
                response = MultilingualResponses.get(
                    "booking",
                    "booking_confirmed",
                    state["language"],
                    booking_id=result.get("booking_id", "N/A"),
                )

                if result.get("payment_required"):
                    response += "\n\nPayment instructions will be sent shortly."

                return {
                    **state,
                    "selected_route": selected_route["id"],
                    "booking_confirmed": True,
                    "awaiting_input": None,
                    "messages": [AIMessage(content=response)],
                }
            else:
                return {
                    **state,
                    "awaiting_input": None,
                    "messages": [
                        AIMessage(content="Booking failed. Please try again.")
                    ],
                }

        except Exception as e:
            logger.error(f"Booking error: {e}", exc_info=True)
            return {
                **state,
                "awaiting_input": None,
                "messages": [
                    AIMessage(content="Failed to create booking. Please try again.")
                ],
            }

    # Routing logic
    def should_search_routes(state: BookingWorkflowState) -> str:
        if state.get("awaiting_input") == "details":
            return END
        if state.get("origin") and state.get("destination"):
            return "search_routes"
        return "collect_details"

    def should_process_booking(state: BookingWorkflowState) -> str:
        if state.get("booking_confirmed"):
            return END
        if state.get("awaiting_input") == "selection":
            return END
        if state.get("routes_shown"):
            return "process_selection"
        return END

    def is_complete(state: BookingWorkflowState) -> str:
        return END

    # Build workflow
    workflow = StateGraph(BookingWorkflowState)

    workflow.add_node("collect_details", collect_trip_details)
    workflow.add_node("search_routes", search_routes)
    workflow.add_node("process_selection", process_selection)

    workflow.add_edge(START, "collect_details")
    workflow.add_conditional_edges("collect_details", should_search_routes)
    workflow.add_conditional_edges("search_routes", should_process_booking)
    workflow.add_conditional_edges("process_selection", is_complete)

    return workflow.compile(checkpointer=checkpointer)
