"""
Main AI System implementation for the optimized_project.
Orchestrates the multi-agent workflow.
"""

import os
from typing import Dict, Any, List, Optional
from pathlib import Path

from langfuse import observe # Assuming Langfuse is kept

# Adjusted imports for the new structure
from ..config.core_config import CoreConfigLoader
from ..core.agents import MaestroAgent, DataGuardianAgent, HRAgent, VocalAssistantAgent
from ..core.tools import DocumentAnalysisTool, AvailabilityTool # CalculatorTool removed
from ..vectorstore.vector_manager import VectorStoreManager
from ..core.graph.workflow import MultiAgentWorkflow
# from ..evaluation.llm_evaluator import LLMEvaluator # Pruned for minimal core app
# from ..utils.helpers import load_sample_data # Pruned for minimal core app

class AISystem:
    """Main AI System orchestrating all components for the optimized project."""

    def __init__(self, project_root_path: Path, config_env_name: str = "development"):
        """
        Initialize the AI system.
        Args:
            project_root_path: Absolute path to the 'optimized_project' root.
            config_env_name: Name of the configuration environment (e.g., "development", "production").
        """
        self.project_root = project_root_path
        self.config_loader = CoreConfigLoader(base_project_root=self.project_root)
        self.core_config = self.config_loader.load_config_yaml(config_env_name)

        # Initialize components, order matters for dependencies
        self.db_manager = self._initialize_database_manager() # For AvailabilityTool
        self.tools = self._initialize_tools()

        self.vector_manager: Optional[VectorStoreManager] = None
        self.agents: Optional[Dict[str, Any]] = None
        self.workflow: Optional[MultiAgentWorkflow] = None
        # self.evaluator: Optional[LLMEvaluator] = None # Pruned

        # Initialize components that might depend on API keys or external resources
        try:
            self.vector_manager = VectorStoreManager(core_config=self.core_config, project_root_path=self.project_root)
            self._load_raw_documents_to_vectorstore() # Load documents after vector_manager is up

            self.agents = self._initialize_agents()
            self.workflow = MultiAgentWorkflow(self.agents) # Pass agent instances

            # self.evaluator = LLMEvaluator(self.core_config) # Pruned

            print("✅ AISystem: All core components initialized successfully.")
        except Exception as e:
            print(f"⚠️ AISystem: Some components failed to initialize: {e}")
            print("   This might be due to missing API keys or configuration issues.")
            import traceback
            traceback.print_exc()

    def _initialize_database_manager(self) -> Optional[Any]:
        """Initializes and returns a DatabaseManager instance."""
        try:
            # Relative import from within core to data_management
            from ..data_management.database import DatabaseManager
            return DatabaseManager(project_root_path=self.project_root)
        except ImportError as e:
            print(f"Error importing DatabaseManager: {e}. AvailabilityTool might not work.")
            return None
        except Exception as e:
            print(f"Error initializing DatabaseManager: {e}")
            return None


    def _initialize_tools(self) -> Dict[str, Any]:
        """Initializes all available tools and returns them in a dictionary."""
        initialized_tools = {}
        initialized_tools["document_analyzer"] = DocumentAnalysisTool()
        # CalculatorTool is removed.

        if self.db_manager:
            initialized_tools["availability_tool"] = AvailabilityTool(db_manager_instance=self.db_manager)
        else:
            print("Warning: DatabaseManager not available, AvailabilityTool not initialized.")

        return initialized_tools

    def _get_agent_llm_config(self, agent_name: str) -> Dict[str, Any]:
        """Helper to construct the LLM config for an agent from core_config."""
        # Start with default LLM settings
        llm_settings = self.core_config.get("models", {}).get("default_llm", {}).copy()
        # Override with agent-specific LLM settings if they exist
        agent_specific_llm_settings = self.core_config.get("models", {}).get(f"{agent_name}_model", {})
        llm_settings.update(agent_specific_llm_settings)

        # Ensure required fields are present, provide defaults if necessary
        return {
            "llm_provider": llm_settings.get("provider", self.core_config.get("models", {}).get("default_llm", {}).get("provider", "google_gemini")),
            "model_name": llm_settings.get("model_name", self.core_config.get("models", {}).get("default_llm", {}).get("model_name", "gemini-pro")),
            "temperature": float(llm_settings.get("temperature", 0.7)),
            # API key env var name can also be globally configured or agent-specific
            "api_key_env_var": llm_settings.get("api_key_env_var", self.core_config.get("api_keys",{}).get("default_llm_api_key_env_var", "GEMINI_API_KEY"))
        }

    def _initialize_agents(self) -> Dict[str, Any]:
        """Initializes all agents with their tools and configurations."""
        agents_dict: Dict[str, Any] = {}

        # Maestro Agent
        maestro_config = self._get_agent_llm_config("maestro_agent")
        # Maestro tools: currently none after Calculator removal. Pass empty list.
        agents_dict["maestro"] = MaestroAgent(agent_config=maestro_config, tools=[])

        # Data Guardian Agent
        data_guardian_config = self._get_agent_llm_config("data_guardian_agent")
        dg_tools = [self.tools["document_analyzer"]] if "document_analyzer" in self.tools else []
        if self.vector_manager:
            agents_dict["data_guardian"] = DataGuardianAgent(
                agent_config=data_guardian_config,
                vector_manager_instance=self.vector_manager,
                project_root_path=self.project_root,
                tools=dg_tools
            )
        else:
            print("Warning: VectorManager not available, DataGuardianAgent not fully initialized.")

        # HR Agent
        hr_agent_config = self._get_agent_llm_config("hr_agent")
        availability_tool_instance = self.tools.get("availability_tool")
        if availability_tool_instance:
            agents_dict["hr_agent"] = HRAgent(
                agent_config=hr_agent_config,
                availability_tool_instance=availability_tool_instance
                # HR Agent typically doesn't use generic tools, but its own AvailabilityTool logic
            )
        else:
            print("Warning: AvailabilityTool not available, HRAgent not fully initialized.")

        # Vocal Assistant Agent
        vocal_assistant_config = self._get_agent_llm_config("vocal_assistant_agent")
        # VocalAssistantAgent primarily orchestrates; actual voice via VoiceService.
        # If it needed to make its own LLM calls for summarization etc., it uses its LLM.
        agents_dict["vocal_assistant"] = VocalAssistantAgent(agent_config=vocal_assistant_config)

        return agents_dict

    def _load_raw_documents_to_vectorstore(self):
        """Loads documents from data/raw/ into the vector store."""
        if not self.vector_manager:
            print("AISystem: VectorManager not initialized. Skipping document loading.")
            return

        raw_docs_dir_path = self.project_root / "data" / "raw"
        if not raw_docs_dir_path.exists() or not raw_docs_dir_path.is_dir():
            print(f"AISystem: Raw documents directory not found: {raw_docs_dir_path}")
            return

        documents_to_add: List[str] = []
        metadatas_to_add: List[Dict[str, Any]] = []

        # print(f"AISystem: Scanning for documents in {raw_docs_dir_path}...")
        for file_path in raw_docs_dir_path.glob("*"): # Handles .md, .txt etc.
            if file_path.is_file() and file_path.suffix.lower() in ['.txt', '.md']:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if content.strip():
                        documents_to_add.append(content)
                        metadatas_to_add.append({
                            'source': file_path.name,
                            'file_path': str(file_path.relative_to(self.project_root) if file_path.is_absolute() else file_path),
                            'file_type': file_path.suffix
                        })
                        # print(f"AISystem: Staged document for loading: {file_path.name}")
                except Exception as e:
                    print(f"AISystem: Failed to read or stage document {file_path.name}: {e}")

        if documents_to_add:
            try:
                self.vector_manager.add_documents(documents_to_add, metadatas_to_add)
                print(f"AISystem: Successfully loaded {len(documents_to_add)} documents into vector store.")
            except Exception as e:
                print(f"AISystem: Error adding documents to vector store: {e}")
        else:
            print(f"AISystem: No documents found in {raw_docs_dir_path} to load.")

    @observe() # Assuming Langfuse is kept
    def process_query(self, query: str, initial_workflow_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Processes a user query through the AI workflow.
        Args:
            query: The user's question or request.
            initial_workflow_input: Optional dictionary to pass additional context to the workflow,
                                    e.g., {"exclude_username": "user_xyz", "ticket_id": "T123"}.
                                    The 'query' will be overridden by the query arg.
        Returns:
            A dictionary containing the response from the AI system.
        """
        # print(f"AISystem: Processing query: {query}")

        if not self.workflow or not self.agents:
            print("AISystem: Workflow or Agents not initialized. Cannot process query.")
            return {
                "query": query, "status": "error", "error": "AISystem not fully initialized.",
                "result": "The AI system is currently unavailable. Please try again later.",
                "synthesis": "The AI system is currently unavailable. Please try again later." # For compatibility
            }

        # Prepare the input for the workflow run
        workflow_input_data = initial_workflow_input.copy() if initial_workflow_input else {}
        workflow_input_data["query"] = query # Ensure the primary query is set

        try:
            workflow_output = self.workflow.run(workflow_input_data)

            # The 'synthesis' key is expected by the frontend (WorkflowClient)
            # MultiAgentWorkflow's final step should populate results["synthesis"] or results["final_system_response"]
            final_response_text = workflow_output.get("synthesis", workflow_output.get("final_system_response", "No definitive response generated by workflow."))

            # Construct a consistent response structure
            system_response = {
                "query": query,
                "status": "success" if "error" not in workflow_output else "error",
                "result": final_response_text, # For general display
                "synthesis": final_response_text, # Specifically for WorkflowClient
                "agents_used": list(self.agents.keys()), # Could be refined by graph output
                "workflow_full_output": workflow_output # Include the detailed graph output
            }
            if "error" in workflow_output:
                system_response["error_details"] = workflow_output["error"]

            return system_response

        except Exception as e:
            print(f"AISystem: Critical error during process_query: {e}")
            import traceback
            traceback.print_exc()
            return {
                "query": query, "status": "error", "error": f"Unhandled exception in AISystem: {str(e)}",
                "result": "An unexpected error occurred while processing your request.",
                "synthesis": "An unexpected error occurred."
            }

# Minimal main for basic testing if this file is run directly
if __name__ == '__main__':
    print("🚀 Initializing AISystem for direct testing...")
    # Assume this script is in optimized_project/core/system.py
    # So, project_root is parent.parent
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent
    print(f"Project root for testing: {project_root}")

    # This requires .env to be in optimized_project/ and config YAMLs in optimized_project/config/
    # Ensure GEMINI_API_KEY is set in .env or environment
    if not (project_root / ".env").exists() and not os.getenv("GEMINI_API_KEY"):
        print("WARNING: .env file not found at project root and GEMINI_API_KEY not in environment.")
        print("         AISystem initialization or LLM calls may fail.")
        print(f"         Expected .env at: {project_root / '.env'}")

    try:
        ai_system = AISystem(project_root_path=project_root, config_env_name="development")

        if ai_system.workflow:
            print("\n✅ AISystem initialized successfully with workflow.")
            test_query = "What is the process for resetting my password?"
            print(f"\n🔍 Testing AISystem with query: '{test_query}'")
            response = ai_system.process_query(test_query)
            print("\n📋 AISystem Response:")
            import json
            print(json.dumps(response, indent=2))
        else:
            print("\n⚠️ AISystem initialized, but workflow component is missing. Cannot run full query processing.")

    except Exception as e:
        print(f"❌ Error during AISystem direct test: {e}")
        import traceback
        traceback.print_exc()
