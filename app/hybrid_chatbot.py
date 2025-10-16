"""
Main hybrid chatbot implementation combining PyTorch and LangGraph.
"""

import logging
import torch


from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage

# Imports (adjust based on your project structure)
from app.chatbot import ChatBot  # Your existing PyTorch chatbot
from utils.memory import PersistentMemoryManager
from utils.language import detect_language, MultilingualResponses
from utils.nltk_utils import tokenize, bag_of_words
from services.account_service import AccountService
from services.route_service import RouteService
from services.transfer_service import TransferService
from langgraph.checkpoint.memory import InMemorySaver

logger = logging.getLogger(__name__)


class HybridChatBot:
    """
    Production-ready hybrid chatbot combining PyTorch intent classification
    with LangGraph workflows for complex multi-turn conversations.
    """

    def __init__(
        self,
        model_path: str,
        intents_path: str,
        memory_manager: "PersistentMemoryManager",
        account_service: "AccountService",
        route_service: "RouteService",
        transfer_service: "TransferService",
        config: Dict[str, Any],
        bot_name: str = "Sam",
    ):
        """
        Initialize hybrid chatbot.

        Args:
            model_path: Path to trained PyTorch model
            intents_path: Path to intents JSON
            memory_manager: Persistent memory manager
            account_service: Account/OTP service
            route_service: Route information service
            transfer_service: Transfer service
            config: Configuration dictionary
            bot_name: Bot name for responses
        """
        self.bot_name = bot_name
        self.config = config
        self.memory_manager = memory_manager

        # Initialize services
        self.account_service = account_service
        self.route_service = route_service
        self.transfer_service = transfer_service

        # Load PyTorch model (implement based on your existing chatbot.py)
        self.pytorch_model = ChatBot(model_path, intents_path, bot_name="Hybrid Bot")

        # Initialize workflows
        self._init_workflows()

        logger.info("Hybrid chatbot initialized successfully")

    def _init_workflows(self):
        """Initialize all workflow graphs and ensure a proper checkpointer instance is used."""
        # Create a single checkpointer instance for all workflows (do NOT use `with`)
        self.checkpointer = InMemorySaver()

        # Import workflow factory functions
        from workflows.otp_workflow import create_otp_workflow
        from workflows.booking_workflow import create_booking_workflow
        from workflows.transfer_workflow import create_transfer_workflow
        from workflows.route_workflow import create_route_workflow

        # Pass the SAME checkpointer instance to each workflow
        self.workflows = {
            "otp": create_otp_workflow(
                self.account_service, checkpointer=self.checkpointer
            ),
            "booking": create_booking_workflow(
                self.route_service, checkpointer=self.checkpointer
            ),
            "transfer": create_transfer_workflow(
                self.transfer_service,
                self.account_service,
                checkpointer=self.checkpointer,
            ),
            "route": create_route_workflow(
                self.route_service, checkpointer=self.checkpointer
            ),
        }

    def process_message(self, user_id: str, message: str) -> Dict[str, str]:
        """
        Process incoming message with hybrid approach.

        Args:
            user_id: Unique user identifier
            message: User's message

        Returns:
            Dictionary with bot response
        """
        try:
            # Check for active workflow
            active_workflow = self.memory_manager.get_workflow_state(user_id)

            if active_workflow:
                response = self._continue_workflow(user_id, message, active_workflow)
            else:
                # Classify intent with PyTorch
                intent, confidence = self._classify_intent(message)

                logger.info(
                    f"User {user_id}: Intent={intent}, Confidence={confidence:.2f}"
                )

                # Route to workflow or direct response
                threshold = self.config.get("confidence_threshold", 0.75)
                if confidence > threshold:
                    response = self._route_to_workflow(user_id, message, intent)
                else:
                    response = self._handle_low_confidence(message)

            # Save conversation
            self.memory_manager.save_conversation(
                user_id=user_id, message=message, response=response[self.bot_name]
            )

            return response

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return {self.bot_name: "I encountered an error. Please try again."}

    def _classify_intent(self, message: str) -> tuple[str, float]:
        """
        Classify intent using the PyTorch model from ChatBot.

        Args:
            message (str): User's input text.

        Returns:
            tuple: (intent_tag, confidence_score)
        """

        try:
            # Access the loaded model and metadata
            model = self.pytorch_model.model
            all_words = self.pytorch_model.all_words
            tags = self.pytorch_model.tags
            device = self.pytorch_model.device

            # Tokenize and create bag of words
            sentence = tokenize(message)
            X = bag_of_words(sentence, all_words)
            X = X.reshape(1, X.shape[0])
            X = torch.from_numpy(X).to(device)

            # Get model output
            model.eval()
            with torch.no_grad():
                output = model(X)
                _, predicted = torch.max(output, dim=1)
                probs = torch.softmax(output, dim=1)
                confidence = probs[0][predicted.item()].item()
                intent = tags[predicted.item()]

            return intent, confidence

        except Exception as e:
            logger.error(f"Error classifying intent: {e}", exc_info=True)
            # Return a neutral fallback
            return "unknown", 0.0

    def _route_to_workflow(
        self, user_id: str, message: str, intent: str
    ) -> Dict[str, str]:
        """Route message to appropriate workflow based on intent."""

        # Map intents to workflows
        workflow_mapping = {
            "otp_request_en": "otp",
            "otp_request_sw": "otp",
            "verify_otp": "otp",
            "booking_request_en": "booking",
            "booking_request_sw": "booking",
            "transfer_request": "transfer",
            "route_inquiry": "route",
            "fare_inquiry": "route",
        }

        workflow_type = workflow_mapping.get(intent)

        if workflow_type:
            return self._start_workflow(user_id, message, workflow_type)
        else:
            # Handle with simple response
            return self._get_simple_response(intent)

    def _start_workflow(
        self, user_id: str, message: str, workflow_type: str
    ) -> Dict[str, str]:
        """Start a new workflow."""

        language = detect_language(message)

        # Create initial state based on workflow type
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "language": language,
            "awaiting_input": None,
            "error": None,
        }

        # Add workflow-specific initial state
        if workflow_type == "otp":
            initial_state.update(
                {
                    "phone_number": None,
                    "fleet_number": None,
                    "otp_sent": False,
                    "verified": False,
                }
            )
        elif workflow_type == "booking":
            initial_state.update(
                {
                    "origin": None,
                    "destination": None,
                    "travel_date": None,
                    "selected_route": None,
                    "passenger_count": 1,
                    "routes_shown": False,
                    "booking_confirmed": False,
                }
            )
        elif workflow_type == "transfer":
            initial_state.update(
                {
                    "amount": None,
                    "source_fleet": None,
                    "dest_fleet": None,
                    "details_complete": False,
                    "transfer_complete": False,
                }
            )
        elif workflow_type == "route":
            initial_state.update({"query_resolved": False})

        # Create config for checkpointing
        config = {"configurable": {"thread_id": f"{workflow_type}_{user_id}"}}

        try:
            # Invoke workflow
            result = self.workflows[workflow_type].invoke(initial_state, config)

            # Save workflow state if not complete
            if not self._is_workflow_complete(result, workflow_type):
                timeout = self.config.get(f"{workflow_type}_timeout", 300)
                self.memory_manager.save_workflow_state(
                    user_id=user_id,
                    workflow_type=workflow_type,
                    state={"config": config, "result": result},
                    timeout=timeout,
                )

            return self._format_response(result)

        except Exception as e:
            logger.error(f"Workflow error: {e}", exc_info=True)
            return {
                self.bot_name: MultilingualResponses.get("general", "error", language)
            }

    def _continue_workflow(
        self, user_id: str, message: str, active_workflow: Dict[str, Any]
    ) -> Dict[str, str]:
        """Continue existing workflow with new user input."""

        workflow_type = active_workflow["workflow_type"]
        saved_state = active_workflow["state"]
        config = saved_state["config"]
        previous_result = saved_state["result"]

        # Create new state with user message
        new_state = {**previous_result, "messages": [HumanMessage(content=message)]}

        try:
            # Continue workflow
            result = self.workflows[workflow_type].invoke(new_state, config)

            # Check if workflow is complete
            if self._is_workflow_complete(result, workflow_type):
                self.memory_manager.delete_workflow_state(user_id)
                logger.info(f"Workflow {workflow_type} completed for user {user_id}")
            else:
                # Update saved state
                timeout = self.config.get(f"{workflow_type}_timeout", 300)
                self.memory_manager.save_workflow_state(
                    user_id=user_id,
                    workflow_type=workflow_type,
                    state={"config": config, "result": result},
                    timeout=timeout,
                )

            return self._format_response(result)

        except Exception as e:
            logger.error(f"Workflow continuation error: {e}", exc_info=True)
            self.memory_manager.delete_workflow_state(user_id)
            return {self.bot_name: "An error occurred. Please start over."}

    def _is_workflow_complete(self, result: Dict[str, Any], workflow_type: str) -> bool:
        """Check if workflow is complete."""
        completion_flags = {
            "otp": result.get("verified", False),
            "booking": result.get("booking_confirmed", False),
            "transfer": result.get("transfer_complete", False) or result.get("error"),
            "route": result.get("query_resolved", False),
        }
        return completion_flags.get(workflow_type, False)

    def _format_response(self, workflow_result: Dict[str, Any]) -> Dict[str, str]:
        """Format workflow response for output."""
        ai_messages = [
            msg
            for msg in workflow_result.get("messages", [])
            if isinstance(msg, AIMessage)
        ]

        if ai_messages:
            return {self.bot_name: ai_messages[-1].content}

        return {self.bot_name: "Processing your request..."}

    def _handle_low_confidence(self, message: str) -> Dict[str, str]:
        """Handle messages with low confidence classification."""
        language = detect_language(message)

        fallback_responses = {
            "en": "I'm not sure I understood that. Could you please rephrase? "
            "I can help with: OTP verification, booking tickets, transfers, or route information.",
            "sw": "Sijaeleweka vizuri. Tafadhali sema tena? "
            "Ninaweza kusaidia na: Uthibitishaji wa OTP, kuhifadhi tiketi, uhamishaji, au taarifa za njia.",
        }

        return {
            self.bot_name: fallback_responses.get(language, fallback_responses["en"])
        }

    def _get_simple_response(self, intent: str) -> Dict[str, str]:
        """Get simple response for non-workflow intents."""
        # Implement based on your intents.json
        # This is a placeholder
        responses = {
            "greeting_en": "Hello! How can I help you today?",
            "greeting_sw": "Habari! Ninaweza kukusaidiaje?",
            "goodbye_en": "Goodbye! Have a great day!",
            "goodbye_sw": "Kwaheri! Siku njema!",
        }
        return {self.bot_name: responses.get(intent, "I'm here to help!")}

    def clear_user_session(self, user_id: str) -> bool:
        """Clear user's active workflow session."""
        try:
            self.memory_manager.delete_workflow_state(user_id)
            logger.info(f"Cleared session for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False

    def get_conversation_history(self, user_id: str, limit: int = 10) -> list:
        """Get user's conversation history."""
        return self.memory_manager.get_conversation_history(user_id, limit)
