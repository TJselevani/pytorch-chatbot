"""
Route inquiry workflow - typically one-shot queries.
"""

import operator
import logging
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage


from utils.extractors import extract_location_pair

logger = logging.getLogger(__name__)


class RouteWorkflowState(TypedDict):
    messages: Annotated[list, operator.add]
    user_id: str
    language: str
    query_resolved: bool
    awaiting_input: str | None


def create_route_workflow(route_service, checkpointer):
    """Factory function to create route inquiry workflow."""

    def process_route_query(state: RouteWorkflowState):
        """Process route/fare inquiry."""
        if not state["messages"]:
            return {
                **state,
                "awaiting_input": "query",
                "messages": [
                    AIMessage(content="Which route would you like information about?")
                ],
            }

        message = state["messages"][-1].content

        # Try to extract locations
        origin, destination = extract_location_pair(message)

        if not origin or not destination:
            # Try to understand if it's a general route query
            # For now, provide generic route information
            response = (
                "Please specify your journey in the format: "
                "'Route from [Origin] to [Destination]' or "
                "'What's the fare from [Origin] to [Destination]?'"
            )
            return {
                **state,
                "awaiting_input": "query",
                "messages": [AIMessage(content=response)],
            }

        try:
            # Search for routes
            result = route_service.search_routes(origin, destination)

            if result.get("success") and result.get("routes"):
                routes = result["routes"]

                # Build response with route information
                response = f"📍 Route Information: {origin} → {destination}\n\n"

                # Group by company if multiple routes
                companies = list(set(r["company"] for r in routes))

                if len(companies) > 1:
                    response += f"🚌 Available Companies: {', '.join(companies)}\n\n"

                # Fare information
                fares = [r["fare"] for r in routes]
                min_fare = min(fares)
                max_fare = max(fares)

                if min_fare == max_fare:
                    response += f"💰 Fare: KSh {min_fare}\n"
                else:
                    response += f"💰 Fare Range: KSh {min_fare} - {max_fare}\n"

                # Travel time (if available)
                if routes[0].get("travel_time"):
                    response += f"⏱️ Travel Time: {routes[0]['travel_time']}\n"

                # Departure times
                departures = [r["departure"] for r in routes if r.get("departure")]
                if departures:
                    response += f"🕐 Departures: {', '.join(departures[:5])}"
                    if len(departures) > 5:
                        response += f" and {len(departures) - 5} more"
                    response += "\n"

                response += "\n💡 To book a ticket, say: 'Book from {} to {}'".format(
                    origin, destination
                )

                return {
                    **state,
                    "query_resolved": True,
                    "awaiting_input": None,
                    "messages": [AIMessage(content=response)],
                }
            else:
                response = (
                    f"Sorry, I couldn't find route information for {origin} to {destination}. "
                    "Please check the city names and try again."
                )
                return {
                    **state,
                    "query_resolved": True,
                    "awaiting_input": None,
                    "messages": [AIMessage(content=response)],
                }

        except Exception as e:
            logger.error(f"Route query error: {e}", exc_info=True)
            return {
                **state,
                "query_resolved": True,
                "awaiting_input": None,
                "messages": [
                    AIMessage(
                        content="Failed to fetch route information. Please try again later."
                    )
                ],
            }

    # Build workflow (simple one-shot)
    workflow = StateGraph(RouteWorkflowState)

    workflow.add_node("process_query", process_route_query)

    workflow.add_edge(START, "process_query")
    workflow.add_edge("process_query", END)

    return workflow.compile(checkpointer=checkpointer)
