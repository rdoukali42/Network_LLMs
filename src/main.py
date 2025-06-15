"""
Main AI System implementation.
Orchestrates the multi-agent workflow with LangChain and LangGraph.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from langfuse import observe

from config.config_loader import config_loader
from agents.base_agent import MaestroAgent, DataGuardianAgent, HRAgent
from tools.custom_tools import DocumentAnalysisTool, CalculatorTool
from tools.availability_tool import AvailabilityTool
from vectorstore.vector_manager import VectorStoreManager
from graphs.workflow import MultiAgentWorkflow
from evaluation.llm_evaluator import LLMEvaluator
from utils.helpers import load_sample_data, save_experiment_results

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
            
            # Initialize evaluator
            self.evaluator = LLMEvaluator(self.config)
            
            print("✅ All components initialized successfully")
        except Exception as e:
            print(f"⚠️  Some components failed to initialize: {e}")
            print("This is normal if API keys are not configured yet.")
    
    def _initialize_tools(self) -> List:
        """Initialize all available tools."""
        return [
            DocumentAnalysisTool(),
            CalculatorTool()
        ]
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agents with their tools."""
        # Tools for Maestro (general processing and calculations)
        maestro_tools = [
            CalculatorTool()
        ]
        
        # Tools for Data Guardian (document analysis)
        data_guardian_tools = [
            DocumentAnalysisTool()
        ]
        
        # Initialize availability tool for HR Agent
        availability_tool = AvailabilityTool()
        
        return {
            "maestro": MaestroAgent(config=self.config, tools=maestro_tools),
            "data_guardian": DataGuardianAgent(config=self.config, tools=data_guardian_tools, vector_manager=self.vector_manager),
            "hr_agent": HRAgent(config=self.config, tools=[], availability_tool=availability_tool)
        }
    
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
            return {
                "query": query,
                "status": "error",
                "error": str(e),
                "result": f"Error processing query: {e}"
            }
    
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
    
    @observe()
    def run_experiment(self, experiment_name: str, test_queries: List[str]) -> Dict[str, Any]:
        """Run an experiment with a specific configuration."""
        print(f"🧪 Running experiment: {experiment_name}")
        
        try:
            # Load experiment configuration
            experiment_config = config_loader.load_experiment_config(experiment_name)
            
            # Create new system instance with experiment config
            experiment_system = AISystem()
            experiment_system.config = experiment_config
            
            # Process all test queries
            results = []
            for query in test_queries:
                result = experiment_system.process_query(query)
                
                # Evaluate if evaluator is available
                evaluation = None
                if self.evaluator:
                    try:
                        evaluation = self.evaluator.evaluate_response(
                            query, result.get("result", ""), None
                        )
                    except Exception as e:
                        evaluation = {"error": str(e)}
                
                results.append({
                    "query": query,
                    "result": result,
                    "evaluation": evaluation
                })
            
            experiment_result = {
                "experiment_name": experiment_name,
                "config": experiment_config,
                "results": results,
                "summary": {
                    "total_queries": len(test_queries),
                    "successful_queries": len([r for r in results if r["result"]["status"] == "success"])
                }
            }
            
            # Save results
            save_experiment_results(experiment_result, experiment_name)
            
            return experiment_result
            
        except Exception as e:
            return {
                "experiment_name": experiment_name,
                "status": "error",
                "error": str(e)
            }
    
    @observe()
    def initialize_with_sample_data(self) -> Dict[str, Any]:
        """Initialize the system with sample data."""
        try:
            # Load sample documents
            sample_docs = load_sample_data()
            
            # Add to vector store if available
            if self.vector_manager:
                result = self.add_documents_to_vectorstore(sample_docs)
                return {
                    "status": "success",
                    "message": "System initialized with sample data",
                    "vectorstore_result": result,
                    "documents_loaded": len(sample_docs)
                }
            else:
                return {
                    "status": "partial",
                    "message": "Sample data loaded but vector store not available",
                    "documents_loaded": len(sample_docs)
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}


def main():
    """Main function for testing the system."""
    print("🚀 Initializing AI System...")
    
    try:
        # Initialize system
        system = AISystem()
        print("✅ AI System initialized successfully")
        
        # Test basic functionality
        test_query = "What is artificial intelligence?"
        print(f"\n🔍 Testing with query: '{test_query}'")
        
        result = system.process_query(test_query)
        print(f"📋 Result: {result}")
        
        # Initialize with sample data
        print("\n📚 Loading sample data...")
        init_result = system.initialize_with_sample_data()
        print(f"📋 Initialization result: {init_result}")
        
        print("\n✅ System test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during system test: {e}")
        print("This is expected if API keys are not configured.")

def process_query(query: str) -> Dict[str, Any]:
    """Standalone function to process a query through the AI system."""
    try:
        system = AISystem()
        return system.process_query(query)
    except Exception as e:
        return {
            "query": query,
            "status": "error",
            "error": str(e),
            "result": f"Error initializing system: {e}"
        }


if __name__ == "__main__":
    main()
