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
    """Multi-agent workflow using LangGraph."""
    
    def __init__(self, agents: Dict[str, Any]):
        self.agents = agents
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the workflow graph."""
        workflow = StateGraph(WorkflowState)
        
        # Add nodes for each agent
        workflow.add_node("research", self._research_step)
        workflow.add_node("analysis", self._analysis_step)
        workflow.add_node("synthesis", self._synthesis_step)
        
        # Define edges
        workflow.set_entry_point("research")
        workflow.add_edge("research", "analysis")
        workflow.add_edge("analysis", "synthesis")
        workflow.add_edge("synthesis", END)
        
        return workflow.compile()
    
    @observe()
    def _research_step(self, state: WorkflowState) -> WorkflowState:
        """Research step in the workflow."""
        state = state.copy()
        state["current_step"] = "research"
        
        # Get query from state
        query = state.get("query", "")
        if not query and state.get("messages"):
            query = state["messages"][-1].get("content", "")
        
        # Run research agent
        if "research" in self.agents:
            research_result = self.agents["research"].run({"query": query})
            state["results"]["research"] = research_result.get("result", "Research completed")
        else:
            state["results"]["research"] = "Research completed"
        
        return state
    
    @observe()
    def _analysis_step(self, state: WorkflowState) -> WorkflowState:
        """Analysis step in the workflow."""
        state = state.copy()
        state["current_step"] = "analysis"
        
        # Get query and research result
        query = state.get("query", "")
        research_result = state["results"].get("research", "")
        
        # Run analysis agent
        if "analysis" in self.agents:
            analysis_result = self.agents["analysis"].run({
                "query": query,
                "research_result": research_result
            })
            state["results"]["analysis"] = analysis_result.get("result", "Analysis completed")
        else:
            state["results"]["analysis"] = "Analysis completed"
        
        return state
    
    @observe()
    def _synthesis_step(self, state: WorkflowState) -> WorkflowState:
        """Synthesis step in the workflow."""
        state = state.copy()
        state["current_step"] = "synthesis"
        
        # Combine research and analysis results
        research = state["results"].get("research", "")
        analysis = state["results"].get("analysis", "")
        
        # Create final synthesized response
        if research and analysis:
            synthesis = f"""Based on comprehensive research and analysis:

RESEARCH FINDINGS:
{research}

ANALYSIS & INSIGHTS:
{analysis}

This represents a complete multi-agent analysis of your query."""
        else:
            synthesis = "Synthesis completed"
        
        state["results"]["synthesis"] = synthesis
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
            # Fallback: run agents manually
            print(f"Running fallback workflow for: {query}")
            
            # Research step
            research_result = self.agents["research"].run({"query": query})
            print(f"Research result: {research_result}")
            
            # Analysis step  
            analysis_result = self.agents["analysis"].run({
                "query": query,
                "research_result": research_result.get("result", "")
            })
            print(f"Analysis result: {analysis_result}")
            
            # Synthesis step
            research_text = research_result.get("result", "Research completed")
            analysis_text = analysis_result.get("result", "Analysis completed")
            
            synthesis = f"""Based on comprehensive research and analysis:

RESEARCH FINDINGS:
{research_text}

ANALYSIS & INSIGHTS:
{analysis_text}

This represents a complete multi-agent analysis of your query."""
            
            return {
                "research": research_text,
                "analysis": analysis_text,
                "synthesis": synthesis
            }
