"""
LLM-based evaluation system.
"""

from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langfuse import observe
import json


class LLMEvaluator:
    """Evaluates AI system outputs using another LLM as a judge."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Explicitly use Gemini Flash Pro for evaluation
        model_name = config.get('evaluation', {}).get('judge_model', 'gemini-1.5-flash')
        self.judge_llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.1  # Low temperature for consistent evaluation
        )
        self.metrics = config['evaluation']['metrics']
    
    @observe()
    def evaluate_response(self, query: str, response: str, reference: str = None) -> Dict[str, Any]:
        """Evaluate a single response."""
        results = {}
        
        for metric in self.metrics:
            if metric == "relevance":
                results[metric] = self._evaluate_relevance(query, response)
            elif metric == "accuracy":
                results[metric] = self._evaluate_accuracy(response, reference)
            elif metric == "completeness":
                results[metric] = self._evaluate_completeness(query, response)
            elif metric == "efficiency":
                results[metric] = self._evaluate_efficiency(response)
        
        return results
    
    @observe()
    def _evaluate_relevance(self, query: str, response: str) -> Dict[str, Any]:
        """Evaluate relevance of response to query."""
        prompt = PromptTemplate(
            input_variables=["query", "response"],
            template="""
            Evaluate how relevant the following response is to the given query.
            
            Query: {query}
            Response: {response}
            
            Rate the relevance on a scale of 1-10 where:
            1 = Completely irrelevant
            10 = Perfectly relevant
            
            Provide your rating and a brief explanation.
            
            IMPORTANT: Return ONLY a valid JSON object in this exact format (no markdown, no code blocks):
            {{"score": <number>, "explanation": "<text>"}}
            """
        )
        
        evaluation = self.judge_llm.invoke(prompt.format(query=query, response=response))
        return self._parse_evaluation(evaluation.content)
    
    @observe()
    def _evaluate_accuracy(self, response: str, reference: str = None) -> Dict[str, Any]:
        """Evaluate accuracy of response."""
        if not reference:
            return {"score": None, "explanation": "No reference provided"}
        
        prompt = PromptTemplate(
            input_variables=["response", "reference"],
            template="""
            Evaluate how accurate the following response is compared to the reference.
            
            Response: {response}
            Reference: {reference}
            
            Rate the accuracy on a scale of 1-10 where:
            1 = Completely inaccurate
            10 = Perfectly accurate
            
            Provide your rating and explanation.
            
            IMPORTANT: Return ONLY a valid JSON object in this exact format (no markdown, no code blocks):
            {{"score": <number>, "explanation": "<text>"}}
            """
        )
        
        evaluation = self.judge_llm.invoke(prompt.format(response=response, reference=reference))
        return self._parse_evaluation(evaluation.content)
    
    @observe()
    def _evaluate_completeness(self, query: str, response: str) -> Dict[str, Any]:
        """Evaluate completeness of response."""
        prompt = PromptTemplate(
            input_variables=["query", "response"],
            template="""
            Evaluate how complete the following response is for the given query.
            
            Query: {query}
            Response: {response}
            
            Rate the completeness on a scale of 1-10 where:
            1 = Very incomplete, missing major aspects
            10 = Completely comprehensive
            
            Provide your rating and explanation.
            
            IMPORTANT: Return ONLY a valid JSON object in this exact format (no markdown, no code blocks):
            {{"score": <number>, "explanation": "<text>"}}
            """
        )
        
        evaluation = self.judge_llm.invoke(prompt.format(query=query, response=response))
        return self._parse_evaluation(evaluation.content)
    
    @observe()
    def _evaluate_efficiency(self, response: str) -> Dict[str, Any]:
        """Evaluate efficiency (conciseness) of response."""
        prompt = PromptTemplate(
            input_variables=["response"],
            template="""
            Evaluate how efficient and concise the following response is.
            
            Response: {response}
            
            Rate the efficiency on a scale of 1-10 where:
            1 = Very verbose, lots of unnecessary information
            10 = Perfectly concise, no wasted words
            
            Provide your rating and explanation.
            
            IMPORTANT: Return ONLY a valid JSON object in this exact format (no markdown, no code blocks):
            {{"score": <number>, "explanation": "<text>"}}
            """
        )
        
        evaluation = self.judge_llm.invoke(prompt.format(response=response))
        return self._parse_evaluation(evaluation.content)
    
    def _parse_evaluation(self, evaluation_text: str) -> Dict[str, Any]:
        """Parse evaluation response into structured format."""
        try:
            # First try to parse as direct JSON
            return json.loads(evaluation_text.strip())
        except json.JSONDecodeError:
            try:
                # Try to extract JSON from markdown code blocks
                import re
                
                # Look for JSON within markdown code blocks
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', evaluation_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                    return json.loads(json_str)
                
                # Look for JSON-like content without code blocks
                json_match = re.search(r'(\{[^}]*"score"[^}]*\})', evaluation_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1).strip()
                    return json.loads(json_str)
                
                # Try to extract score and explanation separately if JSON parsing fails
                score_match = re.search(r'(?:score["\s]*:?\s*|score.*?is["\s]*|rate.*?)(\d+)', evaluation_text, re.IGNORECASE)
                explanation_match = re.search(r'(?:explanation["\s]*:?\s*["\']([^"\']*)["\']|explanation:\s*([^"\n]*)|explanation.*?["\']([^"\']*)["\'])', evaluation_text, re.IGNORECASE)
                
                # Also try simpler patterns for score
                if not score_match:
                    score_match = re.search(r'(\d+)', evaluation_text)
                
                if score_match:
                    score_val = int(score_match.group(1))
                    result = {"score": score_val}
                    
                    if explanation_match:
                        # Get the first non-None group from explanation match
                        exp_groups = [g for g in explanation_match.groups() if g is not None and g.strip()]
                        result["explanation"] = exp_groups[0].strip() if exp_groups else "No explanation provided"
                    else:
                        # Extract explanation from the text if no quotes found
                        lines = evaluation_text.split('\n')
                        explanation_lines = [line.strip() for line in lines if line.strip() and not line.strip().isdigit()]
                        result["explanation"] = ' '.join(explanation_lines) if explanation_lines else "No explanation provided"
                    return result
                
            except (json.JSONDecodeError, AttributeError, ValueError):
                pass
        
        # Fallback: return raw text with parse error flag
        return {
            "score": None,
            "explanation": evaluation_text,
            "parse_error": True
        }
    
    @observe()
    def compare_configurations(self, results_a: List[Dict], results_b: List[Dict]) -> Dict[str, Any]:
        """Compare results from two different configurations."""
        comparison = {
            "config_a_avg_scores": {},
            "config_b_avg_scores": {},
            "winner_by_metric": {},
            "overall_winner": None
        }
        
        # Calculate average scores for each configuration
        for metric in self.metrics:
            scores_a = [r.get(metric, {}).get('score', 0) for r in results_a if r.get(metric, {}).get('score') is not None]
            scores_b = [r.get(metric, {}).get('score', 0) for r in results_b if r.get(metric, {}).get('score') is not None]
            
            avg_a = sum(scores_a) / len(scores_a) if scores_a else 0
            avg_b = sum(scores_b) / len(scores_b) if scores_b else 0
            
            comparison["config_a_avg_scores"][metric] = avg_a
            comparison["config_b_avg_scores"][metric] = avg_b
            comparison["winner_by_metric"][metric] = "A" if avg_a > avg_b else "B"
        
        # Determine overall winner
        a_wins = sum(1 for winner in comparison["winner_by_metric"].values() if winner == "A")
        b_wins = sum(1 for winner in comparison["winner_by_metric"].values() if winner == "B")
        
        comparison["overall_winner"] = "A" if a_wins > b_wins else "B" if b_wins > a_wins else "Tie"
        
        return comparison
