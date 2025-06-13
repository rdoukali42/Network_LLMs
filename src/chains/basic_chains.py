"""
Basic Langchain chains for the AI system.
"""

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import observe
from typing import Dict, Any


class QuestionAnsweringChain:
    """Chain for question answering with retrieved context."""
    
    def __init__(self, config: Dict[str, Any]):
        self.llm = ChatGoogleGenerativeAI(
            model=config['llm']['model'],
            temperature=config['llm']['temperature'],
            max_output_tokens=config['llm']['max_tokens']
        )
        
        self.prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
            You are an AI assistant that answers questions based on the provided context.
            Use only the information from the context to answer the question.
            If the context doesn't contain enough information, say so clearly.
            
            Context:
            {context}
            
            Question: {question}
            
            Answer:
            """
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    @observe()
    def run(self, context: str, question: str) -> str:
        """Run the question answering chain."""
        return self.chain.run(context=context, question=question)


class SummarizationChain:
    """Chain for document summarization."""
    
    def __init__(self, config: Dict[str, Any]):
        self.llm = ChatGoogleGenerativeAI(
            model=config['llm']['model'],
            temperature=config['llm']['temperature'],
            max_output_tokens=config['llm']['max_tokens']
        )
        
        self.prompt = PromptTemplate(
            input_variables=["text"],
            template="""
            Please provide a concise summary of the following text.
            Focus on the main points and key information.
            
            Text:
            {text}
            
            Summary:
            """
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    @observe()
    def run(self, text: str) -> str:
        """Run the summarization chain."""
        return self.chain.run(text=text)


class AnalysisChain:
    """Chain for text analysis and insights."""
    
    def __init__(self, config: Dict[str, Any]):
        self.llm = ChatGoogleGenerativeAI(
            model=config['llm']['model'],
            temperature=config['llm']['temperature'],
            max_output_tokens=config['llm']['max_tokens']
        )
        
        self.prompt = PromptTemplate(
            input_variables=["text", "analysis_type"],
            template="""
            Please perform a {analysis_type} analysis of the following text.
            Provide detailed insights and observations.
            
            Text:
            {text}
            
            Analysis:
            """
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    @observe()
    def run(self, text: str, analysis_type: str = "comprehensive") -> str:
        """Run the analysis chain."""
        return self.chain.run(text=text, analysis_type=analysis_type)
