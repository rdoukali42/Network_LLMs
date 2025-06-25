"""
Workflow service for orchestrating multi-agent workflows.
"""

from typing import Dict, Any, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from core.base_service import BaseService
from core.agent_manager import AgentManager
from core.event_bus import EventBus
from data.models.ticket import Ticket, TicketStatus
from data.models.user import User
from utils.exceptions import ValidationError, BusinessLogicError, WorkflowError
from config.prompts import get_workflow_prompt, get_system_prompt
from graphs.workflow_core import MultiAgentWorkflow
import uuid
import asyncio

if TYPE_CHECKING:
    from services.ticket_service import TicketService
    from services.user_service import UserService


class WorkflowStage(Enum):
    """Workflow execution stages."""
    INITIATED = "initiated"
    PREPROCESSING = "preprocessing"
    AGENT_PROCESSING = "agent_processing"
    SYNTHESIS = "synthesis"
    RESPONSE_GENERATION = "response_generation"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowType(Enum):
    """Types of workflows."""
    TICKET_PROCESSING = "ticket_processing"
    QUERY_ANSWERING = "query_answering"
    HR_REQUEST = "hr_request"
    POLICY_INQUIRY = "policy_inquiry"
    ESCALATION = "escalation"
    FOLLOW_UP = "follow_up"


@dataclass
class WorkflowContext:
    """Context data for workflow execution."""
    workflow_id: str
    workflow_type: WorkflowType
    stage: WorkflowStage
    username: str
    ticket_id: Optional[int] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    agent_results: Dict[str, Any] = field(default_factory=dict)
    error_messages: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_stage(self, new_stage: WorkflowStage):
        """Update workflow stage and timestamp."""
        self.stage = new_stage
        self.updated_at = datetime.now()
    
    def add_error(self, error_message: str):
        """Add error message to context."""
        self.error_messages.append(error_message)
        self.updated_at = datetime.now()
    
    def add_agent_result(self, agent_name: str, result: Dict[str, Any]):
        """Add agent execution result."""
        self.agent_results[agent_name] = {
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.updated_at = datetime.now()


class WorkflowService(BaseService):
    """
    Service for orchestrating multi-agent workflows.
    """
    
    def __init__(self, settings, ticket_service=None, user_service=None):
        super().__init__(settings)
        self.ticket_service = ticket_service
        self.user_service = user_service
        self._active_workflows: Dict[str, WorkflowContext] = {}
        
        # Debug logging for initialization
        self.logger.debug(f"[DEBUG] WorkflowService initialized with user_service: {type(user_service).__name__ if user_service else 'None'}")
        if user_service and hasattr(user_service, 'user_repository'):
            self.logger.debug(f"[DEBUG] WorkflowService user_service repository db_path: {getattr(user_service.user_repository, 'db_path', 'N/A')}")
        
        # Initialize core framework components
        self.agent_manager = AgentManager(settings)
        self.event_bus = EventBus()
        
        # Register agents with the agent manager
        self._register_agents()
        
        # Create agent instances for MultiAgentWorkflow
        self._agents_dict = self._create_agents_dict()
        
        # Initialize MultiAgentWorkflow for complex multi-agent flows
        self.multi_agent_workflow = MultiAgentWorkflow(self._agents_dict)
        
        self._workflow_handlers: Dict[WorkflowType, Callable] = {
            WorkflowType.TICKET_PROCESSING: self._handle_ticket_processing,
            WorkflowType.QUERY_ANSWERING: self._handle_query_answering,
            WorkflowType.HR_REQUEST: self._handle_hr_request,
            WorkflowType.POLICY_INQUIRY: self._handle_policy_inquiry,
            WorkflowType.ESCALATION: self._handle_escalation,
            WorkflowType.FOLLOW_UP: self._handle_follow_up,
        }
    
    def start_workflow(
        self,
        workflow_type: WorkflowType,
        username: str,
        input_data: Dict[str, Any],
        ticket_id: Optional[int] = None
    ) -> str:
        """
        Start a new workflow.
        
        Args:
            workflow_type: Type of workflow to execute
            username: Username of the user initiating the workflow
            input_data: Input data for the workflow
            ticket_id: Optional ticket ID if workflow is ticket-related
            
        Returns:
            Workflow ID
            
        Raises:
            ValidationError: If input validation fails
            BusinessLogicError: If business rules are violated
        """
        try:
            # Validate inputs
            self._validate_workflow_start(workflow_type, username, input_data)
            
            # Generate workflow ID
            workflow_id = str(uuid.uuid4())
            
            # Create workflow context
            context = WorkflowContext(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                stage=WorkflowStage.INITIATED,
                username=username,
                ticket_id=ticket_id,
                input_data=input_data
            )
            
            # Store workflow
            self._active_workflows[workflow_id] = context
            
            self.logger.info(f"Workflow started: {workflow_id} ({workflow_type.value}) for user {username}")
            
            # Execute workflow asynchronously
            self._execute_workflow(context)
            
            return workflow_id
            
        except Exception as e:
            self.logger.error(f"Failed to start workflow: {e}")
            raise
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow status and results.
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow status information
        """
        try:
            if workflow_id not in self._active_workflows:
                return None
            
            context = self._active_workflows[workflow_id]
            
            return {
                "workflow_id": workflow_id,
                "workflow_type": context.workflow_type.value,
                "stage": context.stage.value,
                "username": context.username,
                "ticket_id": context.ticket_id,
                "created_at": context.created_at.isoformat(),
                "updated_at": context.updated_at.isoformat(),
                "output_data": context.output_data,
                "agent_results": context.agent_results,
                "error_messages": context.error_messages,
                "is_completed": context.stage in [WorkflowStage.COMPLETED, WorkflowStage.FAILED, WorkflowStage.CANCELLED]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get workflow status: {e}")
            return None
    
    def cancel_workflow(self, workflow_id: str, cancelled_by_username: str) -> bool:
        """
        Cancel an active workflow.
        
        Args:
            workflow_id: Workflow ID to cancel
            cancelled_by_username: Username of user cancelling the workflow
            
        Returns:
            True if workflow was cancelled
        """
        try:
            if workflow_id not in self._active_workflows:
                return False
            
            context = self._active_workflows[workflow_id]
            
            # Check permissions
            if context.username != cancelled_by_username:
                user = self.user_service.get_user_by_username(cancelled_by_username)
                if not user or not self._is_admin(user):
                    raise BusinessLogicError("Insufficient permissions to cancel this workflow")
            
            # Update context
            context.update_stage(WorkflowStage.CANCELLED)
            context.add_error(f"Workflow cancelled by user {cancelled_by_username}")
            
            self.logger.info(f"Workflow cancelled: {workflow_id} by user {cancelled_by_username}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cancel workflow: {e}")
            raise
    
    def _execute_workflow(self, context: WorkflowContext):
        """Execute workflow based on type."""
        try:
            handler = self._workflow_handlers.get(context.workflow_type)
            if not handler:
                raise WorkflowError(f"No handler for workflow type: {context.workflow_type.value}")
            
            # Execute the specific workflow handler
            import threading
            
            def run_workflow():
                """Run workflow in a separate thread to avoid event loop conflicts."""
                try:
                    # Create a new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run the workflow
                    loop.run_until_complete(self._execute_workflow_async(handler, context))
                    
                finally:
                    # Clean up the event loop
                    loop.close()
            
            # Start workflow in a separate thread to avoid blocking the main event loop
            workflow_thread = threading.Thread(target=run_workflow, daemon=True)
            workflow_thread.start()
            
        except Exception as e:
            context.add_error(f"Workflow execution failed: {str(e)}")
            context.update_stage(WorkflowStage.FAILED)
            self.logger.error(f"Workflow execution failed: {context.workflow_id} - {e}")
    
    async def _execute_workflow_async(self, handler: Callable, context: WorkflowContext):
        """Execute workflow handler asynchronously."""
        try:
            await handler(context)
            
            # Publish completion event
            self.event_bus.publish_sync("workflow.completed", {
                "workflow_id": context.workflow_id,
                "workflow_type": context.workflow_type.value,
                "stage": context.stage.value,
                "username": context.username
            })
            
        except Exception as e:
            context.add_error(f"Workflow execution failed: {str(e)}")
            context.update_stage(WorkflowStage.FAILED)
            
            # Publish failure event
            self.event_bus.publish_sync("workflow.failed", {
                "workflow_id": context.workflow_id,
                "workflow_type": context.workflow_type.value,
                "error": str(e),
                "username": context.username
            })
    
    async def _handle_ticket_processing(self, context: WorkflowContext):
        """Handle ticket processing workflow."""
        try:
            self.logger.info(f"Processing ticket workflow: {context.workflow_id}")
            
            # Stage 1: Preprocessing
            context.update_stage(WorkflowStage.PREPROCESSING)
            
            # Extract ticket information
            ticket_data = context.input_data
            query = ticket_data.get("query", "")
            category = ticket_data.get("category", "general")
            
            # Stage 2: Agent Processing
            context.update_stage(WorkflowStage.AGENT_PROCESSING)
            
            # Route to appropriate agent based on category
            if category.lower() in ["hr", "human resources", "benefits", "policy"]:
                agent_result = await self._process_with_hr_agent(query, context)
                context.add_agent_result("hr_agent", agent_result)
            else:
                agent_result = await self._process_with_maestro_agent(query, context)
                context.add_agent_result("maestro_agent", agent_result)
            
            # Stage 3: Synthesis
            context.update_stage(WorkflowStage.SYNTHESIS)
            response = self._synthesize_response(context)
            
            # Stage 4: Response Generation
            context.update_stage(WorkflowStage.RESPONSE_GENERATION)
            context.output_data = {
                "response": response,
                "agent_used": list(context.agent_results.keys())[0],
                "processing_time": (datetime.now() - context.created_at).total_seconds(),
                "resolution_type": "automated" if agent_result.get("confidence", 0) > 0.8 else "assisted"
            }
            
            # Complete workflow
            context.update_stage(WorkflowStage.COMPLETED)
            
            self.logger.info(f"Ticket processing workflow completed: {context.workflow_id}")
            
        except Exception as e:
            context.add_error(f"Ticket processing failed: {str(e)}")
            context.update_stage(WorkflowStage.FAILED)
            raise
    
    async def _handle_query_answering(self, context: WorkflowContext):
        """Handle query answering workflow using MultiAgentWorkflow."""
        try:
            self.logger.info(f"🎯 QUERY WORKFLOW: Starting multi-agent query answering workflow: {context.workflow_id}")
            
            query = context.input_data.get("query", "")
            if not query:
                self.logger.error(f"🎯 QUERY WORKFLOW: No query provided in input_data")
                raise WorkflowError("Query is required for query answering workflow")
            
            self.logger.info(f"🎯 QUERY WORKFLOW: Processing query with MultiAgentWorkflow: {query}")
            
            # Use MultiAgentWorkflow for complete multi-agent flow
            # Prepare workflow input including ticket ID if available
            workflow_input = {
                "query": query,
                "workflow_id": context.workflow_id,
                "username": context.username
            }
            if context.ticket_id:
                workflow_input["original_ticket_id"] = context.ticket_id
            
            # Run the complete multi-agent workflow (Maestro → Data Guardian → Maestro synthesis)
            workflow_results = self.multi_agent_workflow.run(workflow_input)
            
            self.logger.info(f"🎯 QUERY WORKFLOW: MultiAgentWorkflow completed with results: {list(workflow_results.keys())}")
            
            # Update context with results from multi-agent workflow
            context.update_stage(WorkflowStage.COMPLETED)
            
            # Extract the final response from workflow results
            final_response = workflow_results.get("synthesis", workflow_results.get("final_response", ""))
            if not final_response:
                # No fallback - this is an error condition
                raise WorkflowError("MultiAgentWorkflow did not produce a synthesis response")
            
            context.output_data = {
                "response": final_response,
                "original_query": query,
                "processed_query": query,
                "confidence": 0.8,  # High confidence for multi-agent workflow
                "sources": [],
                "workflow_results": workflow_results,  # Include full workflow results
                "documents_found": workflow_results.get("documents_found", 0)
            }
            
            self.logger.info(f"🎯 QUERY WORKFLOW: Multi-agent workflow completed successfully: {context.workflow_id}")
            self.logger.info(f"🎯 QUERY WORKFLOW: Final response length: {len(final_response)} characters")
            
        except Exception as e:
            self.logger.error(f"🎯 QUERY WORKFLOW ERROR: Multi-agent query answering failed: {str(e)}")
            context.add_error(f"Multi-agent query answering failed: {str(e)}")
            context.update_stage(WorkflowStage.FAILED)
            raise
    
    async def _handle_hr_request(self, context: WorkflowContext):
        """Handle HR-specific request workflow."""
        try:
            self.logger.info(f"Processing HR request workflow: {context.workflow_id}")
            
            context.update_stage(WorkflowStage.PREPROCESSING)
            
            # HR requests require special privacy considerations
            user = self.user_service.get_user_by_username(context.username)
            if not user:
                raise WorkflowError("User not found for HR request")
            
            context.update_stage(WorkflowStage.AGENT_PROCESSING)
            
            # Process with HR agent
            hr_result = await self._process_with_hr_agent(
                context.input_data.get("query", ""), 
                context,
                user_context=user.to_dict()
            )
            context.add_agent_result("hr_agent", hr_result)
            
            # Check if escalation is needed
            if hr_result.get("requires_escalation", False):
                escalation_result = self._handle_hr_escalation(context, hr_result)
                context.add_agent_result("escalation", escalation_result)
            
            context.update_stage(WorkflowStage.SYNTHESIS)
            response = self._synthesize_hr_response(context)
            
            context.update_stage(WorkflowStage.RESPONSE_GENERATION)
            context.output_data = {
                "response": response,
                "privacy_level": hr_result.get("privacy_level", "standard"),
                "requires_follow_up": hr_result.get("requires_follow_up", False),
                "escalated": hr_result.get("requires_escalation", False),
                # Include assignment data for ticket processing
                "hr_action": hr_result.get("hr_action"),
                "employee_data": hr_result.get("employee_data")
            }
            
            context.update_stage(WorkflowStage.COMPLETED)
            
        except Exception as e:
            context.add_error(f"HR request processing failed: {str(e)}")
            context.update_stage(WorkflowStage.FAILED)
            raise
    
    async def _handle_policy_inquiry(self, context: WorkflowContext):
        """Handle policy inquiry workflow."""
        try:
            context.update_stage(WorkflowStage.PREPROCESSING)
            
            query = context.input_data.get("query", "")
            policy_type = context.input_data.get("policy_type", "general")
            
            context.update_stage(WorkflowStage.AGENT_PROCESSING)
            
            # Process with data guardian for policy compliance
            guardian_result = await self._process_with_data_guardian(query, context)
            context.add_agent_result("data_guardian", guardian_result)
            
            # If approved, process with appropriate agent
            if guardian_result.get("approved", False):
                if policy_type in ["hr", "employee"]:
                    agent_result = await self._process_with_hr_agent(query, context)
                    context.add_agent_result("hr_agent", agent_result)
                else:
                    agent_result = await self._process_with_maestro_agent(query, context)
                    context.add_agent_result("maestro_agent", agent_result)
            
            context.update_stage(WorkflowStage.SYNTHESIS)
            response = self._synthesize_policy_response(context)
            
            context.update_stage(WorkflowStage.RESPONSE_GENERATION)
            context.output_data = {
                "response": response,
                "policy_type": policy_type,
                "access_approved": guardian_result.get("approved", False),
                "restrictions": guardian_result.get("restrictions", [])
            }
            
            context.update_stage(WorkflowStage.COMPLETED)
            
        except Exception as e:
            context.add_error(f"Policy inquiry failed: {str(e)}")
            context.update_stage(WorkflowStage.FAILED)
            raise
    
    async def _handle_escalation(self, context: WorkflowContext):
        """Handle escalation workflow."""
        try:
            context.update_stage(WorkflowStage.PREPROCESSING)
            
            # Escalation logic
            escalation_type = context.input_data.get("escalation_type", "general")
            original_ticket_id = context.input_data.get("original_ticket_id")
            
            context.update_stage(WorkflowStage.AGENT_PROCESSING)
            
            # Determine escalation path
            escalation_result = self._determine_escalation_path(context)
            context.add_agent_result("escalation_manager", escalation_result)
            
            context.update_stage(WorkflowStage.RESPONSE_GENERATION)
            context.output_data = {
                "escalation_path": escalation_result.get("path", "manual_review"),
                "assigned_to": escalation_result.get("assigned_to", "support_team"),
                "priority": escalation_result.get("priority", "high"),
                "estimated_resolution": escalation_result.get("estimated_resolution", "24 hours")
            }
            
            context.update_stage(WorkflowStage.COMPLETED)
            
        except Exception as e:
            context.add_error(f"Escalation handling failed: {str(e)}")
            context.update_stage(WorkflowStage.FAILED)
            raise
    
    async def _handle_follow_up(self, context: WorkflowContext):
        """Handle follow-up workflow."""
        try:
            context.update_stage(WorkflowStage.PREPROCESSING)
            
            original_ticket_id = context.input_data.get("original_ticket_id")
            follow_up_type = context.input_data.get("follow_up_type", "satisfaction")
            
            context.update_stage(WorkflowStage.AGENT_PROCESSING)
            
            # Generate follow-up content
            follow_up_result = self._generate_follow_up_content(context)
            context.add_agent_result("follow_up_generator", follow_up_result)
            
            context.update_stage(WorkflowStage.RESPONSE_GENERATION)
            context.output_data = {
                "follow_up_message": follow_up_result.get("message", ""),
                "follow_up_type": follow_up_type,
                "scheduled_for": follow_up_result.get("scheduled_for", "immediate"),
                "requires_response": follow_up_result.get("requires_response", False)
            }
            
            context.update_stage(WorkflowStage.COMPLETED)
            
        except Exception as e:
            context.add_error(f"Follow-up handling failed: {str(e)}")
            context.update_stage(WorkflowStage.FAILED)
            raise
    
    def _register_agents(self):
        """
        Register all real agents with the agent manager.
        This method ensures all real LLM-backed agents are available for use in workflows.
        """
        try:
            # Import agent classes
            from agents.maestro_agent import MaestroAgent
            from agents.hr_agent import HRAgent
            from agents.data_guardian_agent import DataGuardianAgent
            from agents.vocal_assistant import VocalAssistantAgent
            
            # Register Maestro agent - the main query processing agent
            self.agent_manager.register_agent(
                name="maestro",
                agent_class=MaestroAgent,
                capabilities=["ticket_processing", "query_answering", "general_support"],
                metadata={"description": "Primary orchestration and general query agent"}
            )
            
            # Register HR agent - specialized in HR policies and requests
            self.agent_manager.register_agent(
                name="hr",
                agent_class=HRAgent,
                capabilities=["hr_request", "policy_inquiry", "employee_management"],
                metadata={"description": "HR specialist for policy and personnel matters"}
            )
            
            # Register Data Guardian agent - handles data security and document retrieval
            self.agent_manager.register_agent(
                name="data_guardian",
                agent_class=DataGuardianAgent,
                capabilities=["document_search", "data_verification", "security_compliance"],
                metadata={"description": "Data security and document retrieval specialist"}
            )
            
            # Register Vocal Assistant agent - handles voice calls with assigned employees
            self.agent_manager.register_agent(
                name="vocal_assistant",
                agent_class=VocalAssistantAgent,
                capabilities=["voice_calls", "employee_communication", "call_management"],
                metadata={"description": "Voice communication specialist for employee interactions"}
            )
            
            self.logger.info("Successfully registered all real agents with AgentManager")
            
        except Exception as e:
            self.logger.error(f"Failed to register agents: {str(e)}")
            raise WorkflowError(f"Agent registration failed: {str(e)}")
    
    def _create_agents_dict(self) -> Dict[str, Any]:
        """Create agent instances dict for MultiAgentWorkflow."""
        try:
            agents_dict = {}
            required_agents = ["maestro", "hr", "data_guardian", "vocal_assistant"]
            
            # Get agent instances from AgentManager
            for agent_name in required_agents:
                agent_instance = self.agent_manager.get_agent(agent_name, auto_create=True)
                if agent_instance:
                    agents_dict[agent_name] = agent_instance
                    self.logger.debug(f"Added agent '{agent_name}' to workflow agents dict")
                else:
                    # Fail fast if any required agent is missing
                    raise WorkflowError(f"Required agent '{agent_name}' could not be created or retrieved")
            
            self.logger.info(f"Created agents dict with all {len(agents_dict)} required agents: {list(agents_dict.keys())}")
            return agents_dict
            
        except Exception as e:
            self.logger.error(f"Failed to create agents dict: {str(e)}")
            # No fallback - this is an error condition that should be resolved
            raise WorkflowError(f"Agent creation failed: {str(e)}")
    
    def _validate_workflow_start(self, workflow_type: WorkflowType, username: str, input_data: Dict[str, Any]):
        """Validate workflow inputs before starting."""
        # General validation for all workflows
        if not isinstance(workflow_type, WorkflowType):
            raise ValidationError("Invalid workflow type")
        
        if not isinstance(username, str) or not username.strip():
            raise ValidationError("Invalid username")
        
        if not isinstance(input_data, dict):
            raise ValidationError("Input data must be a dictionary")
        
        # Specific validations for each workflow type
        if workflow_type == WorkflowType.TICKET_PROCESSING:
            if "query" not in input_data or not input_data["query"]:
                raise ValidationError("Query is required for ticket processing")
            if "category" not in input_data:
                raise ValidationError("Category is required for ticket processing")
        
        elif workflow_type == WorkflowType.QUERY_ANSWERING:
            if "query" not in input_data or not input_data["query"]:
                raise ValidationError("Query is required for query answering")
        
        elif workflow_type == WorkflowType.HR_REQUEST:
            if "query" not in input_data or not input_data["query"]:
                raise ValidationError("Query is required for HR requests")
        
        elif workflow_type == WorkflowType.POLICY_INQUIRY:
            if "query" not in input_data or not input_data["query"]:
                raise ValidationError("Query is required for policy inquiries")
        
        elif workflow_type == WorkflowType.ESCALATION:
            if "escalation_type" not in input_data:
                raise ValidationError("Escalation type is required")
        
        elif workflow_type == WorkflowType.FOLLOW_UP:
            if "original_ticket_id" not in input_data:
                raise ValidationError("Original ticket ID is required for follow-up")
        
        # Common validation for user existence
        self.logger.debug(f"[DEBUG] WorkflowService user validation for '{username}', workflow: {workflow_type}")
        
        if self.user_service is None:
            self.logger.warning(f"No user service available to validate user {username}")
            # Skip user validation when service is not available
            return
        
        self.logger.debug(f"[DEBUG] WorkflowService using UserService: {type(self.user_service).__name__}")
        self.logger.debug(f"[DEBUG] WorkflowService UserService repository: {type(self.user_service.user_repository).__name__} with db_path: {getattr(self.user_service.user_repository, 'db_path', 'N/A')}")
            
        try:
            user = self.user_service.get_user_by_username(username)
            if not user:
                raise ValidationError("User not found")
            
            self.logger.debug(f"[DEBUG] WorkflowService user validation successful for '{username}': {user.full_name}")
            
            # If HR request, check HR-specific validations
            if workflow_type == WorkflowType.HR_REQUEST:
                if not self._is_hr_policy_compliant(input_data.get("query", ""), user):
                    raise BusinessLogicError("HR request violates policy constraints")
        except Exception as e:
            self.logger.error(f"User validation error: {str(e)}")
            # Continue processing despite validation errors in test/development environments
            if hasattr(self, 'settings') and hasattr(self.settings, 'is_production') and not self.settings.is_production:
                self.logger.warning(f"Continuing despite user validation error in non-production environment")
                return
        
        self.logger.info(f"Workflow start validation passed for {workflow_type.value} by user {username}")
    
    # Agent processing methods using AgentManager
    
    async def _process_with_maestro_agent(self, query: str, context: WorkflowContext) -> Dict[str, Any]:
        """Process query with Maestro agent."""
        try:
            self.logger.info(f"🤖 MAESTRO AGENT: Starting Maestro agent processing")
            self.logger.info(f"🤖 MAESTRO AGENT: Query: {query}")
            self.logger.info(f"🤖 MAESTRO AGENT: Workflow: {context.workflow_id}")
            
            input_data = {
                "query": query,
                "stage": "preprocess",
                "context": {
                    "workflow_id": context.workflow_id,
                    "workflow_type": context.workflow_type.value,
                    "username": context.username
                }
            }
            
            self.logger.info(f"🤖 MAESTRO AGENT: Input data prepared: {input_data}")
            self.logger.info(f"🤖 MAESTRO AGENT: Calling agent_manager.execute_agent('maestro', ...)")
            
            result = await self.agent_manager.execute_agent("maestro", input_data)
            
            self.logger.info(f"🤖 MAESTRO AGENT: Agent execution completed")
            self.logger.info(f"🤖 MAESTRO AGENT: Result type: {type(result)}")
            self.logger.info(f"🤖 MAESTRO AGENT: Result content: {result}")
            
            # Publish event
            self.event_bus.publish_sync("agent.completed", {
                "agent": "maestro",
                "workflow_id": context.workflow_id,
                "result": result
            })
            
            self.logger.info(f"🤖 MAESTRO AGENT: Event published, returning result")
            return result
            
        except Exception as e:
            self.logger.error(f"🤖 MAESTRO AGENT ERROR: Maestro agent processing failed: {str(e)}")
            import traceback
            self.logger.error(f"🤖 MAESTRO AGENT ERROR: Traceback: {traceback.format_exc()}")
            raise WorkflowError(f"Maestro agent processing failed: {str(e)}")
    
    async def _process_with_hr_agent(self, query: str, context: WorkflowContext, user_context: Dict = None) -> Dict[str, Any]:
        """Process query with HR agent."""
        try:
            input_data = {
                "query": query,
                "user_context": user_context or {},
                "context": {
                    "workflow_id": context.workflow_id,
                    "workflow_type": context.workflow_type.value,
                    "username": context.username
                }
            }
            
            result = await self.agent_manager.execute_agent("hr", input_data)
            
            # Publish event
            self.event_bus.publish_sync("agent.completed", {
                "agent": "hr",
                "workflow_id": context.workflow_id,
                "result": result
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"HR agent processing failed: {str(e)}")
            raise WorkflowError(f"HR agent processing failed: {str(e)}")
    
    async def _process_with_data_guardian(self, query: str, context: WorkflowContext) -> Dict[str, Any]:
        """Process query with Data Guardian agent."""
        try:
            input_data = {
                "query": query,
                "context": {
                    "workflow_id": context.workflow_id,
                    "workflow_type": context.workflow_type.value,
                    "username": context.username
                }
            }
            
            result = await self.agent_manager.execute_agent("data_guardian", input_data)
            
            # Publish event
            self.event_bus.publish_sync("agent.completed", {
                "agent": "data_guardian",
                "workflow_id": context.workflow_id,
                "result": result
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f"Data Guardian processing failed: {str(e)}")
            raise WorkflowError(f"Data Guardian processing failed: {str(e)}")
    
    # All simulation methods removed - only real agent processing allowed
    
    def get_service_name(self) -> str:
        """Return the service name."""
        return "WorkflowService"
    
    def process_query(self, query: str, username: str = "system", ticket_id: str = None) -> Dict[str, Any]:
        """
        Simple synchronous method to process a query.
        
        Args:
            query: The query to process
            username: Username (defaults to "system")
            ticket_id: Optional ticket ID for assignment purposes
            
        Returns:
            Dict containing the response and metadata
        """
        try:
            self.logger.info(f"🎫 PROCESSING QUERY: Starting query processing for user '{username}'")
            self.logger.info(f"🎫 QUERY CONTENT: {query}")
            
            # Prepare input data with ticket ID if provided
            input_data = {"query": query}
            if ticket_id:
                input_data["original_ticket_id"] = ticket_id
            
            # Start a query answering workflow
            workflow_id = self.start_workflow(
                workflow_type=WorkflowType.QUERY_ANSWERING,
                username=username,
                input_data=input_data,
                ticket_id=ticket_id
            )
            
            self.logger.info(f"🎫 WORKFLOW STARTED: {workflow_id} - Now waiting for completion...")
            
            # Wait for workflow completion with timeout
            import time
            max_wait_time = 60  # 60 seconds timeout
            wait_interval = 1   # Check every 1 second
            waited_time = 0
            
            while waited_time < max_wait_time:
                status = self.get_workflow_status(workflow_id)
                if not status:
                    self.logger.error(f"🎫 WORKFLOW ERROR: Could not get status for {workflow_id}")
                    break
                
                stage = status.get("stage", "unknown")
                self.logger.info(f"🎫 WORKFLOW STATUS: {workflow_id} - Stage: {stage}")
                
                if stage in ["completed", "failed", "cancelled"]:
                    self.logger.info(f"🎫 WORKFLOW FINISHED: {workflow_id} - Final stage: {stage}")
                    break
                
                time.sleep(wait_interval)
                waited_time += wait_interval
            
            # Get final workflow result
            final_status = self.get_workflow_status(workflow_id)
            
            if final_status and final_status.get("stage") == "completed":
                output_data = final_status.get("output_data", {})
                result = {
                    "result": output_data.get("response", "No response generated"),
                    "confidence": output_data.get("confidence", 0.5),
                    "sources": output_data.get("sources", []),
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "workflow_results": output_data.get("workflow_results", {}),
                    "documents_found": output_data.get("documents_found", 0)
                }
                self.logger.info(f"🎫 WORKFLOW SUCCESS: {workflow_id} - Returning result: {result['result'][:100]}...")
                return result
            elif final_status and final_status.get("stage") == "failed":
                error_messages = final_status.get("error_messages", ["Unknown error"])
                result = {
                    "result": f"Query processing failed: {'; '.join(error_messages)}",
                    "workflow_id": workflow_id,
                    "status": "failed"
                }
                self.logger.error(f"🎫 WORKFLOW FAILED: {workflow_id} - Errors: {error_messages}")
                return result
            else:
                # Timeout or other issue
                final_stage = final_status.get("stage", "unknown") if final_status else "no_status"
                result = {
                    "result": f"Query processing incomplete - workflow stage: {final_stage}",
                    "workflow_id": workflow_id,
                    "status": final_stage
                }
                self.logger.warning(f"🎫 WORKFLOW TIMEOUT: {workflow_id} - Final stage: {final_stage}")
                return result
                
        except Exception as e:
            self.logger.error(f"🎫 QUERY PROCESSING ERROR: {str(e)}")
            return {
                "result": f"Query processing failed: {str(e)}",
                "status": "error"
            }
    
    def _preprocess_query(self, query: str) -> str:
        """Preprocess a query for better understanding."""
        # Simple preprocessing for now - in a real system this would be more sophisticated
        processed_query = query.strip()
        
        # Add ticket context if available
        if processed_query.startswith("🎫") or "Ticket" in processed_query:
            return processed_query
        
        # Add ticket context for better agent understanding
        processed_query = f"🎫 Support Ticket Query: {processed_query}"
        
        return processed_query
    
    def _synthesize_response(self, context: WorkflowContext) -> str:
        """Synthesize a response from agent results."""
        self.logger.info(f"🔄 SYNTHESIS: Starting response synthesis")
        self.logger.info(f"🔄 SYNTHESIS: Available agent results: {list(context.agent_results.keys())}")
        
        # Get the first agent result (only one should be present)
        if not context.agent_results:
            self.logger.warning(f"🔄 SYNTHESIS: No agent results available")
            return "No agent response available."
        
        agent_name = list(context.agent_results.keys())[0]
        self.logger.info(f"🔄 SYNTHESIS: Processing result from agent: {agent_name}")
        
        agent_result = context.agent_results[agent_name]["result"]
        self.logger.info(f"🔄 SYNTHESIS: Agent result type: {type(agent_result)}")
        self.logger.info(f"🔄 SYNTHESIS: Agent result content: {agent_result}")
        
        # Extract response from result
        if isinstance(agent_result, dict):
            response = agent_result.get("response") or agent_result.get("answer") or agent_result.get("result")
            if response:
                self.logger.info(f"🔄 SYNTHESIS: Found response in agent result: {response}")
                return response
            else:
                self.logger.warning(f"🔄 SYNTHESIS: No response/answer/result field found in agent result")
                self.logger.warning(f"🔄 SYNTHESIS: Available keys: {list(agent_result.keys())}")
        else:
            self.logger.warning(f"🔄 SYNTHESIS: Agent result is not a dictionary")
        
        # No fallback - this indicates a serious problem
        error_msg = f"Agent {agent_name} did not produce a valid result for synthesis"
        self.logger.error(f"🔄 SYNTHESIS ERROR: {error_msg}")
        raise WorkflowError(error_msg)
        
    def _synthesize_hr_response(self, context: WorkflowContext) -> str:
        """Synthesize an HR-specific response."""
        # Similar to regular synthesis but with HR context
        if "hr_agent" not in context.agent_results:
            return "No HR agent response available."
        
        hr_result = context.agent_results["hr_agent"]["result"]
        
        # Extract response from result
        if isinstance(hr_result, dict):
            response = hr_result.get("response") or hr_result.get("answer") or hr_result.get("recommendation")
            if response:
                return response
        
        return "Your HR request has been processed."
        
    def _synthesize_policy_response(self, context: WorkflowContext) -> str:
        """Synthesize a policy-specific response."""
        # Get data guardian result first
        if "data_guardian" not in context.agent_results:
            return "No data guardian response available."
        
        guardian_result = context.agent_results["data_guardian"]["result"]
        
        # If access was denied, return the guardian's explanation
        if not guardian_result.get("approved", False):
            return guardian_result.get("explanation", "Access to requested policy information was denied.")
        
        # Otherwise, get the response from the primary agent
        for agent_name in ["hr_agent", "maestro_agent"]:
            if agent_name in context.agent_results:
                agent_result = context.agent_results[agent_name]["result"]
                response = agent_result.get("response") or agent_result.get("answer") or agent_result.get("result")
                if response:
                    return response
        
        return "Your policy inquiry has been processed."
    
    def _is_admin(self, user: User) -> bool:
        """Check if a user has admin privileges."""
        if not user:
            return False
            
        # Check for admin role in user roles
        if hasattr(user, 'roles') and isinstance(user.roles, list):
            return 'admin' in [role.lower() for role in user.roles]
            
        # Check for admin flag if available
        if hasattr(user, 'is_admin'):
            return bool(user.is_admin)
            
        # Default to False for safety
        return False
    
    def _is_hr_policy_compliant(self, query: str, user: User) -> bool:
        """Check if an HR request complies with HR policy."""
        if not query or not user:
            return False
            
        # Block obvious sensitive keywords for non-HR users
        sensitive_keywords = [
            "salary", "compensation", "fire", "terminate", "ssn", 
            "social security", "bank account", "password"
        ]
        
        query_lower = query.lower()
        
        # If user has HR role, allow all queries
        if hasattr(user, 'roles') and isinstance(user.roles, list):
            if 'hr' in [role.lower() for role in user.roles]:
                return True
        
        # Check for sensitive keywords
        for keyword in sensitive_keywords:
            if keyword in query_lower:
                # Allow users to query their own information
                if "my " + keyword in query_lower or keyword + " my" in query_lower:
                    continue
                    
                # Otherwise block the query
                return False
        
        # Default to allow
        return True
    
    def _handle_hr_escalation(self, context: WorkflowContext, hr_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle HR request escalation."""
        escalation_reason = hr_result.get("escalation_reason", "No reason provided")
        priority = hr_result.get("priority", "medium")
        
        # Determine assignee
        assignee = "hr_team"  # Default
        
        return {
            "escalated_to": assignee,
            "reason": escalation_reason,
            "priority": priority,
            "requires_human": hr_result.get("requires_human", True),
            "estimated_response": "24 hours" if priority == "low" else "8 hours" if priority == "medium" else "4 hours"
        }
    
    def _determine_escalation_path(self, context: WorkflowContext) -> Dict[str, Any]:
        """Determine the escalation path for a workflow."""
        escalation_type = context.input_data.get("escalation_type", "general")
        
        # Determine escalation path based on type
        if escalation_type == "hr":
            path = "hr_team"
            priority = "high"
        elif escalation_type == "technical":
            path = "engineering_team"
            priority = "medium"
        elif escalation_type == "urgent":
            path = "support_manager"
            priority = "critical"
        else:
            path = "support_team"
            priority = "normal"
        
        return {
            "path": path,
            "assigned_to": f"{path}@company.com",
            "priority": priority,
            "estimated_resolution": "4 hours" if priority == "critical" else "8 hours" if priority == "high" else "24 hours"
        }
    
    def _generate_follow_up_content(self, context: WorkflowContext) -> Dict[str, Any]:
        """Generate follow-up content for a workflow."""
        follow_up_type = context.input_data.get("follow_up_type", "satisfaction")
        
        if follow_up_type == "satisfaction":
            message = "We hope your issue has been resolved to your satisfaction."
            scheduled_for = "24 hours"
            requires_response = True
        elif follow_up_type == "confirmation":
            message = "We want to confirm that your issue has been resolved."
            scheduled_for = "8 hours"
            requires_response = True
        else:
            message = "Thank you for using our support system."
            scheduled_for = "24 hours"
            requires_response = True
        
        return {
            "message": message,
            "scheduled_for": scheduled_for,
            "requires_response": requires_response
        }
