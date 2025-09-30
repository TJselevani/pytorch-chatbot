# integration_example.py
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.pregel.main import Interrupt
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
import operator

# Import your existing components
from app.chatbot import ChatBot
from utils.extractors import extract_phone_number, extract_fleet_number
from utils.services import account_service
from utils.services.account_service import AccountService
from utils.match import detect_language
from utils.nltk_utils import tokenize, bag_of_words
import torch


class OTPWorkflowState(TypedDict):
    messages: Annotated[list, operator.add]
    user_id: str
    phone_number: str | None
    fleet_number: str | None
    language: str
    otp_sent: bool
    verified: bool
    error_message: str | None


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


class WorkflowManager:
    def __init__(self, account_service: AccountService):
        self.account_service = account_service

    def create_otp_workflow(self):
        """Enhanced OTP workflow using your existing components"""

        def collect_otp_details(state: OTPWorkflowState):
            """Collect phone and fleet number using your extractors"""
            latest_message = state["messages"][-1].content

            # Use your existing extractors
            phone = extract_phone_number(latest_message) or state.get("phone_number")
            fleet = extract_fleet_number(latest_message) or state.get("fleet_number")

            # Update state with extracted info
            updates = {}
            if phone:
                updates["phone_number"] = phone
            if fleet:
                updates["fleet_number"] = fleet

            current_phone = phone
            current_fleet = fleet

            # If both missing, interrupt and wait for user input
            if not current_phone and not current_fleet:
                # Interrupt and prompt user to provide both details
                phone_input = Interrupt("Please provide your phone number.")
                fleet_input = Interrupt("Please provide your fleet number.")
                return {
                    **state,
                    **updates,
                    "phone_number": phone_input,
                    "fleet_number": fleet_input,
                    "messages": [],
                }
            elif not current_phone:
                phone_input = Interrupt("Kindly provide your phone number.")
                return {
                    **state,
                    **updates,
                    "phone_number": phone_input,
                    "messages": [],
                }
            elif not current_fleet:
                fleet_input = Interrupt("Kindly provide your fleet number.")
                return {
                    **state,
                    **updates,
                    "fleet_number": fleet_input,
                    "messages": [],
                }
            else:
                # All required info collected, proceed without interruption
                return {
                    **state,
                    **updates,
                    "messages": [],  # Will be handled by send_otp
                }

        def send_otp(state: OTPWorkflowState):
            """Send OTP using your AccountService"""
            phone = state["phone_number"]

            try:
                # Use your existing service
                result = self.account_service.send_otp(phone)

                # resp.json() from httpbin will include your payload under "json" so you can inspect it
                # print(
                #     "Echoed payload:", result.get("provider_response", {}).get("json")
                # )

                if result.get("status") == "success":
                    response = self._get_response_by_language(
                        state["language"], "otp_sent_success"
                    )
                    return {
                        **state,
                        "otp_sent": True,
                        "messages": [AIMessage(content=response)],
                    }
                else:
                    response = self._get_response_by_language(
                        state["language"], "otp_failed"
                    )
                    return {
                        **state,
                        "error_message": result.get("message", "Unknown error"),
                        "messages": [AIMessage(content=response)],
                    }
            except Exception as e:
                response = self._get_response_by_language(
                    state["language"], "otp_failed"
                )
                return {
                    **state,
                    "error_message": str(e),
                    "messages": [AIMessage(content=response)],
                }

        def verify_otp(state: OTPWorkflowState):
            """Verify OTP using your AccountService"""
            latest_message = state["messages"][-1].content
            otp_code = latest_message.strip()
            phone = state["phone_number"]

            try:
                result = self.account_service.verify_otp(phone, otp_code)

                return {
                    **state,
                    "verified": result.get("status") == "success",
                    "messages": [AIMessage(content=result["message"])],
                }
            except Exception as e:
                return {
                    **state,
                    "error_message": str(e),
                    "messages": [
                        AIMessage(content="Verification failed. Please try again.")
                    ],
                }

        def should_send_otp(state: OTPWorkflowState) -> str:
            """Route based on whether we have required details"""
            if state.get("phone_number") and state.get("fleet_number"):
                return "send_otp"
            return "collect_details"

        def should_verify_otp(state: OTPWorkflowState) -> str:
            """Route based on OTP sending status"""
            if state.get("otp_sent"):
                return "verify_otp"
            elif state.get("error_message"):
                return "collect_details"  # Retry
            return END

        def is_verification_complete(state: OTPWorkflowState) -> str:
            """Check if verification is complete"""
            if state.get("verified"):
                return END
            return "verify_otp"  # Keep trying

        # Build the workflow graph
        workflow = StateGraph(OTPWorkflowState)

        # Add nodes
        workflow.add_node("collect_details", collect_otp_details)
        workflow.add_node("send_otp", send_otp)
        workflow.add_node("verify_otp", verify_otp)

        # Add edges
        workflow.add_edge(START, "collect_details")
        workflow.add_conditional_edges("collect_details", should_send_otp)
        workflow.add_conditional_edges("send_otp", should_verify_otp)
        workflow.add_conditional_edges("verify_otp", is_verification_complete)

        return workflow.compile()

    def create_booking_workflow(self):
        """Booking workflow for travel reservations"""

        @tool
        def search_routes(origin: str, destination: str, date: str = None) -> dict:
            """Search for available routes - replace with your actual API"""
            # Your route search API call here
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
            """Create booking - replace with your actual booking API"""
            # Your booking API call here
            return {
                "booking_id": f"BK{route_id}001",
                "status": "confirmed",
                "payment_required": True,
            }

        def collect_trip_details(state: BookingWorkflowState):
            """Extract trip details from user message"""
            message = state["messages"][-1].content.lower()

            # Simple extraction - you can enhance this with NLP
            if "from" in message and "to" in message:
                parts = message.split("from")[1].split("to")
                if len(parts) >= 2:
                    origin = parts[0].strip()
                    destination = parts[1].strip()

                    return {
                        **state,
                        "origin": origin,
                        "destination": destination,
                        "messages": [],
                    }

            # Ask for missing details
            response = "Please provide your trip details in format: 'Book from [Origin] to [Destination]'"
            return {**state, "messages": [AIMessage(content=response)]}

        def show_available_routes(state: BookingWorkflowState):
            """Show available routes using the search tool"""
            routes_result = search_routes.invoke(
                {"origin": state["origin"], "destination": state["destination"]}
            )

            if routes_result["success"]:
                routes_text = f"Available routes from {state['origin']} to {state['destination']}:\n\n"
                for route in routes_result["routes"]:
                    routes_text += f"• {route['company']} - KSh {route['fare']} (Departs: {route['departure']})\n"
                routes_text += "\nReply with the company name to book."

                return {
                    **state,
                    "routes_shown": True,
                    "messages": [AIMessage(content=routes_text)],
                }
            else:
                return {
                    **state,
                    "messages": [
                        AIMessage(content="No routes found for your destination.")
                    ],
                }

        def process_booking_selection(state: BookingWorkflowState):
            """Handle route selection and booking"""
            selection = state["messages"][-1].content.lower()

            # Match selection to available routes (simplified)
            if "express" in selection:
                route_id = "R001"
            elif "shuttle" in selection:
                route_id = "R002"
            else:
                return {
                    **state,
                    "messages": [
                        AIMessage(
                            content="Please select a valid company from the list."
                        )
                    ],
                }

            # Create booking
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
                "messages": [AIMessage(content=response)],
            }

        # Routing functions
        def should_show_routes(state: BookingWorkflowState) -> str:
            if state.get("origin") and state.get("destination"):
                return "show_routes"
            return "collect_details"

        def should_process_booking(state: BookingWorkflowState) -> str:
            if state.get("routes_shown") and not state.get("booking_confirmed"):
                return "process_booking"
            elif state.get("booking_confirmed"):
                return END
            return "show_routes"

        # Build workflow
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

        return booking_workflow.compile()

    def create_route_inquiry_workflow(self):
        """Handle route and fare inquiries with API calls"""

        @tool
        def get_route_information(
            query: str, origin: str = None, destination: str = None
        ) -> dict:
            """Get comprehensive route information"""
            # Your route API call
            return {
                "routes": [
                    {
                        "route_name": "Nairobi-Mombasa Highway",
                        "stages": ["Nairobi", "Machakos", "Voi", "Mombasa"],
                        "fare_ranges": {"economy": "800-1200", "business": "1500-2000"},
                        "companies": ["Modern Coast", "Guardian Coach", "Buscar"],
                        "travel_time": "8-10 hours",
                    }
                ],
                "success": True,
            }

        @tool
        def get_company_details(company_name: str) -> dict:
            """Get specific company information"""
            return {
                "company": company_name,
                "contact": "+254700000000",
                "booking_office": "Tom Mboya Street, Nairobi",
                "fleet_types": ["Standard", "VIP", "Business Class"],
            }

        def process_route_query(state: dict):
            """Process complex route queries"""
            message = state["messages"][-1].content.lower()

            # Extract location mentions (enhance this with NER)
            locations = []
            common_cities = [
                "nairobi",
                "mombasa",
                "kisumu",
                "eldoret",
                "nakuru",
                "machakos",
            ]
            for city in common_cities:
                if city in message:
                    locations.append(city.title())

            # Determine query type
            if any(word in message for word in ["fare", "cost", "price", "how much"]):
                query_type = "fare_inquiry"
            elif any(word in message for word in ["company", "companies", "operator"]):
                query_type = "company_inquiry"
            elif any(word in message for word in ["time", "duration", "how long"]):
                query_type = "time_inquiry"
            else:
                query_type = "general_inquiry"

            # Get route information
            route_info = get_route_information.invoke(
                {
                    "query": message,
                    "origin": locations[0] if locations else None,
                    "destination": locations[1] if len(locations) > 1 else None,
                }
            )

            if route_info["success"]:
                response = self._format_route_response(
                    route_info, query_type, state["language"]
                )
            else:
                response = "Sorry, I couldn't find information for that route."

            return {
                **state,
                "query_resolved": True,
                "messages": [AIMessage(content=response)],
            }

        # Simple workflow for route inquiries
        route_workflow = StateGraph(dict)
        route_workflow.add_node("process_query", process_route_query)
        route_workflow.add_edge(START, "process_query")
        route_workflow.add_edge("process_query", END)

        return route_workflow.compile()

    def create_transfer_workflow(self):
        """Handle money transfer requests between fleets"""

        @tool
        def validate_fleet(fleet_id: str) -> dict:
            """Validate if fleet exists and is active"""
            # Your fleet validation API
            return {
                "valid": True,
                "fleet_name": f"Fleet {fleet_id}",
                "status": "active",
            }

        @tool
        def process_transfer(
            source_fleet: str, dest_fleet: str, amount: float, user_id: str
        ) -> dict:
            """Process the money transfer"""
            # Your transfer API
            return {
                "transaction_id": "TXN123456",
                "status": "success",
                "message": f"KSh {amount} transferred from {source_fleet} to {dest_fleet}",
            }

        def collect_transfer_details(state: dict):
            """Extract transfer details from message"""
            message = state["messages"][-1].content

            # Enhanced pattern matching for transfers
            import re

            # Pattern: Transfer 500 from sm34 to sm45
            pattern = r"transfer\s+(?:ksh\s*)?(\d+)\s+from\s+([a-z]{2}\d+)\s+to\s+([a-z]{2}\d+)"
            match = re.search(pattern, message.lower())

            if match:
                amount = int(match.group(1))
                source_fleet = match.group(2)
                dest_fleet = match.group(3)

                # Validate both fleets
                source_valid = validate_fleet.invoke({"fleet_id": source_fleet})
                dest_valid = validate_fleet.invoke({"fleet_id": dest_fleet})

                if source_valid["valid"] and dest_valid["valid"]:
                    return {
                        **state,
                        "amount": amount,
                        "source_fleet": source_fleet,
                        "dest_fleet": dest_fleet,
                        "details_complete": True,
                        "messages": [],
                    }
                else:
                    error_msg = "Invalid fleet number(s). Please check and try again."
                    return {
                        **state,
                        "error": error_msg,
                        "messages": [AIMessage(content=error_msg)],
                    }
            else:
                help_msg = "Please use format: 'Transfer [amount] from [source_fleet] to [dest_fleet]'"
                return {**state, "messages": [AIMessage(content=help_msg)]}

        def execute_transfer(state: dict):
            """Execute the validated transfer"""
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
                "transaction_id": result["transaction_id"],
                "messages": [AIMessage(content=result["message"])],
            }

        def should_execute_transfer(state: dict) -> str:
            if state.get("details_complete") and not state.get("error"):
                return "execute_transfer"
            elif state.get("transfer_complete"):
                return END
            return "collect_details"

        # Build transfer workflow
        transfer_workflow = StateGraph(dict)
        transfer_workflow.add_node("collect_details", collect_transfer_details)
        transfer_workflow.add_node("execute_transfer", execute_transfer)

        transfer_workflow.add_edge(START, "collect_details")
        transfer_workflow.add_conditional_edges(
            "collect_details", should_execute_transfer
        )
        transfer_workflow.add_edge("execute_transfer", END)

        return transfer_workflow.compile()

    def _format_route_response(
        self, route_info: dict, query_type: str, language: str
    ) -> str:
        """Format route information based on query type"""
        routes = route_info["routes"]
        if not routes:
            return "No routes found."

        route = routes[0]  # Take first route for simplicity

        if query_type == "fare_inquiry":
            return (
                f"Fare for {route['route_name']}:\n"
                + f"Economy: KSh {route['fare_ranges']['economy']}\n"
                + f"Business: KSh {route['fare_ranges']['business']}"
            )
        elif query_type == "company_inquiry":
            companies = ", ".join(route["companies"])
            return f"Companies operating on {route['route_name']}: {companies}"
        elif query_type == "time_inquiry":
            return f"Travel time on {route['route_name']}: {route['travel_time']}"
        else:
            # General inquiry - return comprehensive info
            stages = " → ".join(route["stages"])
            companies = ", ".join(route["companies"])
            return (
                f"Route: {route['route_name']}\n"
                + f"Stages: {stages}\n"
                + f"Companies: {companies}\n"
                + f"Travel time: {route['travel_time']}\n"
                + f"Fares: Economy KSh {route['fare_ranges']['economy']}, "
                + f"Business KSh {route['fare_ranges']['business']}"
            )

    def _get_response_by_language(self, language: str, response_key: str) -> str:
        """Use your existing multilingual response system"""
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


# Modified ChatBot integration
class HybridChatBotIntegration(ChatBot):
    def __init__(self, file_path, bot_name="Sam"):
        super().__init__(file_path, bot_name)

        # Initialize workflow manager with your existing service
        self.workflow_manager = WorkflowManager(account_service)

        # Create workflows
        self.otp_workflow = self.workflow_manager.create_otp_workflow()
        self.booking_workflow = self.workflow_manager.create_booking_workflow()
        self.route_workflow = self.workflow_manager.create_route_inquiry_workflow()
        self.transfer_workflow = self.workflow_manager.create_transfer_workflow()

        # Track active workflows
        self.active_workflows = {}

    def process_message(self, user_id, message):
        """Enhanced process_message with workflow support"""
        print(f"{user_id},  {message}")

        # Check for active workflows first
        if user_id in self.active_workflows:
            return self._continue_workflow(user_id, message)

        # Use your existing PyTorch classification
        result = super().process_message(user_id, message)

        # Extract the intent from your existing logic
        sentence = tokenize(message)
        X = bag_of_words(sentence, self.all_words)
        X = X.reshape(1, X.shape[0])
        X = torch.from_numpy(X).to(self.device)
        output = self.model(X)
        _, predicted = torch.max(output, dim=1)
        tag = self.tags[predicted.item()]
        probs = torch.softmax(output, dim=1)
        prob = probs[0][predicted.item()]

        # Route high-confidence complex intents to workflows
        if prob.item() > 0.8:
            if tag in ["otp_request_en", "otp_request_sw"]:
                return self._start_otp_workflow(user_id, message)
            elif tag in ["booking_request_en", "booking_request_sw"]:
                return self._start_booking_workflow(user_id, message)
            elif tag in ["transfer_request"]:
                return self._start_transfer_workflow(user_id, message)
            elif "route" in tag.lower() or "travel" in tag.lower():
                return self._start_route_workflow(user_id, message)

        # Return the PyTorch result for other intents
        return result

    def _start_otp_workflow(self, user_id, message):
        """Start OTP workflow"""
        language = detect_language(message)

        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "phone_number": None,
            "fleet_number": None,
            "language": language,
            "otp_sent": False,
            "verified": False,
            "error_message": None,
        }

        result = self.otp_workflow.invoke(initial_state)

        if not result.get("verified"):
            self.active_workflows[user_id] = {"type": "otp", "state": result}

        return self._format_response(result)

    def _start_route_workflow(self, user_id, message):
        """Start route inquiry workflow"""
        language = detect_language(message)

        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "language": language,
            "query_resolved": False,
        }

        result = self.route_workflow.invoke(initial_state)
        return self._format_response(result)

    def _start_transfer_workflow(self, user_id, message):
        """Start transfer workflow"""
        language = detect_language(message)

        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "language": language,
            "amount": None,
            "source_fleet": None,
            "dest_fleet": None,
            "details_complete": False,
            "transfer_complete": False,
            "error": None,
        }

        result = self.transfer_workflow.invoke(initial_state)

        if not result.get("transfer_complete") and not result.get("error"):
            self.active_workflows[user_id] = {"type": "transfer", "state": result}

        return self._format_response(result)

    def _start_booking_workflow(self, user_id, message):
        """Start booking workflow"""
        language = detect_language(message)

        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "origin": None,
            "destination": None,
            "travel_date": None,
            "selected_route": None,
            "passenger_count": 1,
            "language": language,
            "routes_shown": False,
            "booking_confirmed": False,
        }

        result = self.booking_workflow.invoke(initial_state)

        if not result.get("booking_confirmed"):
            self.active_workflows[user_id] = {"type": "booking", "state": result}

        return self._format_response(result)

    def _continue_workflow(self, user_id, message):
        """Continue existing workflow"""
        active = self.active_workflows[user_id]
        workflow_type = active["type"]
        current_state = active["state"]

        # Add new message
        updated_state = {
            **current_state,
            "messages": current_state["messages"] + [HumanMessage(content=message)],
        }

        # Run appropriate workflow
        if workflow_type == "otp":
            result = self.otp_workflow.invoke(updated_state)
            if result.get("verified"):
                del self.active_workflows[user_id]
            else:
                self.active_workflows[user_id]["state"] = result
        elif workflow_type == "booking":
            result = self.booking_workflow.invoke(updated_state)
            if result.get("booking_confirmed"):
                del self.active_workflows[user_id]
            else:
                self.active_workflows[user_id]["state"] = result
        elif workflow_type == "transfer":
            result = self.transfer_workflow.invoke(updated_state)
            if result.get("transfer_complete") or result.get("error"):
                del self.active_workflows[user_id]
            else:
                self.active_workflows[user_id]["state"] = result

        return self._format_response(result)

    def _format_response(self, workflow_result):
        """Format workflow response to match your existing format"""
        ai_messages = [
            msg
            for msg in workflow_result.get("messages", [])
            if isinstance(msg, AIMessage)
        ]

        if ai_messages:
            return {self.bot_name: ai_messages[-1].content}
        return {self.bot_name: "Processing your request..."}
