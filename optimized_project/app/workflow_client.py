"""
Workflow client for connecting the Streamlit app (in optimized_project/app)
to the AI system (in optimized_project/core).
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# To import AISystem from optimized_project.core.system
# This client assumes it's within optimized_project/app/
# So, optimized_project_root is one level up from this file's parent.
OPTIMIZED_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Add optimized_project root to sys.path to allow imports like 'from core.system import AISystem'
if str(OPTIMIZED_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(OPTIMIZED_PROJECT_ROOT))

# Now we can import from core
from core.system import AISystem

# Environment variables for core system are loaded by CoreConfigLoader within AISystem/CoreConfigLoader itself.
# No need for dotenv here directly, unless app layer has its own .env for UI settings.

class AppWorkflowClient:
    """
    Client for the Streamlit UI to interact with the backend AISystem.
    This acts as a bridge and helps decouple the UI from direct AISystem complexities.
    """

    _instance: Optional['AppWorkflowClient'] = None
    _initialized_system: Optional[AISystem] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AppWorkflowClient, cls).__new__(cls)
            # Initialize AISystem only once
            try:
                # print(f"AppWorkflowClient: Initializing AISystem with project root: {OPTIMIZED_PROJECT_ROOT}")
                # The AISystem now takes project_root_path and optionally config_env_name
                cls._initialized_system = AISystem(project_root_path=OPTIMIZED_PROJECT_ROOT)
                if not cls._initialized_system.workflow: # Check if a critical part failed
                    print("AppWorkflowClient: Warning - AISystem initialized but workflow component is missing.")
                    # Decide if this is a fatal error for the client
                    # For now, it will lead to process_message returning an error.
            except Exception as e:
                print(f"AppWorkflowClient: Critical error initializing AISystem: {e}")
                import traceback
                traceback.print_exc()
                cls._initialized_system = None # Ensure it's None if init fails
        return cls._instance

    def __init__(self):
        """
        Initializes the AppWorkflowClient.
        The AISystem is initialized as a singleton within the __new__ method.
        """
        # __init__ will be called every time AppWorkflowClient() is invoked,
        # but self.system will point to the class-level _initialized_system.
        self.system: Optional[AISystem] = AppWorkflowClient._initialized_system
        if self.system:
            # print("AppWorkflowClient: AISystem is available.")
            pass
        else:
            print("AppWorkflowClient: AISystem is NOT available. Process_message calls will fail.")


    def process_message(self, message_text: str, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a message (query) through the AI system.

        Args:
            message_text: The user's message or query.
            additional_context: Optional dictionary for extra data to pass to the workflow
                                (e.g., {"exclude_username": "user_xyz", "ticket_id": "T123"}).
        Returns:
            A dictionary containing the response from the AI system.
        """
        if not self.system or not self.system.workflow: # Also check if workflow (critical part) is up
            error_msg = "AI system is not initialized or critical components are missing. Please check backend logs."
            print(f"AppWorkflowClient: {error_msg}")
            return {
                "status": "error",
                "error": error_msg,
                "synthesis": "The AI system is currently unavailable. Please try again later."
            }

        try:
            # The AISystem.process_query now handles the CWD changes internally if needed.
            # We pass the query and any additional context.
            # print(f"AppWorkflowClient: Processing message: '{message_text}' with context: {additional_context}")
            return self.system.process_query(query=message_text, initial_workflow_input=additional_context)

        except Exception as e:
            print(f"AppWorkflowClient: Error during process_message: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"Error processing message via AI system: {str(e)}",
                "synthesis": "An error occurred while communicating with the AI system."
            }

    def is_ai_system_ready(self) -> bool:
        """Check if the underlying AI system (and its workflow) is initialized and ready."""
        return self.system is not None and self.system.workflow is not None

# Example of how this client might be used in the Streamlit app:
# client = AppWorkflowClient() # Singleton pattern ensures AISystem is init'd once
# if client.is_ai_system_ready():
#     response = client.process_message("My query here", {"ticket_id": "T456"})
# else:
#     st.error("AI System is not ready.")

if __name__ == '__main__':
    print("Attempting to initialize AppWorkflowClient (and AISystem)...")
    # This test requires:
    # 1. This file to be in optimized_project/app/
    # 2. The rest of the core system (agents, graph, etc.) to be in optimized_project/core/
    # 3. Config files (development.yaml) in optimized_project/config/
    # 4. .env file in optimized_project/ (with GEMINI_API_KEY)
    # 5. data/raw directory with some documents in optimized_project/ for vector store loading.

    # Create dummy raw file for AISystem init if it doesn't exist, for testing purposes
    raw_dir_for_test = OPTIMIZED_PROJECT_ROOT / "data" / "raw"
    raw_dir_for_test.mkdir(parents=True, exist_ok=True)
    dummy_doc_path = raw_dir_for_test / "dummy_test_doc.md"
    if not dummy_doc_path.exists():
        with open(dummy_doc_path, "w") as f:
            f.write("This is a dummy document for AISystem initialization testing.")
        print(f"Created dummy document: {dummy_doc_path}")

    client = AppWorkflowClient()
    print(f"AI System Ready: {client.is_ai_system_ready()}")

    if client.is_ai_system_ready():
        print("\nTesting process_message...")
        test_msg = "What is the company policy on remote work?"
        # Example of passing additional context, like exclude_username for HR agent
        context = {"exclude_username": "test_user_streamlit", "ticket_id": "UI_T001"}
        response = client.process_message(test_msg, additional_context=context)

        print("\nResponse from AI System via Client:")
        import json
        print(json.dumps(response, indent=2))
    else:
        print("Cannot test process_message as AI system is not ready.")

    # Second instantiation should use the same AISystem instance
    # print("\nAttempting second client instantiation...")
    # client2 = AppWorkflowClient()
    # if client.system is client2.system:
    #     print("Confirmed: Second client uses the same AISystem instance (Singleton behavior).")
    # else:
    #     print("Error: Second client created a new AISystem instance (Singleton FAILED).")
