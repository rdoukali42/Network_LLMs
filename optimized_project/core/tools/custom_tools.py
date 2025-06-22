"""
Custom tools for agents to use in the optimized project.
These are example tools and can be expanded or replaced.
CalculatorTool has been removed as per user request.
"""
from typing import Any, Dict, Optional
from langchain.tools import BaseTool # Assuming Langchain BaseTool is still the desired base
from langfuse import observe # Assuming Langfuse is kept

# It's good practice to define a more specific input schema if tools become complex
# from pydantic import BaseModel, Field
# class DocumentAnalysisInput(BaseModel):
#     document_content: str = Field(description="The full text of the document to be analyzed.")
#     analysis_focus: Optional[str] = Field(None, description="Specific aspect to focus on during analysis, e.g., 'summarize', 'extract_entities'.")

class DocumentAnalysisTool(BaseTool):
    name: str = "document_analyzer"
    description: str = "Analyzes a given document text to extract key information or provide insights. Input should be the document text."
    # args_schema: Type[BaseModel] = DocumentAnalysisInput # Example if using Pydantic input schema

    @observe()
    def _run(self, document_content: str, analysis_focus: Optional[str] = None) -> str:
        """
        Analyzes the document.
        In a real scenario, this would involve NLP techniques, possibly another LLM call.
        """
        if not document_content:
            return "Error: No document content provided for analysis."

        # print(f"DocumentAnalysisTool received content (first 100 chars): {document_content[:100]}")
        # print(f"Analysis focus: {analysis_focus}")

        if analysis_focus == "summarize":
            summary = ". ".join(document_content.split(". ")[:2]) + "."
            return f"Summary of document: {summary}"
        elif analysis_focus == "extract_entities":
            if "john doe" in document_content.lower():
                return "Identified entity: John Doe (Person)"
            return "No specific entities identified in this basic example."

        return f"Basic analysis of document (length: {len(document_content)} chars): Key themes appear to be related to the initial content: '{document_content[:100]}...'. Further NLP processing would be needed for deeper insights."

    async def _arun(self, document_content: str, analysis_focus: Optional[str] = None) -> str:
        return self._run(document_content=document_content, analysis_focus=analysis_focus)

# Example usage (not typically run directly, but for testing)
if __name__ == '__main__':
    doc_tool = DocumentAnalysisTool()

    print("--- Document Analysis Tool ---")
    sample_doc = "The quick brown fox jumps over the lazy dog. This is the second sentence."
    print(f"Input doc: {sample_doc}")
    print(f"Default analysis: {doc_tool._run(document_content=sample_doc)}")
    print(f"Summarize focus: {doc_tool._run(document_content=sample_doc, analysis_focus='summarize')}")
    print(f"Entity focus: {doc_tool._run(document_content=sample_doc + ' Report by John Doe.', analysis_focus='extract_entities')}")
