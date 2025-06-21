"""
HRAgent - Employee matching and assignment agent with Pydantic validation.
"""

from typing import Dict, Any, List, Optional
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import BaseTool
from langchain.prompts import ChatPromptTemplate
from langfuse import observe
from pydantic import ValidationError
import time
import json
import re
from datetime import datetime

from .base_agent import BaseAgent

# Try relative imports first, fall back to absolute imports
try:
    from ..models.hr_models import (
        HRTicketRequest,
        HREmployeeMatch,
        HRTicketResponse,
        HRAssignmentResponse,
        HRErrorResponse,
        HRSystemStatus
    )
    from ..models.common_models import StatusEnum
except ImportError:
    # Fallback to absolute imports for standalone execution
    from models.hr_models import (
        HRTicketRequest,
        HREmployeeMatch,
        HRTicketResponse,
        HRAssignmentResponse,
        HRErrorResponse,
        HRSystemStatus
    )
    from models.common_models import StatusEnum


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
            return AgentExecutor(agent=agent, tools=self.tools, verbose=False)
        except Exception as e:
            print(f"⚠️ Failed to create HR agent executor: {e}")
            return None

    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main entry point for HR Agent with Pydantic validation."""
        start_time = time.time()
        
        # DEBUG: Print input data
        # print(f"🔍 HR_AGENT DEBUG - INPUT:")
        # print(f"   Raw input: {input_data}")
        # print(f"   Input keys: {list(input_data.keys())}")
        
        try:
            # Validate and parse input data
            ticket_request = self._parse_ticket_request(input_data)
            
            # DEBUG: Print parsed ticket
            # print(f"   Parsed ticket ID: {ticket_request.ticket_id}")
            # print(f"   Parsed title: {ticket_request.title}")
            # print(f"   Parsed priority: {ticket_request.priority}")
            # print(f"   Parsed skills: {ticket_request.skills_required}")
            
            # print(f"🤖 HR Agent using AI-powered matching for ticket: {ticket_request.ticket_id}")
            
            # Get available employees
            if not self.availability_tool:
                return self._create_error_response(
                    "configuration_error",
                    "No availability tool configured",
                    ticket_request.ticket_id,
                    "configure_availability_tool"
                ).model_dump()
            
            available_employees = self.availability_tool.get_available_employees()
            
            # Use AI for employee matching instead of algorithm
            matches = self._find_employee_matches_with_ai(ticket_request, available_employees)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Create structured response
            response = HRTicketResponse(
                agent_name=self.name,
                ticket_id=ticket_request.ticket_id,
                matched_employees=matches,
                total_matches=len(matches),
                processing_time_ms=processing_time,
                matching_strategy="ai_powered_analysis",
                confidence_level=self._calculate_confidence(matches),
                recommended_assignment=matches[0].employee_id if matches else None,
                assignment_reasoning=matches[0].match_reasoning if matches else "No suitable matches found by AI"
            )
            
            # DEBUG: Print output details
            # print(f"🎯 HR_AGENT DEBUG - AI OUTPUT:")
            # print(f"   Status: {response.status}")
            # print(f"   Total matches found: {response.total_matches}")
            # print(f"   Processing time: {response.processing_time_ms:.1f}ms")
            # print(f"   Confidence level: {response.confidence_level:.2f}")
            # print(f"   Recommended assignment: {response.recommended_assignment}")
            if matches:
                best_match = matches[0]
                # print(f"   Best match: {best_match.name} (AI Score: {best_match.overall_score:.2f})")
                # print(f"   AI reasoning: {best_match.match_reasoning[:100]}...")
                # print(f"   Best match status: {best_match.availability_status}")
            else:
                print(f"   AI found no suitable matches for query")
            
            return response.model_dump()
                
        except ValidationError as e:
            return self._create_validation_error_response(e, input_data.get("ticket_id")).model_dump()
        except Exception as e:
            return self._create_error_response(
                "processing_error",
                f"HR Agent AI processing failed: {str(e)}",
                input_data.get("ticket_id"),
                "retry_request"
            ).model_dump()
    
    def _parse_ticket_request(self, input_data: Dict[str, Any]) -> HRTicketRequest:
        """Parse and validate input data into HRTicketRequest model."""
        # Handle legacy input format
        if "query" in input_data and "ticket_id" not in input_data:
            # Convert legacy format
            query = input_data["query"]
            ticket_data = {
                "ticket_id": input_data.get("ticket_id", f"ticket_{int(time.time())}"),
                "title": query[:100] if len(query) > 100 else query,
                "description": query,
                "priority": input_data.get("priority", "medium"),
                "category": input_data.get("category"),
                "department": input_data.get("department"),
                "skills_required": input_data.get("skills_required", []),
                "urgency_level": input_data.get("urgency_level", 3)
            }
        else:
            ticket_data = input_data
        
        return HRTicketRequest(**ticket_data)
    
    def _find_employee_matches_with_ai(self, ticket: HRTicketRequest, available_employees: Dict) -> List[HREmployeeMatch]:
        """Use AI to analyze and match employees to the ticket."""
        # Combine available and busy employees (busy can handle urgent issues)
        candidates = available_employees.get("available", []) + available_employees.get("busy", [])
        
        # DEBUG: Print availability data
        # print(f"🤖 AI MATCHING: Available employees: {len(available_employees.get('available', []))}")
        # print(f"🤖 AI MATCHING: Busy employees: {len(available_employees.get('busy', []))}")
        # print(f"🤖 AI MATCHING: Total candidates: {len(candidates)}")
        
        if not candidates:
            print(f"🤖 AI MATCHING: ⚠️ No candidates available for AI analysis")
            return []
        
        # Format employee data for AI
        employee_profiles = []
        for emp in candidates:
            profile = {
                "id": str(emp.get('id', emp.get('username', 'unknown'))),
                "name": emp.get('full_name', 'Unknown'),
                "username": emp.get('username', 'unknown'),
                "role": emp.get('role_in_company', ''),
                "expertise": emp.get('expertise', ''),
                "department": emp.get('department', ''),
                "responsibilities": emp.get('responsibilities', ''),
                "availability_status": emp.get('availability_status', 'Unknown'),
                "workload_level": emp.get('workload_level', 50)
            }
            employee_profiles.append(profile)
        
        # AI prompt for employee matching
        prompt = f"""You are an expert HR matching system tasked with matching support tickets to the best employees.

TICKET DETAILS:
Title: {ticket.title}
Description: {ticket.description}
Priority: {ticket.priority}

AVAILABLE EMPLOYEES:
{json.dumps(employee_profiles, indent=2)}

TASK: Follow this strict workflow:

1. TICKET ANALYSIS PHASE:
- Interpret "{ticket.description}" to identify:
  • Core problem type (technical/human/ambiguous)
  • Actual required expertise (vs mentioned keywords)
  • Hidden needs based on context
- Create POTENTIAL TICKET: 
  {{
    "true_problem": "Extracted core issue", 
    "critical_expertise": ["essential","skills"],
    "secondary_factors": ["department","urgency"]
  }}

2. MATCHING PHASE:
For each employee:
- Calculate BASE SCORE (0-100):
  70% weight: Match between POTENTIAL TICKET's "critical_expertise" and employee skills
  30% weight: Alignment with POTENTIAL TICKET's "true_problem" based on historical tickets solved
- Apply BONUS/PENALTY:
  +15%: Available AND workload < 60% capacity
  -10%: Missing ≥2 critical skills
- FINAL SCORE = (BASE SCORE + adjustments) capped at 100 (1.0)

3. SELECTION RULES:
- Must have ≥60% BASE SCORE to qualify
- Prioritize expertise over availability: Available candidates get preference ONLY when final scores are within 10 points
- If no BASE SCORE ≥60 exists, select top expert regardless of availability

Return a JSON array of the TOP 3 BEST MATCHES in this exact format:
[
    {{
        "employee_id": "1",
        "employee_username": "username1",
        "employee_name": "Full Name",
        "overall_score": 0.95,
        "skill_match_score": 0.90,
        "availability_score": 1.0,
        "workload_score": 0.80,
        "department_match_score": 0.85,
        "matching_skills": ["skill1", "skill2", "skill3"],
        "missing_skills": ["missing1", "missing2"],
        "match_reasoning": "Detailed explanation of why this employee is perfect for this specific issue. Focus on technical expertise and problem alignment."
    }}
]

CRITICAL RULES:
- All scores must be between 0.0 and 1.0 (0-100%)
- The POTENTIAL TICKET must be created before any matching
- Scores represent percentages (0-100)
- Never sacrifice expertise for availability
- For ambiguous tickets, POTENTIAL TICKET must identify the most probable intent
- Only return valid JSON, no additional text
- Ensure employee_id matches the id field from the employee data
- Ensure always include employee_username and that it matches the username field from the employee data"""
        
        try:
            # print(f"🤖 AI MATCHING: Sending request to AI for employee analysis...")
            # print(f"🤖 AI MATCHING: Query - {ticket.title}: {ticket.description}")
            
            # Use the LLM for AI matching if available
            if not self.llm:
                # print(f"🤖 AI MATCHING: ❌ No LLM configured, falling back to basic matching")
                return self._fallback_basic_matching(ticket, candidates)
            
            ai_response = self.llm.invoke(prompt)
            ai_content = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
            
            # print(f"🤖 AI MATCHING: Raw AI response length: {len(ai_content)} characters")
            # print(f"🤖 AI MATCHING: AI response preview: {ai_content}")
            
            # Extract JSON from AI response
            json_str = self._extract_json_from_response(ai_content)
            if json_str:
                try:
                    ai_matches = json.loads(json_str)
                    # print(f"🤖 AI MATCHING: Successfully parsed {len(ai_matches)} AI matches")
                except json.JSONDecodeError as e:
                    print(f"🤖 AI MATCHING: ❌ JSON parsing error: {e}")
                    return self._fallback_basic_matching(ticket, candidates)
            else:
                print(f"🤖 AI MATCHING: Failed to extract JSON from AI response")
                return self._fallback_basic_matching(ticket, candidates)
            
            # Convert AI matches to HREmployeeMatch objects
            matches = []
            for i, match_data in enumerate(ai_matches):
                try:
                    # Find the full employee data
                    employee_data = None
                    target_id = str(match_data.get('employee_id', ''))
                    target_username = match_data.get('employee_username', '')
                    
                    for emp in candidates:
                        emp_id = str(emp.get('id', ''))
                        emp_username = emp.get('username', '')
                        if emp_id == target_id or emp_username == target_username:
                            employee_data = emp
                            break
                    
                    if not employee_data:
                        print(f"🤖 AI MATCHING: Warning - Employee {target_id}/{target_username} not found")
                        continue
                    
                    # Create HREmployeeMatch object with AI data
                    employee_match = HREmployeeMatch(
                        employee_id=str(employee_data.get('id', match_data.get('employee_id', f'ai_match_{i}'))),
                        username=match_data.get('employee_username', employee_data.get('username', 'unknown')),
                        name=match_data.get('employee_name', employee_data.get('full_name', 'Unknown')),
                        email=employee_data.get('email', 'unknown@company.com'),
                        department=employee_data.get('department', 'Unknown'),
                        skills=match_data.get('matching_skills', []),
                        availability_status=employee_data.get('availability_status', 'Unknown'),
                        workload_level=int(employee_data.get('workload_level', 50)),
                        overall_score=float(match_data.get('overall_score', 0.0)),
                        skill_match_score=float(match_data.get('skill_match_score', 0.0)),
                        availability_score=float(match_data.get('availability_score', 0.0)),
                        workload_score=float(match_data.get('workload_score', 0.0)),
                        department_match_score=float(match_data.get('department_match_score', 0.0)),
                        matching_skills=match_data.get('matching_skills', []),
                        missing_skills=match_data.get('missing_skills', []),
                        match_reasoning=match_data.get('match_reasoning', 'AI-powered match')
                    )
                    
                    matches.append(employee_match)
                    # print(f"🤖 AI MATCHING: ✅ Created match for {employee_match.name} (AI Score: {employee_match.overall_score:.2f})")
                    
                except (ValueError, KeyError, TypeError) as e:
                    print(f"🤖 AI MATCHING: ❌ Error creating match for {match_data}: {e}")
                    continue
            
            # print(f"🤖 AI MATCHING: Successfully created {len(matches)} AI-powered employee matches")
            return matches
            
        except json.JSONDecodeError as e:
            print(f"🤖 AI MATCHING: ❌ JSON parsing error: {e}")
            return self._fallback_basic_matching(ticket, candidates)
        except Exception as e:
            print(f"🤖 AI MATCHING: ❌ General error in AI matching: {e}")
            return self._fallback_basic_matching(ticket, candidates)
    
    def _fallback_basic_matching(self, ticket: HRTicketRequest, candidates: List[Dict]) -> List[HREmployeeMatch]:
        """Fallback basic matching when AI fails."""
        print(f"🔄 FALLBACK: Using basic matching as AI fallback")
        
        matches = []
        for emp in candidates[:3]:  # Return first 3 as basic fallback
            try:
                employee_match = HREmployeeMatch(
                    employee_id=str(emp.get('id', emp.get('username', 'unknown'))),
                    username=emp.get('username', 'unknown'),
                    name=emp.get('full_name', 'Unknown'),
                    email=emp.get('email', 'unknown@company.com'),
                    department=emp.get('department', 'Unknown'),
                    skills=[],
                    availability_status=emp.get('availability_status', 'Unknown'),
                    workload_level=int(emp.get('workload_level', 50)),
                    overall_score=0.5,
                    skill_match_score=0.5,
                    availability_score=1.0 if emp.get('availability_status') == 'Available' else 0.5,
                    workload_score=0.5,
                    department_match_score=0.5,
                    matching_skills=[],
                    missing_skills=[],
                    match_reasoning="Basic fallback match - AI analysis unavailable"
                )
                matches.append(employee_match)
            except Exception as e:
                print(f"🔄 FALLBACK: Error in basic matching for {emp.get('full_name', 'Unknown')}: {e}")
                continue
        
        return matches
    
    def _score_employee_match(self, ticket: HRTicketRequest, employee: Dict) -> HREmployeeMatch:
        """Score how well an employee matches a ticket using enhanced algorithm."""
        # Extract employee information with proper validation
        raw_id = employee.get('id') or employee.get('username') or employee.get('emp_id')
        employee_id = str(raw_id) if raw_id is not None else 'unknown'
        
        name = str(employee.get('full_name', 'Unknown'))
        email = str(employee.get('email', 'unknown@company.com'))
        department = str(employee.get('department', 'Unknown'))
        role = str(employee.get('role_in_company', '')).lower()
        expertise = str(employee.get('expertise', '')).lower()
        responsibilities = str(employee.get('responsibilities', '')).lower()
        availability = str(employee.get('availability_status', 'Unknown'))
        
        # Handle workload_level with validation
        try:
            workload = int(employee.get('workload_level', 50))
            if workload < 0 or workload > 100:
                workload = 50  # Default to 50% if invalid
        except (ValueError, TypeError):
            workload = 50
        
        # DEBUG: Print employee being scored
        print(f"     Scoring {name} (ID: {employee_id}): role='{role}', expertise='{expertise[:30]}...', status={availability}")
        
        # Get all employee skills/keywords
        employee_skills = self._extract_employee_skills(employee)
        
        # Calculate individual scores
        skill_score = self._calculate_skill_match_score(ticket, employee_skills, role, expertise, responsibilities)
        availability_score = self._calculate_availability_score(availability)
        workload_score = self._calculate_workload_score(workload)
        department_score = self._calculate_department_match_score(ticket.department, department)
        
        # Calculate overall score (weighted average)
        overall_score = (
            skill_score * 0.5 +
            availability_score * 0.25 +
            workload_score * 0.15 +
            department_score * 0.1
        )
        
        # DEBUG: Print detailed scoring
        # print(f"       Skills: {skill_score:.2f}, Avail: {availability_score:.2f}, Workload: {workload_score:.2f}, Dept: {department_score:.2f} -> Overall: {overall_score:.2f}")
        
        # Find matching and missing skills
        matching_skills, missing_skills = self._analyze_skill_gaps(ticket.skills_required, employee_skills)
        
        # Generate reasoning
        reasoning = self._generate_match_reasoning(
            name, skill_score, availability_score, workload_score, 
            department_score, matching_skills, missing_skills
        )
        
        # Create HREmployeeMatch with error handling
        try:
            return HREmployeeMatch(
                employee_id=employee_id,
                name=name,
                email=email,
                department=department,
                skills=employee_skills,
                availability_status=availability,
                workload_level=workload,
                overall_score=overall_score,
                skill_match_score=skill_score,
                availability_score=availability_score,
                workload_score=workload_score,
                department_match_score=department_score,
                matching_skills=matching_skills,
                missing_skills=missing_skills,
                match_reasoning=reasoning
            )
        except ValidationError as e:
            # Log validation error and create a fallback match
            print(f"     ❌ Validation error for employee {employee_id}: {e}")
            print(f"     Employee data: {employee}")
            
            # Create fallback match with minimal valid data
            return HREmployeeMatch(
                employee_id=employee_id,
                name=name,
                email=email,
                department=department,
                skills=[],
                availability_status="Unknown",
                workload_level=50,
                overall_score=0.0,
                skill_match_score=0.0,
                availability_score=0.0,
                workload_score=0.0,
                department_match_score=0.0,
                matching_skills=[],
                missing_skills=[],
                match_reasoning=f"Validation error for {name} - using fallback data"
            )
    
    def _extract_employee_skills(self, employee: Dict) -> List[str]:
        """Extract all relevant skills from employee data."""
        skills = []
        
        # Get explicit skills if available
        if 'skills' in employee:
            if isinstance(employee['skills'], list):
                skills.extend(employee['skills'])
            elif isinstance(employee['skills'], str):
                skills.extend([s.strip() for s in employee['skills'].split(',')])
        
        # Extract skills from role, expertise, and responsibilities
        text_fields = [
            employee.get('role_in_company', ''),
            employee.get('expertise', ''),
            employee.get('responsibilities', '')
        ]
        
        # Domain-specific skill extraction
        domain_keywords = {
            'ml': ['machine learning', 'ml', 'neural', 'deep learning', 'pytorch', 'tensorflow',
                   'regression', 'classification', 'clustering', 'ai', 'data science'],
            'ui_ux': ['ui', 'ux', 'design', 'figma', 'prototype', 'wireframe', 'frontend'],
            'data': ['sql', 'database', 'analytics', 'pandas', 'excel', 'powerbi', 'tableau'],
            'backend': ['api', 'python', 'javascript', 'django', 'flask', 'microservices'],
            'product': ['product management', 'agile', 'scrum', 'roadmap', 'stakeholder']
        }
        
        combined_text = ' '.join(text_fields).lower()
        for domain, keywords in domain_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    skills.append(keyword)
        
        return list(set(skills))  # Remove duplicates
    
    def _calculate_skill_match_score(self, ticket: HRTicketRequest, employee_skills: List[str], 
                                   role: str, expertise: str, responsibilities: str) -> float:
        """Calculate skill matching score between ticket and employee."""
        # Combine ticket text for analysis
        ticket_text = f"{ticket.title} {ticket.description}".lower()
        
        # Extract keywords from ticket
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
                     'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had'}
        
        ticket_keywords = [word for word in ticket_text.split() 
                          if len(word) > 2 and word not in stop_words]
        
        # Domain detection
        domain_keywords = {
            'ml': ['model', 'classification', 'algorithm', 'machine learning', 'neural', 'deep learning'],
            'ui_ux': ['design', 'interface', 'user experience', 'prototype', 'wireframe', 'figma'],
            'data': ['data', 'analysis', 'visualization', 'dashboard', 'sql', 'database'],
            'backend': ['api', 'server', 'database', 'backend', 'python', 'javascript'],
            'product': ['product', 'roadmap', 'requirements', 'specification', 'agile']
        }
        
        detected_domains = []
        for domain, keywords in domain_keywords.items():
            if any(keyword in ticket_text for keyword in keywords):
                detected_domains.append(domain)
        
        score = 0.0
        max_possible_score = 100.0
        
        # Domain expertise matching (high weight)
        employee_text = f"{role} {expertise} {responsibilities}".lower()
        for domain in detected_domains:
            domain_skills = domain_keywords[domain]
            if any(skill in employee_text for skill in domain_skills):
                score += 40  # High score for domain match
        
        # Keyword matching
        for keyword in ticket_keywords:
            if keyword in employee_text or keyword in [s.lower() for s in employee_skills]:
                score += 5
        
        # Required skills matching
        if ticket.skills_required:
            matching_required = sum(1 for skill in ticket.skills_required 
                                  if any(skill.lower() in emp_skill.lower() for emp_skill in employee_skills))
            if ticket.skills_required:
                score += (matching_required / len(ticket.skills_required)) * 30
        
        return min(score / max_possible_score, 1.0)
    
    def _calculate_availability_score(self, availability: str) -> float:
        """Calculate availability score based on status."""
        availability_scores = {
            'Available': 1.0,
            'Busy': 0.6,
            'In Meeting': 0.3,
            'Do Not Disturb': 0.1,
            'Offline': 0.0
        }
        return availability_scores.get(availability, 0.5)
    
    def _calculate_workload_score(self, workload_level: Optional[int]) -> float:
        """Calculate workload score (lower workload = higher score)."""
        if workload_level is None:
            return 0.5
        return max(0.0, (100 - workload_level) / 100.0)
    
    def _calculate_department_match_score(self, ticket_dept: Optional[str], employee_dept: str) -> float:
        """Calculate department matching score."""
        if not ticket_dept or not employee_dept:
            return 0.5  # Neutral score if no department info
        
        if ticket_dept.lower() == employee_dept.lower():
            return 1.0
        
        # Partial match for related departments
        related_departments = {
            'engineering': ['development', 'software', 'tech'],
            'product': ['business', 'strategy', 'management'],
            'design': ['ui', 'ux', 'creative'],
            'data': ['analytics', 'science', 'research']
        }
        
        ticket_dept_lower = ticket_dept.lower()
        employee_dept_lower = employee_dept.lower()
        
        for main_dept, related in related_departments.items():
            if main_dept in ticket_dept_lower or any(r in ticket_dept_lower for r in related):
                if main_dept in employee_dept_lower or any(r in employee_dept_lower for r in related):
                    return 0.7
        
        return 0.3  # Low score for unrelated departments
    
    def _analyze_skill_gaps(self, required_skills: List[str], employee_skills: List[str]) -> tuple:
        """Analyze matching and missing skills."""
        if not required_skills:
            return employee_skills[:5], []  # Return top 5 employee skills
        
        matching = []
        missing = []
        
        employee_skills_lower = [s.lower() for s in employee_skills]
        
        for required in required_skills:
            if any(required.lower() in emp_skill for emp_skill in employee_skills_lower):
                matching.append(required)
            else:
                missing.append(required)
        
        return matching, missing
    
    def _generate_match_reasoning(self, name: str, skill_score: float, availability_score: float,
                                workload_score: float, dept_score: float, 
                                matching_skills: List[str], missing_skills: List[str]) -> str:
        """Generate human-readable reasoning for the match."""
        reasons = []
        
        if skill_score > 0.7:
            reasons.append(f"Strong skill match (score: {skill_score:.2f})")
        elif skill_score > 0.4:
            reasons.append(f"Good skill match (score: {skill_score:.2f})")
        else:
            reasons.append(f"Moderate skill match (score: {skill_score:.2f})")
        
        if availability_score >= 0.8:
            reasons.append("Currently available")
        elif availability_score >= 0.5:
            reasons.append("Limited availability but can assist")
        else:
            reasons.append("Low availability")
        
        if workload_score > 0.7:
            reasons.append("Low current workload")
        elif workload_score > 0.4:
            reasons.append("Moderate workload")
        else:
            reasons.append("High workload but capable")
        
        if matching_skills:
            reasons.append(f"Matching skills: {', '.join(matching_skills[:3])}")
        
        if missing_skills:
            reasons.append(f"May need support with: {', '.join(missing_skills[:2])}")
        
        return f"{name} is recommended because: " + "; ".join(reasons)
    
    def _calculate_confidence(self, matches: List[HREmployeeMatch]) -> float:
        """Calculate overall confidence in the matching results."""
        if not matches:
            return 0.0
        
        best_score = matches[0].overall_score
        if best_score > 0.8:
            return 0.9
        elif best_score > 0.6:
            return 0.7
        elif best_score > 0.4:
            return 0.5
        else:
            return 0.3
    
    def _create_error_response(self, error_type: str, message: str, 
                             ticket_id: Optional[str] = None, 
                             suggested_action: Optional[str] = None) -> HRErrorResponse:
        """Create structured error response."""
        return HRErrorResponse(
            agent_name=self.name,
            error_type=error_type,
            error_message=message,
            ticket_id=ticket_id,
            failed_operation="employee_matching",
            suggested_action=suggested_action
        )
    
    def _create_validation_error_response(self, validation_error: ValidationError, 
                                        ticket_id: Optional[str] = None) -> HRErrorResponse:
        """Create error response for validation failures."""
        error_details = []
        for error in validation_error.errors():
            error_details.append(f"{error['loc'][0]}: {error['msg']}")
        
        return HRErrorResponse(
            agent_name=self.name,
            error_type="validation_error",
            error_message=f"Input validation failed: {'; '.join(error_details)}",
            ticket_id=ticket_id,
            failed_operation="input_validation",
            suggested_action="check_input_format"
        )
    
    def assign_ticket(self, ticket_id: str, employee_id: str, assignment_reason: str = None) -> Dict[str, Any]:
        """Assign a ticket to a specific employee with structured response."""
        try:
            # In a real implementation, this would update the database
            # For now, we'll create a mock assignment response
            
            # Get employee details (mock implementation)
            employee_name = f"Employee_{employee_id}"  # In real implementation, fetch from DB
            
            response = HRAssignmentResponse(
                agent_name=self.name,
                ticket_id=ticket_id,
                assigned_employee_id=employee_id,
                assigned_employee_name=employee_name,
                assignment_confidence=0.8,  # Would be calculated based on match quality
                assignment_reason=assignment_reason or "Manual assignment requested",
                estimated_completion_time="2-3 business days"
            )
            
            return response.model_dump()
            
        except Exception as e:
            error_response = self._create_error_response(
                "assignment_error",
                f"Failed to assign ticket: {str(e)}",
                ticket_id,
                "retry_assignment"
            )
            return error_response.model_dump()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get HR system status with structured response."""
        try:
            # In a real implementation, this would query the database
            # For now, return mock status
            
            if self.availability_tool:
                available_employees = self.availability_tool.get_available_employees()
                total_available = len(available_employees.get("available", []))
                total_busy = len(available_employees.get("busy", []))
                total_offline = len(available_employees.get("offline", []))
                total_employees = total_available + total_busy + total_offline
            else:
                total_employees = total_available = total_busy = total_offline = 0
            
            status = HRSystemStatus(
                total_employees=total_employees,
                available_employees=total_available,
                busy_employees=total_busy,
                offline_employees=total_offline,
                database_connection=self.availability_tool is not None
            )
            
            return status.model_dump()
            
        except Exception as e:
            error_response = self._create_error_response(
                "status_error",
                f"Failed to get system status: {str(e)}",
                suggested_action="check_system_health"
            )
            return error_response.model_dump()

    def _format_employee_recommendation(self, employee_match: HREmployeeMatch) -> str:
        """Format employee recommendation for backward compatibility."""
        status_emoji = {
            'Available': '🟢',
            'Busy': '🟡',
            'In Meeting': '🔴',
            'Do Not Disturb': '🔴'
        }.get(employee_match.availability_status, '❓')
        
        return f"""👤 **{employee_match.name}** (@{employee_match.employee_id})
🏢 **Department**: {employee_match.department}
💼 **Skills**: {', '.join(employee_match.skills[:5])}
� **Match Score**: {employee_match.overall_score:.2f}
{status_emoji} **Status**: {employee_match.availability_status}

**Why this match?** {employee_match.match_reasoning}

**Matching Skills**: {', '.join(employee_match.matching_skills) if employee_match.matching_skills else 'General expertise'}
{f"**May need help with**: {', '.join(employee_match.missing_skills[:3])}" if employee_match.missing_skills else ""}"""

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

    def run_legacy(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy interface for backward compatibility during transition."""
        # Get the new structured response
        new_response = self.run(input_data)
        
        # Convert to legacy format
        if new_response.get("status") == "success":
            matched_employees = new_response.get("matched_employees", [])
            recommended_assignment = new_response.get("recommended_assignment")
            
            if matched_employees and recommended_assignment:
                # Find the recommended employee
                recommended_employee = next(
                    (emp for emp in matched_employees if emp["employee_id"] == recommended_assignment),
                    matched_employees[0] if matched_employees else None
                )
                
                if recommended_employee:
                    # Convert to legacy employee data format
                    legacy_employee_data = {
                        "id": recommended_employee["employee_id"],
                        "username": recommended_employee["employee_id"],
                        "full_name": recommended_employee["name"],
                        "email": recommended_employee["email"],
                        "department": recommended_employee["department"],
                        "role_in_company": f"Score: {recommended_employee['overall_score']:.2f}",
                        "expertise": ", ".join(recommended_employee["skills"][:3]),
                        "responsibilities": recommended_employee["match_reasoning"],
                        "availability_status": recommended_employee["availability_status"]
                    }
                    
                    return {
                        "agent": self.name,
                        "status": "success",
                        "action": "assign",
                        "employee_data": legacy_employee_data,
                        "result": self._format_employee_recommendation(recommended_employee),
                        "query": input_data.get("query", input_data.get("description", ""))
                    }
            
            # No assignment case
            return {
                "agent": self.name,
                "status": "success", 
                "action": "no_assignment",
                "result": "No suitable employees available at the moment",
                "query": input_data.get("query", input_data.get("description", ""))
            }
        else:
            # Error case
            return {
                "agent": self.name,
                "status": "error",
                "error": new_response.get("error_message", "Unknown error"),
                "result": f"HR Agent failed: {new_response.get('error_message', 'Unknown error')}"
            }
    
    def _extract_json_from_response(self, content: str) -> str:
        """Extract JSON from AI response, handling markdown code blocks and various formats."""
        if not content:
            raise ValueError("Empty response content")
        
        # First, try to find JSON inside markdown code blocks
        markdown_patterns = [
            r'```json\s*(.*?)\s*```',  # ```json ... ```
            r'```\s*(.*?)\s*```',      # ``` ... ``` (generic code block)
        ]
        
        for pattern in markdown_patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                candidate = match.group(1).strip()
                if candidate and (candidate.startswith('[') or candidate.startswith('{')):
                    return candidate
        
        # If no markdown blocks found, try to extract JSON array directly
        json_match = re.search(r'\[.*\]', content, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # Try to extract JSON object
        json_obj_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_obj_match:
            return json_obj_match.group(0)
        
        # If nothing found, return the content as-is and let JSON parser handle the error
        return content.strip()
