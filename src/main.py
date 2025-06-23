"""
Main AI System implementation.
Orchestrates the multi-agent workflow with LangChain and LangGraph.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from langfuse import observe

from config.config_loader import config_loader
from agents import MaestroAgent, DataGuardianAgent, HRAgent
from tools.availability_tool import AvailabilityTool
from tools.employee_search_tool import EmployeeSearchTool
from vectorstore.vector_manager import VectorStoreManager
from graphs.workflow import MultiAgentWorkflow

# Load environment variables
load_dotenv()


class AISystem:
    """Main AI System orchestrating all components."""
    
    def __init__(self, config_name: str = "development"):
        """Initialize the AI system with configuration."""
        # Load configuration
        self.config = config_loader.load_config(config_name)
        
        # Initialize tools first
        self.tools = self._initialize_tools()
        
        # Initialize vector manager
        self.vector_manager = None
        self.agents = None
        self.workflow = None
        self.evaluator = None
        
        # Initialize advanced components (may require API keys)
        try:
            # Vector manager first
            self.vector_manager = VectorStoreManager(self.config)
            
            # Load documents from raw folder into vector store
            self._load_raw_documents()
            
            # Initialize agents with vector manager
            self.agents = self._initialize_agents()
            
            # Initialize workflow with agents
            self.workflow = MultiAgentWorkflow(self.agents)
            
            print("✅ All components initialized successfully")
        except Exception as e:
            print(f"⚠️  Some components failed to initialize: {e}")
            print("This is normal if API keys are not configured yet.")
    
    def _initialize_tools(self) -> List:
        """Initialize all available tools."""
        return []
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agents with their tools."""
        # Tools for Maestro (general processing)
        maestro_tools = []
        
        # Tools for Data Guardian (document analysis)
        data_guardian_tools = []
        
        # Initialize availability tool for HR Agent
        availability_tool = AvailabilityTool()
        
        # Initialize employee search tool for redirect functionality
        employee_search_tool = EmployeeSearchTool()
        
        agents = {
            "maestro": MaestroAgent(config=self.config, tools=maestro_tools),
            "data_guardian": DataGuardianAgent(config=self.config, tools=data_guardian_tools, vector_manager=self.vector_manager),
            "hr_agent": HRAgent(config=self.config, tools=[], availability_tool=availability_tool),
            "employee_search_tool": employee_search_tool  # Add search tool as an "agent" for workflow access
        }
        
        # Add VocalAssistant if available
        try:
            from agents.vocal_assistant import VocalAssistantAgent
            agents["vocal_assistant"] = VocalAssistantAgent(config=self.config, tools=[])
            print("✅ VocalAssistant agent loaded successfully")
        except ImportError as e:
            print(f"⚠️ Warning: Could not load VocalAssistant agent: {e}")
            print("Voice functionality will not be available")
        
        return agents
    
    def _load_raw_documents(self):
        """Load documents from data/raw/ folder into vector store."""
        import os
        from pathlib import Path
        
        try:
            # Get path to raw documents
            project_root = Path(__file__).parent.parent
            raw_docs_path = project_root / "data" / "raw"
            
            if not raw_docs_path.exists():
                print(f"⚠️ Raw documents folder not found: {raw_docs_path}")
                return
            
            documents = []
            metadatas = []
            
            # Load all text files from raw folder
            for file_path in raw_docs_path.glob("*"):
                if file_path.is_file() and file_path.suffix in ['.txt', '.md']:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if content.strip():  # Only add non-empty files
                                documents.append(content)
                                metadatas.append({
                                    'source': file_path.name,
                                    'file_path': str(file_path),
                                    'file_type': file_path.suffix
                                })
                        print(f"📄 Loaded document: {file_path.name}")
                    except Exception as e:
                        print(f"⚠️ Failed to load {file_path.name}: {e}")
            
            # Add documents to vector store
            if documents:
                self.vector_manager.add_documents(documents, metadatas)
                print(f"✅ Successfully loaded {len(documents)} documents into vector store")
            else:
                print("⚠️ No documents found in raw folder")
                
        except Exception as e:
            print(f"⚠️ Failed to load raw documents: {e}")

    @observe()
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the complete system."""
        print(f"🔍 Processing query: {query}")
        
        try:
            # If workflow is available, use it for real AI processing
            if self.workflow:
                workflow_result = self.workflow.run({"query": query})
                
                # Extract the final synthesized response
                final_response = workflow_result.get("synthesis", "")
                if not final_response or final_response == "Synthesis completed":
                    # Fallback to combining available results
                    research = workflow_result.get("research", "")
                    analysis = workflow_result.get("analysis", "")
                    if research and analysis:
                        final_response = f"Research: {research}\n\nAnalysis: {analysis}"
                    else:
                        final_response = f"Processed query: {query}"
                
                response = {
                    "query": query,
                    "status": "success",
                    "result": final_response,
                    "agents_used": list(self.agents.keys()),
                    "tools_available": len(self.tools),
                    "workflow_result": workflow_result
                }
            else:
                # Fallback when workflow is not available
                response = {
                    "query": query,
                    "status": "success",
                    "result": f"Processed query: {query}",
                    "agents_used": list(self.agents.keys()),
                    "tools_available": len(self.tools)
                }
            
            return response
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            response = {
                "query": query,
                "status": "error",
                "error": str(e),
                "result": f"Error processing query: {e}"
            }
            return response

    @observe()
    def add_documents_to_vectorstore(self, documents: List[str]) -> Dict[str, Any]:
        """Add documents to the vector store."""
        if not self.vector_manager:
            return {"status": "error", "message": "Vector manager not initialized"}
        
        try:
            self.vector_manager.add_documents(documents)
            return {
                "status": "success",
                "message": f"Added {len(documents)} documents to vector store"
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    @observe()
    def search_documents(self, query: str, k: int = 4) -> Dict[str, Any]:
        """Search documents in the vector store."""
        if not self.vector_manager:
            return {"status": "error", "message": "Vector manager not initialized"}
        
        try:
            results = self.vector_manager.similarity_search(query, k=k)
            return {
                "status": "success",
                "query": query,
                "results": results
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    pass
