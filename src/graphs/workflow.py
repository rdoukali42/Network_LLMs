"""
LangGraph workflow definitions.
"""

from typing import Dict, Any, List, TypedDict
from langgraph.graph import StateGraph, END
from langfuse import observe


class WorkflowState(TypedDict):
    """State object for the workflow."""
    messages: List[Dict]
    current_step: str
    results: Dict[str, Any]
    metadata: Dict[str, Any]
    query: str  # Add query as explicit field


class MultiAgentWorkflow:
    """Multi-agent workflow using LangGraph for Maestro and Data Guardian."""
    
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the workflow graph."""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each step
        workflow.add_node("maestro_preprocess", self._maestro_preprocess_step)
        workflow.add_node("data_guardian", self._data_guardian_step)
        workflow.add_node("maestro_synthesize", self._maestro_synthesize_step)
        
        # Define edges: Maestro → Data Guardian → Maestro → End
        workflow.set_entry_point("maestro_preprocess")
        workflow.add_edge("maestro_preprocess", "data_guardian")
        workflow.add_edge("data_guardian", "maestro_synthesize")
        workflow.add_edge("maestro_synthesize", END)
        
        return workflow.compile()
    
    @observe()
    def _maestro_preprocess_step(self, state: WorkflowState) -> WorkflowState:
        """Maestro preprocessing step - reformulate query for search."""
        state = state.copy()
        state["current_step"] = "maestro_preprocess"
        
        # Get query from state
        query = state.get("query", "")
        if not query and state.get("messages"):
            query = state["messages"][-1].get("content", "")
        
        # Run Maestro preprocessing
        if "maestro" in self.agents:
            maestro_result = self.agents["maestro"].run({
                "query": query,
                "stage": "preprocess"
            })
            state["results"]["maestro_preprocess"] = maestro_result.get("result", "Query processed")
        else:
            state["results"]["maestro_preprocess"] = query  # Fallback
        
        return state
    
    @observe()
    def _data_guardian_step(self, state: WorkflowState) -> WorkflowState:
        """Data Guardian step - search local documents."""
        state = state.copy()
        state["current_step"] = "data_guardian"
        
        # Get query and preprocessed queries
        query = state.get("query", "")
        search_queries = state["results"].get("maestro_preprocess", query)
        
        # Run Data Guardian search
        if "data_guardian" in self.agents:
            data_guardian_result = self.agents["data_guardian"].run({
                "query": query,
                "search_queries": search_queries
            })
            state["results"]["data_guardian"] = data_guardian_result.get("result", "No documents found")
        else:
            state["results"]["data_guardian"] = "Data Guardian not available"
        
        return state
    
    @observe()
    def _maestro_synthesize_step(self, state: WorkflowState) -> WorkflowState:
        """Maestro synthesis step - create final response."""
        state = state.copy()
        state["current_step"] = "maestro_synthesize"
        
        # Get query and Data Guardian result
        query = state.get("query", "")
        data_guardian_result = state["results"].get("data_guardian", "")
        
        # Run Maestro synthesis
        if "maestro" in self.agents:
            synthesis_result = self.agents["maestro"].run({
                "query": query,
                "stage": "synthesize",
                "data_guardian_result": data_guardian_result
            })
            state["results"]["synthesis"] = synthesis_result.get("result", "Response generated")
        else:
            # Fallback synthesis
            state["results"]["synthesis"] = f"Based on available information: {data_guardian_result}"
        
        return state
    
    @observe()
    def run(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete workflow."""
        query = initial_input.get("query", "")
        
        initial_state: WorkflowState = {
            "messages": [{"content": query, "type": "user"}],
            "current_step": "",
            "results": {},
            "metadata": initial_input,
            "query": query  # Ensure query is preserved
        }
        
        # Try to run the graph workflow, fallback to simple execution
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state["results"]
        except Exception as e:
            # Fallback: run agents manually in sequence
            print(f"Running fallback workflow for: {query}")
            
            # Step 1: Maestro preprocessing
            maestro_preprocess = self.agents["maestro"].run({
                "query": query,
                "stage": "preprocess"
            })
            print(f"Maestro preprocess result: {maestro_preprocess}")
            
            # Step 2: Data Guardian search
            data_guardian_result = self.agents["data_guardian"].run({
                "query": query,
                "search_queries": maestro_preprocess.get("result", query)
            })
            print(f"Data Guardian result: {data_guardian_result}")
            
            # Step 3: Maestro synthesis
            maestro_synthesis = self.agents["maestro"].run({
                "query": query,
                "stage": "synthesize", 
                "data_guardian_result": data_guardian_result.get("result", "")
            })
            print(f"Maestro synthesis result: {maestro_synthesis}")
            
            # Return combined results
            return {
                "maestro_preprocess": maestro_preprocess.get("result", ""),
                "data_guardian": data_guardian_result.get("result", ""),
                "synthesis": maestro_synthesis.get("result", ""),
                "documents_found": data_guardian_result.get("documents_found", 0)
            }
