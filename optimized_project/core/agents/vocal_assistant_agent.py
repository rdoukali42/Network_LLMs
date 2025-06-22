"""
VocalAssistantAgent for optimized_project.
This agent's role in the graph is primarily to handle the "initiate_call" and
"process_conversation" (for solution generation) stages.
Actual STT/TTS and interactive chat during a call will be managed by VoiceService
called from the frontend.
"""

from typing import Dict, Any, List, Optional

from .base_agent import BaseAgent
from langfuse import observe # Assuming Langfuse is kept
# VoiceService will be created later and might be injected if this agent needs to trigger TTS/STT itself.
# For now, its run method focuses on data transformation and LLM calls for summarization/solution generation.

class VocalAssistantAgent(BaseAgent):
    """
    Agent specialized in tasks related to voice call interactions, like initiating
    call data or processing conversation summaries to generate solutions.
    """

    def __init__(self, agent_config: Dict[str, Any], tools: Optional[List[Any]] = None):
        """
        Initializes the VocalAssistantAgent.
        Args:
            agent_config: Configuration dictionary for the agent.
            tools: An optional list of Langchain tools (likely none for this agent).
        """
        super().__init__(name="VocalAssistantAgent", agent_config=agent_config, tools=tools)
        # If this agent needed to directly perform STT/TTS (e.g., speaking an alert),
        # an instance of VoiceService would be passed here.
        # self.voice_service = voice_service_instance

    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes tasks related to voice calls based on the specified action.
        Args:
            input_data: A dictionary containing:
                - "action": "initiate_call" or "process_conversation_summary".
                - "ticket_data": (for initiate_call) Information about the ticket.
                - "employee_data": (for initiate_call) Information about the assigned employee.
                - "conversation_summary": (for process_conversation_summary) Text summary of the call.
                - "query": The original user query (can be part of ticket_data).
        Returns:
            A dictionary with the agent's output.
        """
        action = input_data.get("action", "unknown_action")
        # print(f"🎤 VocalAssistantAgent received action: {action}")

        if not self.llm and action == "process_conversation_summary": # LLM needed for this action
             return {
                "agent": self.name, "status": "error", "error": "LLM not configured for VocalAssistantAgent",
                "result": "VocalAssistantAgent LLM not available for processing conversation."
            }

        try:
            if action == "initiate_call":
                ticket_data = input_data.get("ticket_data", {})
                employee_data = input_data.get("employee_data", {})

                # This agent's role is to prepare information that the system (workflow)
                # will pass to the frontend, which then uses VoiceService for actual call UI.
                call_info_for_ui = {
                    "ticket_id": ticket_data.get("id", "N/A"),
                    "ticket_subject": ticket_data.get("subject", "N/A"),
                    "employee_name": employee_data.get("full_name", "Assigned Expert"),
                    "employee_username": employee_data.get("username", "N/A"),
                    # employee_data itself might be useful for the VoiceService later
                    "employee_data_snapshot": employee_data,
                    "ticket_data_snapshot": ticket_data,
                    # status could be set by UI or db: "pending_ui_notification"
                }

                return {
                    "agent": self.name,
                    "status": "success", # Changed from "call_initiated" to generic success
                    "action_result": "call_data_prepared", # More specific result
                    "call_info_for_ui": call_info_for_ui,
                    "result": f"Call data prepared for {employee_data.get('full_name', 'expert')} regarding ticket {ticket_data.get('id', 'N/A')}."
                }

            elif action == "process_conversation_summary":
                # This action is if the agent needs to generate a solution/summary from text.
                # The actual interactive conversation (STT->LLM->TTS loop) would be handled by
                # VoiceService + frontend. This agent might be called *after* a call to summarize.
                conversation_summary = input_data.get("conversation_summary", "")
                ticket_data = input_data.get("ticket_data", {}) # For context
                employee_data = input_data.get("employee_data", {}) # For context

                if not conversation_summary:
                    return {"agent": self.name, "status": "error", "error": "No conversation summary provided.", "result": ""}

                prompt = f"""
Based on the following conversation summary between a user and an employee ({employee_data.get('full_name', 'Support Expert')})
regarding ticket '{ticket_data.get('subject', 'Support Request')}', please generate a concise solution or summary of the resolution.

Conversation Summary:
{conversation_summary}

Task:
Extract the key problem, steps taken, and the final resolution.
If no clear resolution, summarize the current status.
Present this as a professional summary suitable for internal notes or as a basis for a customer update.
"""
                response_obj = self.llm.invoke(f"{self.get_system_prompt(action)}\n\n{prompt}")
                solution_text = response_obj.content

                return {
                    "agent": self.name,
                    "status": "success",
                    "action_result": "solution_generated_from_summary",
                    "generated_solution": solution_text,
                    "result": "Solution/summary generated from conversation."
                }

            else:
                return {
                    "agent": self.name, "status": "error", "error": f"Unknown action: {action}",
                    "result": f"VocalAssistantAgent cannot handle action: {action}"
                }

        except Exception as e:
            print(f"Error in VocalAssistantAgent run (action: {action}): {e}")
            import traceback
            traceback.print_exc()
            return {
                "agent": self.name, "status": "error", "error": str(e),
                "result": f"VocalAssistantAgent failed during action {action}."
            }

    def get_system_prompt(self, stage: Optional[str] = None) -> str:
        common_intro = "You are an AI assistant helping with tasks related to voice support calls."
        if stage == "initiate_call": # This stage is mostly data prep now, no LLM call here.
            return f"{common_intro} Your current task is to prepare data for initiating a voice call notification."
        elif stage == "process_conversation_summary":
            return f"{common_intro} Your current task is to analyze a conversation summary and extract or generate a ticket solution."

        return f"""{common_intro}
You assist in a support system by handling tasks related to voice interactions.
- For 'initiate_call', you prepare data needed by the system to notify an employee.
- For 'process_conversation_summary', you analyze text summaries of calls to produce solutions or updates.
"""

# Note: The detailed STT/TTS methods (transcribe_audio, process_voice_input with full STT/LLM/TTS loop)
# and the embedded CloudTTS/GeminiChat classes from the original src/agents/vocal_assistant.py
# will be refactored into `optimized_project/core/services/voice_service.py`.
# This agent now focuses on its role within the AISystem graph.
