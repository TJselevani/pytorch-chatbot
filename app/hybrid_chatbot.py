import torch
from app.chatbot import ChatBot
from utils.services import account_service
from langchain_core.messages import HumanMessage, AIMessage
from utils.match import detect_language
from utils.nltk_utils import tokenize, bag_of_words
from utils.workflow import WorkflowManager


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

        # Track active workflows with their configuration
        self.active_workflows = {}

    def process_message(self, user_id, message):
        """Enhanced process_message with workflow support"""
        print(f"{user_id},  {message}")

        # Check for active workflows first
        if user_id in self.active_workflows:
            return self._continue_workflow(user_id, message)

        # Use your existing PyTorch classification
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
        if prob.item() > 0.75:
            if tag in ["otp_request_en", "otp_request_sw"]:
                return self._start_otp_workflow(user_id, message)
            elif tag in ["booking_request_en", "booking_request_sw"]:
                return self._start_booking_workflow(user_id, message)
            elif "transfer" in tag.lower():
                return self._start_transfer_workflow(user_id, message)
            elif "route" in tag.lower() or "travel" in tag.lower():
                return self._start_route_workflow(user_id, message)

        # Return the PyTorch result for other intents
        return super().process_message(user_id, message)

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
            "awaiting_input": None,
        }

        # Create config with thread_id for checkpointing
        config = {"configurable": {"thread_id": f"otp_{user_id}"}}

        result = self.otp_workflow.invoke(initial_state, config)

        # Store workflow info if not complete
        if not result.get("verified"):
            self.active_workflows[user_id] = {
                "type": "otp",
                "config": config,
                "state": result,
            }

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

        config = {"configurable": {"thread_id": f"booking_{user_id}"}}
        result = self.booking_workflow.invoke(initial_state, config)

        if not result.get("booking_confirmed"):
            self.active_workflows[user_id] = {
                "type": "booking",
                "config": config,
                "state": result,
            }

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

        config = {"configurable": {"thread_id": f"transfer_{user_id}"}}
        result = self.transfer_workflow.invoke(initial_state, config)

        if not result.get("transfer_complete") and not result.get("error"):
            self.active_workflows[user_id] = {
                "type": "transfer",
                "config": config,
                "state": result,
            }

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

        config = {"configurable": {"thread_id": f"route_{user_id}"}}
        result = self.route_workflow.invoke(initial_state, config)

        # Route inquiries are typically one-shot, so we don't store them
        return self._format_response(result)

    def _continue_workflow(self, user_id, message):
        """Continue existing workflow with new user input"""
        active = self.active_workflows[user_id]
        workflow_type = active["type"]
        config = active["config"]
        current_state = active["state"]

        # Prepare new state with updated messages
        # We need to append the new message to the existing state
        new_state = {
            **current_state,
            "messages": [HumanMessage(content=message)],  # New message only
        }

        # Run appropriate workflow with the same config (for checkpointing)
        if workflow_type == "otp":
            result = self.otp_workflow.invoke(new_state, config)

            # Check if workflow is complete
            if result.get("verified") or not result.get("awaiting_input"):
                del self.active_workflows[user_id]
            else:
                self.active_workflows[user_id]["state"] = result

        elif workflow_type == "booking":
            result = self.booking_workflow.invoke(new_state, config)

            if result.get("booking_confirmed"):
                del self.active_workflows[user_id]
            else:
                self.active_workflows[user_id]["state"] = result

        elif workflow_type == "transfer":
            result = self.transfer_workflow.invoke(new_state, config)

            if result.get("transfer_complete") or result.get("error"):
                del self.active_workflows[user_id]
            else:
                self.active_workflows[user_id]["state"] = result
        else:
            # Unknown workflow type
            del self.active_workflows[user_id]
            return {self.bot_name: "Sorry, something went wrong. Please start over."}

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

    def clear_workflow(self, user_id):
        """Manually clear a user's active workflow (useful for debugging/reset)"""
        if user_id in self.active_workflows:
            del self.active_workflows[user_id]
            return True
        return False
