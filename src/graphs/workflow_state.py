"""
Workflow state definitions and types.
"""
from typing import Dict, Any, List, TypedDict


class WorkflowState(TypedDict):
    """State object for the workflow."""
    messages: List[Dict]
    current_step: str
    results: Dict[str, Any]
    metadata: Dict[str, Any]
    query: str  # Add query as explicit field
