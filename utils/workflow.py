from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
import operator
import re


class OTPWorkflowState(TypedDict):
    messages: Annotated[list, operator.add]
    user_id: str
    phone_number: str | None
    fleet_number: str | None
    language: str
    otp_sent: bool
    verified: bool
    error_message: str | None
    awaiting_input: str | None


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


class WorkflowManager:
    def __init__(self, account_service):
        self.account_service = account_service

    def create_otp_workflow(self):
        """Fixed OTP workflow that properly handles missing information"""

        def collect_otp_details(state: OTPWorkflowState):
            """Collect phone and fleet number"""
            from utils.extractors import extract_phone_number, extract_fleet_number

            latest_message = state["messages"][-1].content if state["messages"] else ""

            # Extract from the latest message
            phone = extract_phone_number(latest_message)
            fleet = extract_fleet_number(latest_message)

            # Merge with existing state
            current_phone = phone or state.get("phone_number")
            current_fleet = fleet or state.get("fleet_number")

            updates = {
                **state,
                "messages": [],
            }

            if phone:
                updates["phone_number"] = current_phone
            if fleet:
                updates["fleet_number"] = current_fleet

            # Check what's missing
            if not current_phone and not current_fleet:
                response = self._get_response_by_language(
                    state["language"], "awaiting_both"
                )
                return {
                    **updates,
                    "awaiting_input": "both",
                    "messages": [AIMessage(content=response)],
                }
            elif not current_phone:
                response = self._get_response_by_language(
                    state["language"], "awaiting_phone_number"
                )
                return {
                    **updates,
                    "awaiting_input": "phone",
                    "messages": [AIMessage(content=response)],
                }
            elif not current_fleet:
                response = self._get_response_by_language(
                    state["language"], "awaiting_fleet_number"
                )
                return {
                    **updates,
                    "awaiting_input": "fleet",
                    "messages": [AIMessage(content=response)],
                }
            else:
                # All info collected
                return {
                    **updates,
                    "phone_number": current_phone,
                    "fleet_number": current_fleet,
                    "awaiting_input": None,
                }

        def send_otp(state: OTPWorkflowState):
            """Send OTP"""
            phone = state["phone_number"]

            try:
                result = self.account_service.send_otp(phone)

                if result.get("status") == "success":
                    response = self._get_response_by_language(
                        state["language"], "otp_sent_success"
                    )
                    return {
                        **state,
                        "otp_sent": True,
                        "awaiting_input": "otp",
                        "messages": [AIMessage(content=response)],
                    }
                else:
                    response = self._get_response_by_language(
                        state["language"], "otp_failed"
                    )
                    return {
                        **state,
                        "error_message": result.get("message", "Unknown error"),
                        "awaiting_input": None,
                        "messages": [AIMessage(content=response)],
                    }
            except Exception as e:
                response = self._get_response_by_language(
                    state["language"], "otp_failed"
                )
                return {
                    **state,
                    "error_message": str(e),
                    "awaiting_input": None,
                    "messages": [AIMessage(content=response)],
                }

        def verify_otp(state: OTPWorkflowState):
            """Verify OTP"""
            latest_message = state["messages"][-1].content if state["messages"] else ""
            otp_code = latest_message.strip()
            phone = state["phone_number"]

            try:
                result = self.account_service.verify_otp(phone, otp_code)

                if result.get("status") == "success":
                    return {
                        **state,
                        "verified": True,
                        "awaiting_input": None,
                        "messages": [AIMessage(content=result["message"])],
                    }
                else:
                    return {
                        **state,
                        "error_message": result.get("message", "Invalid OTP"),
                        "awaiting_input": "otp",
                        "messages": [AIMessage(content=result["message"])],
                    }
            except Exception as e:
                return {
                    **state,
                    "error_message": str(e),
                    "awaiting_input": "otp",
                    "messages": [
                        AIMessage(content="Verification failed. Please try again.")
                    ],
                }

        def should_send_otp(state: OTPWorkflowState) -> str:
            """Route based on whether we have required details"""
            if state.get("awaiting_input") in ["both", "phone", "fleet"]:
                return END
            if state.get("phone_number") and state.get("fleet_number"):
                return "send_otp"
            return "collect_details"

        def should_verify_otp(state: OTPWorkflowState) -> str:
            """Route based on OTP sending status"""
            if state.get("otp_sent"):
                return END
            elif state.get("error_message"):
                return END
            return END

        def should_continue_verification(state: OTPWorkflowState) -> str:
            """Check if verification is complete"""
            if state.get("verified"):
                return END
            if state.get("awaiting_input") == "otp":
                return END
            return END

        # Build the workflow graph
        workflow = StateGraph(OTPWorkflowState)

        workflow.add_node("collect_details", collect_otp_details)
        workflow.add_node("send_otp", send_otp)
        workflow.add_node("verify_otp", verify_otp)

        workflow.add_edge(START, "collect_details")
        workflow.add_conditional_edges("collect_details", should_send_otp)
        workflow.add_conditional_edges("send_otp", should_verify_otp)
        workflow.add_conditional_edges("verify_otp", should_continue_verification)

        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    def create_booking_workflow(self):
        """Fixed booking workflow"""

        @tool
        def search_routes(origin: str, destination: str, date: str = None) -> dict:
            """Search for available routes"""
            return {
                "routes": [
                    {
                        "id": "R001",
                        "company": "SafariCom Express",
                        "fare": 500,
                        "departure": "08:00",
                    },
                    {
                        "id": "R002",
                        "company": "Nairobi Shuttle",
                        "fare": 450,
                        "departure": "10:00",
                    },
                ],
                "success": True,
            }

        @tool
        def create_booking(route_id: str, passenger_details: dict) -> dict:
            """Create booking"""
            return {
                "booking_id": f"BK{route_id}001",
                "status": "confirmed",
                "payment_required": True,
            }

        def collect_trip_details(state: BookingWorkflowState):
            """Extract trip details"""
            if not state["messages"]:
                return {
                    **state,
                    "awaiting_input": "details",
                    "messages": [
                        AIMessage(
                            content="Please provide your trip details in format: 'Book from [Origin] to [Destination]'"
                        )
                    ],
                }

            message = state["messages"][-1].content.lower()

            origin = state.get("origin")
            destination = state.get("destination")

            # Extract from message
            if "from" in message and "to" in message:
                parts = message.split("from")
                if len(parts) >= 2:
                    sub_parts = parts[1].split("to")
                    if len(sub_parts) >= 2:
                        origin = sub_parts[0].strip()
                        destination = sub_parts[1].strip()

            updates = {
                **state,
                "messages": [],
            }

            if origin:
                updates["origin"] = origin
            if destination:
                updates["destination"] = destination

            if updates.get("origin") and updates.get("destination"):
                updates["awaiting_input"] = None
                return updates
            else:
                updates["awaiting_input"] = "details"
                updates["messages"] = [
                    AIMessage(
                        content="Please provide your trip details in format: 'Book from [Origin] to [Destination]'"
                    )
                ]
                return updates

        def show_available_routes(state: BookingWorkflowState):
            """Show available routes"""
            routes_result = search_routes.invoke(
                {"origin": state["origin"], "destination": state["destination"]}
            )

            if routes_result["success"]:
                routes_text = f"Available routes from {state['origin']} to {state['destination']}:\n\n"
                for idx, route in enumerate(routes_result["routes"], 1):
                    routes_text += f"{idx}. {route['company']} - KSh {route['fare']} (Departs: {route['departure']})\n"
                routes_text += "\nReply with the number or company name to book."

                return {
                    **state,
                    "routes_shown": True,
                    "awaiting_input": "selection",
                    "messages": [AIMessage(content=routes_text)],
                }
            else:
                return {
                    **state,
                    "awaiting_input": None,
                    "messages": [
                        AIMessage(content="No routes found for your destination.")
                    ],
                }

        def process_booking_selection(state: BookingWorkflowState):
            """Handle route selection"""
            if not state["messages"]:
                return {
                    **state,
                    "awaiting_input": "selection",
                    "messages": [AIMessage(content="Please select a route.")],
                }

            selection = state["messages"][-1].content.lower()

            route_id = None
            if "express" in selection or "1" in selection:
                route_id = "R001"
            elif "shuttle" in selection or "2" in selection:
                route_id = "R002"

            if not route_id:
                return {
                    **state,
                    "awaiting_input": "selection",
                    "messages": [
                        AIMessage(
                            content="Please select a valid company from the list."
                        )
                    ],
                }

            booking_result = create_booking.invoke(
                {
                    "route_id": route_id,
                    "passenger_details": {"user_id": state["user_id"]},
                }
            )

            response = (
                f"Booking confirmed! Your booking ID is {booking_result['booking_id']}"
            )
            if booking_result.get("payment_required"):
                response += "\nPayment instructions will be sent shortly."

            return {
                **state,
                "selected_route": route_id,
                "booking_confirmed": True,
                "awaiting_input": None,
                "messages": [AIMessage(content=response)],
            }

        def should_show_routes(state: BookingWorkflowState) -> str:
            if state.get("awaiting_input") == "details":
                return END
            if state.get("origin") and state.get("destination"):
                return "show_routes"
            return "collect_details"

        def should_process_booking(state: BookingWorkflowState) -> str:
            if state.get("booking_confirmed"):
                return END
            if state.get("awaiting_input") == "selection":
                return END
            if state.get("routes_shown"):
                return "process_booking"
            return END

        booking_workflow = StateGraph(BookingWorkflowState)

        booking_workflow.add_node("collect_details", collect_trip_details)
        booking_workflow.add_node("show_routes", show_available_routes)
        booking_workflow.add_node("process_booking", process_booking_selection)

        booking_workflow.add_edge(START, "collect_details")
        booking_workflow.add_conditional_edges("collect_details", should_show_routes)
        booking_workflow.add_conditional_edges("show_routes", should_process_booking)
        booking_workflow.add_conditional_edges(
            "process_booking", should_process_booking
        )

        memory = MemorySaver()
        return booking_workflow.compile(checkpointer=memory)

    def create_transfer_workflow(self):
        """Fixed transfer workflow"""

        @tool
        def validate_fleet(fleet_id: str) -> dict:
            """Validate fleet"""
            return {
                "valid": True,
                "fleet_name": f"Fleet {fleet_id}",
                "status": "active",
            }

        @tool
        def process_transfer(
            source_fleet: str, dest_fleet: str, amount: float, user_id: str
        ) -> dict:
            """Process transfer"""
            return {
                "transaction_id": "TXN123456",
                "status": "success",
                "message": f"KSh {amount} transferred from {source_fleet} to {dest_fleet}",
            }

        def collect_transfer_details(state: TransferWorkflowState):
            """Extract transfer details"""
            if not state["messages"]:
                return {
                    **state,
                    "awaiting_input": "details",
                    "messages": [
                        AIMessage(
                            content="Please use format: 'Transfer [amount] from [source_fleet] to [dest_fleet]'"
                        )
                    ],
                }

            message = state["messages"][-1].content

            pattern = r"transfer\s+(?:ksh\s*)?(\d+)\s+from\s+([a-z]{2}\d+)\s+to\s+([a-z]{2}\d+)"
            match = re.search(pattern, message.lower())

            if match:
                amount = int(match.group(1))
                source_fleet = match.group(2)
                dest_fleet = match.group(3)

                source_valid = validate_fleet.invoke({"fleet_id": source_fleet})
                dest_valid = validate_fleet.invoke({"fleet_id": dest_fleet})

                if source_valid["valid"] and dest_valid["valid"]:
                    return {
                        **state,
                        "amount": amount,
                        "source_fleet": source_fleet,
                        "dest_fleet": dest_fleet,
                        "details_complete": True,
                        "awaiting_input": "confirmation",
                        "messages": [
                            AIMessage(
                                content=f"You want to transfer KSh {amount} from {source_fleet} to {dest_fleet}. Reply 'yes' to confirm."
                            )
                        ],
                    }
                else:
                    return {
                        **state,
                        "error": "Invalid fleet number(s)",
                        "awaiting_input": None,
                        "messages": [
                            AIMessage(
                                content="Invalid fleet number(s). Please check and try again."
                            )
                        ],
                    }
            else:
                return {
                    **state,
                    "awaiting_input": "details",
                    "messages": [
                        AIMessage(
                            content="Please use format: 'Transfer [amount] from [source_fleet] to [dest_fleet]'"
                        )
                    ],
                }

        def execute_transfer(state: TransferWorkflowState):
            """Execute transfer"""
            if not state["messages"]:
                return {
                    **state,
                    "awaiting_input": "confirmation",
                    "messages": [
                        AIMessage(content="Reply 'yes' to confirm the transfer.")
                    ],
                }

            confirmation = state["messages"][-1].content.lower().strip()

            if confirmation in ["yes", "confirm", "proceed", "ok"]:
                result = process_transfer.invoke(
                    {
                        "source_fleet": state["source_fleet"],
                        "dest_fleet": state["dest_fleet"],
                        "amount": state["amount"],
                        "user_id": state["user_id"],
                    }
                )

                return {
                    **state,
                    "transfer_complete": True,
                    "awaiting_input": None,
                    "messages": [AIMessage(content=result["message"])],
                }
            else:
                return {
                    **state,
                    "transfer_complete": False,
                    "awaiting_input": None,
                    "messages": [AIMessage(content="Transfer cancelled.")],
                }

        def should_execute_transfer(state: TransferWorkflowState) -> str:
            if state.get("error"):
                return END
            if state.get("awaiting_input") == "details":
                return END
            if state.get("awaiting_input") == "confirmation":
                return END
            if state.get("details_complete") and not state.get("transfer_complete"):
                return "execute_transfer"
            if state.get("transfer_complete"):
                return END
            return "collect_details"

        def should_complete(state: TransferWorkflowState) -> str:
            if state.get("transfer_complete") or state.get("error"):
                return END
            if state.get("awaiting_input") == "confirmation":
                return END
            return END

        transfer_workflow = StateGraph(TransferWorkflowState)
        transfer_workflow.add_node("collect_details", collect_transfer_details)
        transfer_workflow.add_node("execute_transfer", execute_transfer)

        transfer_workflow.add_edge(START, "collect_details")
        transfer_workflow.add_conditional_edges(
            "collect_details", should_execute_transfer
        )
        transfer_workflow.add_conditional_edges("execute_transfer", should_complete)

        memory = MemorySaver()
        return transfer_workflow.compile(checkpointer=memory)

    def create_route_inquiry_workflow(self):
        """Simple route inquiry - usually one-shot"""

        @tool
        def get_route_information(query: str) -> dict:
            """Get route information"""
            return {
                "routes": [
                    {
                        "route_name": "Nairobi-Mombasa Highway",
                        "fare_ranges": {"economy": "800-1200", "business": "1500-2000"},
                        "companies": ["Modern Coast", "Guardian Coach"],
                        "travel_time": "8-10 hours",
                    }
                ],
                "success": True,
            }

        def process_route_query(state: dict):
            """Process route query"""
            message = state["messages"][-1].content.lower()

            route_info = get_route_information.invoke({"query": message})

            if route_info["success"] and route_info["routes"]:
                route = route_info["routes"][0]
                response = (
                    f"Route: {route['route_name']}\n"
                    f"Companies: {', '.join(route['companies'])}\n"
                    f"Travel time: {route['travel_time']}\n"
                    f"Fares: Economy KSh {route['fare_ranges']['economy']}, "
                    f"Business KSh {route['fare_ranges']['business']}"
                )
            else:
                response = "Sorry, I couldn't find information for that route."

            return {
                **state,
                "query_resolved": True,
                "messages": [AIMessage(content=response)],
            }

        route_workflow = StateGraph(dict)
        route_workflow.add_node("process_query", process_route_query)
        route_workflow.add_edge(START, "process_query")
        route_workflow.add_edge("process_query", END)

        memory = MemorySaver()
        return route_workflow.compile(checkpointer=memory)

    def _get_response_by_language(self, language: str, response_key: str) -> str:
        """Multilingual responses"""
        responses = {
            "awaiting_both": {
                "en": "Please provide both your phone number and fleet number.",
                "sw": "Tafadhali toa nambari yako ya simu na nambari ya gari lako.",
            },
            "awaiting_phone_number": {
                "en": "Kindly provide your phone number.",
                "sw": "Tafadhali toa nambari yako ya simu.",
            },
            "awaiting_fleet_number": {
                "en": "Okay, kindly help me with your fleet number.",
                "sw": "Sawa, tafadhali nisaidie na nambari ya gari lako.",
            },
            "otp_sent_success": {
                "en": "An OTP has been sent to your phone number. Please enter it to proceed.",
                "sw": "OTP imetumwa kwa nambari yako ya simu. Tafadhali ingiza ili kuendelea.",
            },
            "otp_failed": {
                "en": "Failed to send OTP. Please try again later.",
                "sw": "Imeshindikana kutuma OTP. Tafadhali jaribu tena baadaye.",
            },
        }
        return responses.get(response_key, {}).get(
            language, responses[response_key]["en"]
        )
