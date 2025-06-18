"""
HRAgent - Employee matching and assignment agent.
"""

from typing import Dict, Any, List
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langfuse import observe
from .base_agent import BaseAgent


class HRAgent(BaseAgent):
    """Agent specialized in finding the best employee to handle tickets when documents don't have answers."""
    
    def __init__(self, config: Dict[str, Any] = None, tools: List[BaseTool] = None, availability_tool=None):
        super().__init__("HRAgent", config, tools)
        self.availability_tool = availability_tool
        
        # Create agent executor with tools if available
        if self.llm and self.tools:
            self.agent_executor = self._create_agent_executor()
        else:
            self.agent_executor = None
    
    def _create_agent_executor(self):
        """Create an agent executor with tools."""
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.get_system_prompt()),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ])
            
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        except Exception as e:
            print(f"⚠️ Failed to create HR agent executor: {e}")
            return None

    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        query = input_data.get("query", "")
        
        try:
            print(f"👥 HRAgent finding expert for: {query}")
            
            # Get available employees (automatically filtered by AvailabilityTool)
            if self.availability_tool:
                available_employees = self.availability_tool.get_available_employees()
            else:
                return {
                    "agent": self.name,
                    "status": "error",
                    "result": "No availability tool configured"
                }
            
            # Find best match
            best_match_data = self._find_best_employee_match(query, available_employees)
            
            if best_match_data:
                return {
                    "agent": self.name,
                    "status": "success",
                    "action": "assign",
                    "employee_data": best_match_data,
                    "result": self._format_employee_recommendation(best_match_data),
                    "query": query
                }
            else:
                return {
                    "agent": self.name,
                    "status": "success",
                    "action": "no_assignment",
                    "result": "No suitable employees available at the moment",
                    "query": query
                }
                
        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "result": f"HR Agent failed: {e}"
            }
    
    def _find_best_employee_match(self, query: str, available_employees: Dict) -> Dict:
        """Find the best employee match for the query using improved domain-aware matching."""
        # Combine available and busy employees (busy can handle urgent issues)
        candidates = available_employees["available"] + available_employees["busy"]
        
        if not candidates:
            return None
        
        # Improved keyword matching with domain awareness
        query_lower = query.lower()
        
        # Define domain-specific keywords and their domains
        domain_keywords = {
            'ml': ['model', 'classification', 'algorithm', 'machine learning', 'neural', 'deep learning', 
                   'training', 'prediction', 'dataset', 'feature', 'mlops', 'pytorch', 'tensorflow',
                   'regression', 'clustering', 'supervised', 'unsupervised', 'ai', 'artificial intelligence'],
            'ui_ux': ['design', 'interface', 'user experience', 'prototype', 'wireframe', 'figma', 
                     'usability', 'accessibility', 'responsive', 'frontend', 'ui', 'ux'],
            'data': ['data', 'analysis', 'visualization', 'dashboard', 'sql', 'database', 'analytics',
                    'reporting', 'statistics', 'pandas', 'excel', 'powerbi'],
            'backend': ['api', 'server', 'database', 'backend', 'python', 'javascript', 'django',
                       'deployment', 'infrastructure', 'microservices'],
            'product': ['product', 'roadmap', 'requirements', 'specification', 'agile', 'scrum',
                       'stakeholder', 'business', 'strategy', 'kpi']
        }
        
        # Detect query domain
        detected_domains = []
        for domain, keywords in domain_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                detected_domains.append(domain)
        
        # Extract meaningful keywords (filter out noise)
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
                     'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had',
                     'do', 'does', 'did', 'will', 'would', 'could', 'should', 'can', 'may',
                     'i', 'you', 'he', 'she', 'it', 'we', 'they', 'a', 'an', 'this', 'that',
                     'these', 'those', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
        
        meaningful_keywords = [word for word in query_lower.split() 
                              if len(word) > 2 and word not in stop_words]
        
        # Score employees based on improved relevance
        scored_candidates = []
        for employee in candidates:
            score = 0
            role = employee.get('role_in_company', '').lower()
            expertise = employee.get('expertise', '').lower()
            responsibilities = employee.get('responsibilities', '').lower()
            
            # Domain-specific scoring - huge bonus for domain experts
            employee_domains = []
            if any(term in role + expertise for term in ['machine learning', 'ml', 'data scientist']):
                employee_domains.append('ml')
            if any(term in role + expertise for term in ['ui', 'ux', 'design']):
                employee_domains.append('ui_ux')
            if any(term in role + expertise for term in ['data analyst', 'analytics']):
                employee_domains.append('data')
            if any(term in role + expertise for term in ['software engineer', 'backend', 'api']):
                employee_domains.append('backend')
            if any(term in role + expertise for term in ['product manager', 'product']):
                employee_domains.append('product')
            
            # Give massive bonus for domain match
            for domain in detected_domains:
                if domain in employee_domains:
                    score += 50  # Domain expert gets huge advantage
            
            # Keyword-based scoring (improved)
            for keyword in meaningful_keywords:
                if keyword in role:
                    score += 5
                if keyword in expertise:
                    score += 8
                if keyword in responsibilities:
                    score += 3
                    
            # Additional domain keyword bonuses
            for domain, keywords in domain_keywords.items():
                if domain in employee_domains:
                    for keyword in keywords:
                        if keyword in query_lower:
                            score += 10
            
            # Prefer available over busy
            if employee.get('availability_status') == 'Available':
                score += 2
            
            scored_candidates.append((score, employee))
        
        # Sort by score and get best match
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        if scored_candidates[0][0] > 0:  # At least some relevance
            return scored_candidates[0][1]
        else:
            # Return first available if no keyword matches
            if scored_candidates:
                return scored_candidates[0][1]
            return None
    
    def _format_employee_recommendation(self, employee: Dict) -> str:
        """Format employee recommendation for response."""
        status_emoji = {
            'Available': '🟢',
            'Busy': '🟡',
            'In Meeting': '🔴',
            'Do Not Disturb': '🔴'
        }.get(employee.get('availability_status', 'Unknown'), '❓')
        
        return f"""👤 **{employee.get('full_name', 'Unknown')}** (@{employee.get('username', 'unknown')})
🏢 **Role**: {employee.get('role_in_company', 'Not specified')}
💼 **Expertise**: {employee.get('expertise', 'Not specified')}
📋 **Responsibilities**: {employee.get('responsibilities', 'Not specified')}
{status_emoji} **Status**: {employee.get('availability_status', 'Unknown')}

This employee has the expertise to help with your request."""

    def get_system_prompt(self) -> str:
        return """You are HR Agent, specialized in matching support tickets with the most suitable available employees.

Your primary responsibilities:
- Analyze support ticket content to understand required expertise
- Search through available employees based on their roles, expertise, and responsibilities
- Match ticket requirements with employee capabilities
- Consider employee availability status when making recommendations
- Provide clear reasoning for employee recommendations

Key principles:
- Prioritize employees who are Available over those who are Busy
- Match technical expertise to technical problems
- Consider role compatibility with the ticket type
- Always provide the employee's contact information and current status
- Explain why this employee is the best match for the specific ticket

You help ensure every ticket gets routed to the right person, even when our documentation doesn't have the answer."""
