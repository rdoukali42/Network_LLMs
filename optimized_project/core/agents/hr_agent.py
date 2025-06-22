"""
HRAgent - Employee matching and assignment agent with Pydantic validation for optimized_project.
"""

from typing import Dict, Any, List, Optional
from pydantic import ValidationError
import time
import json
import re
# datetime is part of HRTicketRequest model default factory

from langchain.agents import AgentExecutor, create_tool_calling_agent # If tools were to be used
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate # If agent_executor is used
from langfuse import observe

from .base_agent import BaseAgent
from ..models.hr_models import ( # Relative import from ../models/
    HRTicketRequest,
    HREmployeeMatch,
    HRTicketResponse,
    HRAssignmentResponse,
    HRErrorResponse,
    HRSystemStatus
)
# AvailabilityTool will be injected
# from ..tools.availability_tool import AvailabilityTool

class HRAgent(BaseAgent):
    """
    Agent specialized in finding the best employee to handle tickets.
    Uses an AvailabilityTool to get employee status and an LLM for matching logic.
    """

    def __init__(self, agent_config: Dict[str, Any],
                 availability_tool_instance: Any, # Should be an instance of AvailabilityTool
                 tools: Optional[List[BaseTool]] = None): # HRAgent in original didn't seem to use generic tools
        """
        Initializes the HRAgent.
        Args:
            agent_config: Configuration dictionary for the agent.
            availability_tool_instance: An instance of AvailabilityTool.
            tools: An optional list of Langchain tools (currently not used by HRAgent's core logic).
        """
        super().__init__(name="HRAgent", agent_config=agent_config, tools=tools)
        self.availability_tool = availability_tool_instance

        # HRAgent's primary logic is LLM-driven based on a detailed prompt,
        # not typically requiring a ReAct style agent_executor unless it needs to use other tools.
        # If it were to use tools, the executor would be set up here.
        self.agent_executor: Optional[AgentExecutor] = None
        if self.llm and self.tools: # If tools were provided and LLM is up
            # print(f"Warning: HRAgent received tools, but its primary logic doesn't use an AgentExecutor by default.")
            # self.agent_executor = self._create_agent_executor_if_needed() # Placeholder
            pass


    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for HR Agent. Parses ticket, finds AI-matched employees, and returns a structured response.
        Args:
            input_data: Dictionary, expected to conform to HRTicketRequest or be parsable into it.
                        Typically includes "query" (for description), "ticket_id", "priority", etc.
        Returns:
            A dictionary representing HRTicketResponse or HRErrorResponse.
        """
        start_time = time.time()

        try:
            ticket_request = self._parse_ticket_request(input_data)

            if not self.availability_tool:
                return self._create_error_response(
                    error_type="configuration_error",
                    message="AvailabilityTool not configured for HRAgent.",
                    ticket_id=ticket_request.ticket_id if ticket_request else input_data.get("ticket_id"),
                    suggested_action="Initialize HRAgent with AvailabilityTool."
                ).model_dump()

            # Exclude the user who submitted the ticket, if that info is passed
            # The AvailabilityTool in optimized_project now takes exclude_username directly
            exclude_username = input_data.get("exclude_username")
            available_employees_data = self.availability_tool.get_available_employees(exclude_username=exclude_username)

            matches = self._find_employee_matches_with_ai(ticket_request, available_employees_data)

            processing_time = (time.time() - start_time) * 1000

            response = HRTicketResponse(
                agent_name=self.name,
                ticket_id=ticket_request.ticket_id,
                matched_employees=matches,
                total_matches=len(matches),
                processing_time_ms=processing_time,
                matching_strategy="ai_powered_analysis", # This agent's strategy
                confidence_level=self._calculate_confidence_from_matches(matches),
                recommended_assignment=matches[0].employee_id if matches else None,
                assignment_reasoning=matches[0].match_reasoning if matches else "No suitable AI match found."
            )
            return response.model_dump()

        except ValidationError as e: # Pydantic validation error for HRTicketRequest
            return self._create_validation_error_response(e, input_data.get("ticket_id")).model_dump()
        except Exception as e:
            print(f"Error in HRAgent run: {e}")
            import traceback
            traceback.print_exc()
            return self._create_error_response(
                error_type="processing_error",
                message=f"HRAgent AI processing failed: {str(e)}",
                ticket_id=input_data.get("ticket_id"),
                suggested_action="Review HRAgent logs and input."
            ).model_dump()

    def _parse_ticket_request(self, input_data: Dict[str, Any]) -> HRTicketRequest:
        """Parses input data into HRTicketRequest, handling potential legacy formats."""
        # Prioritize direct fields, then adapt from 'query' if needed.
        # This simplifies compared to original, assuming 'query' is mostly description.

        # Default skills_required to empty list if not provided
        skills_required = input_data.get("skills_required", [])
        if isinstance(skills_required, str): # Handle comma-separated string
            skills_required = [skill.strip() for skill in skills_required.split(',') if skill.strip()]

        parsed_data = {
            "ticket_id": input_data.get("ticket_id", f"hr_ticket_{int(time.time())}"),
            "title": input_data.get("title", input_data.get("query", "Untitled Ticket")[:100]),
            "description": input_data.get("description", input_data.get("query", "No description provided.")),
            "priority": input_data.get("priority", "medium"), # HRTicketPriority will validate
            "category": input_data.get("category"),
            "department": input_data.get("department"),
            "skills_required": skills_required,
            "urgency_level": input_data.get("urgency_level", 3)
        }
        return HRTicketRequest(**parsed_data)

    def _find_employee_matches_with_ai(self, ticket: HRTicketRequest,
                                     availability_data: Dict) -> List[HREmployeeMatch]:
        """Uses LLM to analyze and match employees to the ticket."""
        if not self.llm:
            print("Warning: HRAgent LLM not initialized. Cannot perform AI matching.")
            return [] # Or implement a very basic non-AI fallback if required

        # Combine 'available' and 'busy' employees as potential candidates
        # The original also included 'busy'. This can be a configuration.
        candidate_employees = availability_data.get("available", []) + availability_data.get("busy", [])

        if not candidate_employees:
            # print("No candidate employees (available or busy) for AI matching.")
            return []

        employee_profiles_for_prompt = []
        for emp in candidate_employees:
            # Construct a concise profile for the LLM
            profile = {
                "id": str(emp.get('id', emp.get('username'))), # Ensure ID is string
                "username": emp.get('username'),
                "name": emp.get('full_name'),
                "role": emp.get('role_in_company'),
                "expertise_summary": emp.get('expertise'), # LLM can parse this
                "availability": emp.get('availability_status')
            }
            employee_profiles_for_prompt.append(profile)

        # AI prompt for employee matching (Simplified from original for clarity and focus)
        # The original prompt was very detailed and prescriptive about scoring, which can be hard for LLMs
        # to follow perfectly. A more goal-oriented prompt might yield better/more consistent JSON.
        prompt = f"""
You are an HR AI Assistant. Your task is to find the best employee matches for the following support ticket.
Provide your response as a JSON array of the top 3 matches.

Ticket Details:
- Title: {ticket.title}
- Description: {ticket.description}
- Priority: {ticket.priority.value}
- Required Skills: {', '.join(ticket.skills_required) if ticket.skills_required else "Not specified"}

Available Employee Profiles:
{json.dumps(employee_profiles_for_prompt, indent=2)}

Instructions for Matching:
1.  Analyze the ticket description and required skills.
2.  For each employee, assess their suitability based on their role, expertise summary, and availability.
3.  Prioritize employees whose expertise strongly aligns with the ticket.
4.  Consider 'Available' status as highly preferred. 'Busy' employees can be considered if expertise match is very high.
5.  Provide an 'overall_score' (0.0 to 1.0) indicating the quality of the match.
6.  Provide a brief 'match_reasoning' (1-2 sentences) for each recommended employee.
7.  List key 'matching_skills' and potential 'missing_skills' based on the ticket's needs.

Output Format (Strict JSON array of top 3 matches):
[
  {{
    "employee_id": "employee_id_value",
    "employee_username": "username_value",
    "employee_name": "Full Name",
    "overall_score": 0.0_to_1.0,
    "matching_skills": ["skill1", "skill2"],
    "missing_skills": ["skill3"],
    "match_reasoning": "Brief explanation."
  }}
  // ... up to 2 more matches
]
Ensure employee_id and employee_username are from the provided profiles.
If no suitable matches, return an empty JSON array [].
"""

        try:
            ai_response_content = self.llm.invoke(f"{self.get_system_prompt()}\n\n{prompt}").content
            # print(f"HRAgent AI raw response: {ai_response_content}")

            extracted_json_str = self._extract_json_from_ai_response(ai_response_content)
            if not extracted_json_str:
                # print("HRAgent: No JSON array found in AI response.")
                return []

            ai_suggested_matches = json.loads(extracted_json_str)

            processed_matches: List[HREmployeeMatch] = []
            for suggested_match in ai_suggested_matches:
                # Find full employee data from candidates list to get all details
                full_emp_data = next((emp for emp in candidate_employees
                                      if str(emp.get("id", emp.get("username"))) == str(suggested_match.get("employee_id")) or \
                                         emp.get("username") == suggested_match.get("employee_username")), None)

                if full_emp_data:
                    try:
                        # Create HREmployeeMatch, filling missing fields from full_emp_data or defaults
                        match_obj = HREmployeeMatch(
                            employee_id=str(suggested_match.get("employee_id", full_emp_data.get("id"))),
                            username=suggested_match.get("employee_username", full_emp_data.get("username")),
                            name=suggested_match.get("employee_name", full_emp_data.get("full_name")),
                            email=full_emp_data.get("email"), # From full data
                            department=full_emp_data.get("department"), # From full data
                            skills=full_emp_data.get("expertise").split(", ") if isinstance(full_emp_data.get("expertise"), str) else [], # Simplified
                            availability_status=full_emp_data.get("availability_status", "Unknown"),
                            workload_level=int(full_emp_data.get("workload_level", 50)), # From full data
                            overall_score=float(suggested_match.get("overall_score", 0.0)),
                            # Other scores can be added if LLM provides them, or calculated by helper
                            skill_match_score=float(suggested_match.get("skill_match_score", suggested_match.get("overall_score",0.0)*0.7)), # Estimate
                            availability_score= 1.0 if full_emp_data.get("availability_status") == "Available" else 0.5, # Simple score
                            matching_skills=suggested_match.get("matching_skills", []),
                            missing_skills=suggested_match.get("missing_skills", []),
                            match_reasoning=suggested_match.get("match_reasoning", "AI recommended match.")
                        )
                        processed_matches.append(match_obj)
                    except ValidationError as ve:
                        print(f"HRAgent: Pydantic validation error for AI match data: {suggested_match}. Error: {ve}")
                    except Exception as ex:
                        print(f"HRAgent: Error processing AI match data: {suggested_match}. Error: {ex}")

            # Sort by overall_score if LLM provided it, otherwise keep LLM's order
            if processed_matches and hasattr(processed_matches[0], 'overall_score'):
                 processed_matches.sort(key=lambda m: m.overall_score, reverse=True)
            return processed_matches

        except json.JSONDecodeError as e:
            print(f"HRAgent: JSON parsing error from AI response: {e}. Raw content: {ai_response_content[:500]}")
            return [] # Fallback to no matches
        except Exception as e:
            print(f"HRAgent: General error in AI matching: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_json_from_ai_response(self, response_text: str) -> Optional[str]:
        """Extracts a JSON array string from the AI's text response."""
        # Look for markdown ```json ... ```
        match = re.search(r"```json\s*(\[[\s\S]*?\])\s*```", response_text, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Look for a raw JSON array
        match = re.search(r"(\[[\s\S]*?\])", response_text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    def _calculate_confidence_from_matches(self, matches: List[HREmployeeMatch]) -> float:
        """Calculates a confidence score based on the quality of the best match."""
        if not matches:
            return 0.0
        best_score = matches[0].overall_score # Assumes matches are sorted by score
        # Simple confidence mapping
        if best_score >= 0.85: return 0.95
        if best_score >= 0.70: return 0.80
        if best_score >= 0.50: return 0.60
        return 0.40

    def _create_error_response(self, error_type: str, message: str,
                             ticket_id: Optional[str] = None,
                             suggested_action: Optional[str] = None) -> HRErrorResponse:
        return HRErrorResponse(
            agent_name=self.name, error_type=error_type, error_message=message,
            ticket_id=ticket_id, failed_operation="employee_matching", suggested_action=suggested_action
        )

    def _create_validation_error_response(self, validation_error: ValidationError,
                                        ticket_id: Optional[str] = None) -> HRErrorResponse:
        error_details = "; ".join([f"{err['loc'][0] if err['loc'] else 'field'}: {err['msg']}" for err in validation_error.errors()])
        return HRErrorResponse(
            agent_name=self.name, error_type="validation_error",
            error_message=f"Input validation failed: {error_details}",
            ticket_id=ticket_id, failed_operation="input_validation", suggested_action="Check input format."
        )

    # Methods like assign_ticket, get_system_status, run_legacy, _format_employee_recommendation
    # from the original HRAgent are removed as they are either not part of the core AI workflow path
    # triggered by AISystem, or their functionality is now encapsulated within the main `run` method
    # or would be handled by different UI/service layers in a more modular design.
    # The _score_employee_match and related helpers are also removed as the new _find_employee_matches_with_ai
    # relies on the LLM for scoring and reasoning.

    def get_system_prompt(self) -> str:
        # This prompt is used if HRAgent were to use an AgentExecutor with tools.
        # For the current direct LLM call in _find_employee_matches_with_ai, a more specific prompt is constructed there.
        return """You are HRAgent, an AI expert in matching support tickets to the most suitable employees based on their skills, expertise, and availability.
Your goal is to find the best possible person to handle a given ticket efficiently.
You will be provided with ticket details and a list of available employee profiles.
Analyze this information carefully to make your recommendations.
"""
