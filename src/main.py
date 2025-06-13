"""
Main AI System implementation.
Orchestrates the multi-agent workflow with LangChain and LangGraph.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv
from langfuse import observe

from config.config_loader import config_loader
from agents.base_agent import ResearchAgent, AnalysisAgent
from tools.custom_tools import WebSearchTool, DocumentAnalysisTool, CalculatorTool
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
        
        # Initialize components
        self.tools = self._initialize_tools()
        self.agents = self._initialize_agents()
        self.vector_manager = None
        self.workflow = None
        self.evaluator = None
        
        # Initialize advanced components (may require API keys)
        try:
            self.vector_manager = VectorStoreManager(self.config)
            self.workflow = MultiAgentWorkflow(self.agents)
            self.evaluator = LLMEvaluator(self.config)
            print("✅ All components initialized successfully")
        except Exception as e:
            print(f"⚠️  Some components failed to initialize: {e}")
            print("This is normal if API keys are not configured yet.")
    
    def _initialize_tools(self) -> List:
        """Initialize all available tools."""
        return [
            WebSearchTool(),
            DocumentAnalysisTool(),
            CalculatorTool()
        ]
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all agents with their tools."""
        """Initialize all agents with their tools."""
        tools = [
            WebSearchTool(),
            DocumentAnalysisTool(),
            CalculatorTool()
        ]
        
        return {
            "research": ResearchAgent(tools=tools),
            "analysis": AnalysisAgent(tools=tools)
        }
    
    @observe()
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the complete system."""
        print(f"🔍 Processing query: {query}")
        
        try:
            # For now, return a simple response
            # This will be expanded once API keys are configured
            response = {
                "query": query,
                "status": "success",
                "result": f"Processed query: {query}",
                "agents_used": list(self.agents.keys()),
                "tools_available": len(self.tools)
            }
            
            # If workflow is available, use it
            if self.workflow:
                workflow_result = self.workflow.run({"query": query})
                response["workflow_result"] = workflow_result
            
            return response
            
        except Exception as e:
            return {
                "query": query,
                "status": "error",
                "error": str(e)
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


if __name__ == "__main__":
    main()
