#!/usr/bin/env python3
"""
Vocal Assistant Agent - Handles voice calls with assigned employees
Extracts voice components from smooth_vocal_gemini_fixed_copy.py and adapts for ticket system
"""
import os
import io
import tempfile
import requests
import json
import base64
import speech_recognition as sr
from typing import Dict, Any, List, Tuple, Optional

# Handle base agent import with fallback for standalone execution
try:
    from .base_agent import BaseAgent
except ImportError:
    # Fallback to absolute import for standalone execution
    from base_agent import BaseAgent

# Try to import langfuse decorators, fallback if not available
try:
    from langfuse import observe
except ImportError:
    # Fallback decorator if langfuse not available
    def observe():
        def decorator(func):
            return func
        return decorator

# Import TTS functionality
try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False


class VocalResponse:
    """Parse structured vocal assistant responses for redirect requests."""
    
    def __init__(self, conversation_data: Dict):
        self.redirect_requested = False
        self.redirect_employee_info = {}
        self.conversation_complete = False
        self.solution = ""
        
        self._parse_structured_response(conversation_data)
    
    def _parse_structured_response(self, conversation_data: Dict):
        """Parse structured response format from vocal assistant."""
        print(f"   🔍 VocalResponse: Starting to parse conversation data...")
        print(f"   🔍 VocalResponse: Conversation data keys: {list(conversation_data.keys())}")
        
        # Get the response text - adjust field name as needed
        response_text = conversation_data.get("response", "")
        if not response_text:
            response_text = conversation_data.get("conversation_summary", "")
        if not response_text:
            response_text = conversation_data.get("final_response", "")
        
        print(f"   🔍 VocalResponse: Response text length: {len(response_text) if response_text else 0}")
        if response_text:
            print(f"   🔍 VocalResponse: First 200 chars: {response_text[:200]}")
        
        if not response_text:
            print(f"   ⚠️ VocalResponse: No response text found!")
            return
        
        lines = response_text.split('\n')
        redirect_info = {}
        
        print(f"   🔍 VocalResponse: Processing {len(lines)} lines...")
        
        for i, line in enumerate(lines):
            line_upper = line.upper().strip()
            
            # Check for both structured and simple redirect patterns
            if "REDIRECT_REQUEST:" in line_upper:
                value = line.split(':', 1)[1].strip().upper()
                self.redirect_requested = (value == "YES")
                print(f"   🔄 VocalResponse: Found REDIRECT_REQUEST: {value} -> {self.redirect_requested}")
            elif "REDIRECT_REQUESTED:" in line_upper:
                # Handle both "REDIRECT_REQUESTED: True" and cases where it's embedded in text
                parts = line_upper.split("REDIRECT_REQUESTED:")
                if len(parts) > 1:
                    value = parts[1].strip()
                    # 🔧 FIX: Remove any formatting characters and check for TRUE
                    clean_value = value.replace('*', '').replace('-', '').replace('_', '').strip()
                    self.redirect_requested = (clean_value == "TRUE")
                    print(f"   🔄 VocalResponse: Found REDIRECT_REQUESTED: {value} -> {self.redirect_requested}")
                
            elif "USERNAME_TO_REDIRECT:" in line_upper:
                value = line.split(':', 1)[1].strip()
                # 🔧 FIX: Remove any formatting characters 
                clean_value = value.replace('*', '').replace('-', '').replace('_', '').strip()
                if clean_value.upper() != "NONE":
                    redirect_info["username"] = clean_value
                    print(f"   🔄 VocalResponse: Found USERNAME: {clean_value}")
                    
            elif "ROLE_OF_THE_REDIRECT_TO:" in line_upper:
                value = line.split(':', 1)[1].strip()
                # 🔧 FIX: Remove any formatting characters
                clean_value = value.replace('*', '').replace('-', '').replace('_', '').strip()
                if clean_value.upper() != "NONE":
                    redirect_info["role"] = clean_value
                    print(f"   🔄 VocalResponse: Found ROLE: {clean_value}")
                    
            elif "RESPONSABILTIES:" in line_upper or "RESPONSIBILITIES:" in line_upper:
                value = line.split(':', 1)[1].strip()
                # 🔧 FIX: Remove any formatting characters (but keep content)
                clean_value = value.replace('*', '').strip()
                if clean_value.upper() != "NONE":
                    redirect_info["responsibilities"] = clean_value
                    print(f"   🔄 VocalResponse: Found RESPONSIBILITIES: {clean_value}")
        
        # Store the parsed redirect information
        if self.redirect_requested and redirect_info:
            self.redirect_employee_info = redirect_info
            print(f"   ✅ VocalResponse: Redirect parsed successfully: {self.redirect_employee_info}")
        
        # If no redirect requested, mark conversation as complete
        if not self.redirect_requested:
            # Check for explicit completion markers  
            if any(marker in response_text.upper() for marker in [
                "CONVERSATION_COMPLETE: TRUE", 
                "CONVERSATION_COMPLETE: YES",
                "CALL_COMPLETE: TRUE",
                "CALL_COMPLETE: YES"
            ]):
                self.conversation_complete = True
            elif not any(marker in response_text.upper() for marker in [
                "REDIRECT_REQUEST:", "REDIRECT_REQUESTED:",
                "USERNAME_TO_REDIRECT:", "ROLE_OF_THE_REDIRECT_TO:"
            ]):
                # If no redirect markers found, assume conversation is complete
                self.conversation_complete = True
                
            # Extract solution/response details (everything after the headers)
            self.solution = self._extract_solution_text(response_text)
            print(f"   ✅ VocalResponse: Conversation complete, solution length: {len(self.solution)}")
        else:
            print(f"   🔄 VocalResponse: Redirect requested, not marking as complete")
    
    def _extract_solution_text(self, response_text: str) -> str:
        """Extract the solution/conversation details after the structured headers."""
        lines = response_text.split('\n')
        solution_lines = []
        headers_ended = False
        
        for line in lines:
            line_upper = line.upper().strip()
            
            # Skip structured header lines
            if any(header in line_upper for header in [
                "REDIRECT_REQUEST:", "USERNAME_TO_REDIRECT:", 
                "ROLE_OF_THE_REDIRECT_TO:", "RESPONSABILTIES:", "RESPONSIBILITIES:"
            ]):
                headers_ended = True
                continue
                
            # After headers, collect the solution text
            if headers_ended or (line.strip() and not any(header in line_upper for header in [
                "REDIRECT_REQUEST:", "USERNAME_TO_REDIRECT:", 
                "ROLE_OF_THE_REDIRECT_TO:", "RESPONSABILTIES:", "RESPONSIBILITIES:"
            ])):
                solution_lines.append(line)
        
        return '\n'.join(solution_lines).strip()
    
    def has_any_redirect_info(self) -> bool:
        """Check if any redirect information was provided."""
        return bool(self.redirect_employee_info)
    
    def get_redirect_criteria(self) -> Dict[str, str]:
        """Get the redirect criteria for employee search."""
        return self.redirect_employee_info.copy()


class CloudTTS:
    """Google Cloud Text-to-Speech client using REST API."""
    
    def __init__(self):
        self.api_key = "AIzaSyD-tvahGE1_oPquWN20h1lpdBcdZ7fUXlk"
        self.base_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        self.client = True
    
    def synthesize_speech(self, text: str) -> bytes:
        """Synthesize speech using Google Cloud TTS REST API."""
        try:
            # Limit text length
            if len(text) > 800:
                text = text[:800] + "..."
            
            payload = {
                "input": {"text": text},
                "voice": {
                    "languageCode": "en-US",
                    "name": "en-US-Chirp3-HD-Leda",
                    "ssmlGender": "FEMALE"
                },
                "audioConfig": {
                    "audioEncoding": "MP3",
                    "sampleRateHertz": 24000
                }
            }
            
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key
            }
            
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                audio_content = result.get('audioContent')
                if audio_content:
                    return base64.b64decode(audio_content)
            
            # Fallback to gTTS
            return self._fallback_tts(text)
            
        except Exception as e:
            return self._fallback_tts(text)
    
    def _fallback_tts(self, text: str) -> bytes:
        """Fallback to gTTS if Cloud TTS fails."""
        if not GTTS_AVAILABLE:
            return b""
        
        try:
            tts = gTTS(text=text, lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except:
            return b""


class GeminiChat:
    """Google Gemini 1.5 Flash integration for employee role-playing."""
    
    def __init__(self):
        self.api_key = "AIzaSyD-tvahGE1_oPquWN20h1lpdBcdZ7fUXlk"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    def chat(self, message: str, ticket_data: Dict, employee_data: Dict, is_employee: bool = True, conversation_history: List = None) -> str:
        """Send message to Gemini and get response with ticket and employee context."""
        try:
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            if is_employee:
                # Anna AI Assistant system prompt - conversation-aware and friendly
                system_prompt = f"""You are Anna, a friendly AI assistant having a natural conversation with {employee_data.get('full_name', 'Unknown')} about a support ticket. You speak in a warm, human-like tone.

IMPORTANT: You MUST start your response with these exact headers:

REDIRECT_REQUEST: [YES | NO]
USERNAME_TO_REDIRECT: [username or "NONE"]
ROLE_OF_THE_REDIRECT_TO: [role or "NONE"]
RESPONSABILTIES: [responsibilities or "NONE"]

Then provide your detailed response below the headers.

EXAMPLE RESPONSE FORMAT:
REDIRECT_REQUEST: YES
USERNAME_TO_REDIRECT: sarah
ROLE_OF_THE_REDIRECT_TO: "NONE"
RESPONSABILTIES: "NONE"

CONVERSATION FLOW:
- Always make sure to REDIRECT_REQUEST to YES only when the employee explicitly says they request a transfer.
- If this is the start of conversation: Introduce yourself warmly and explain the ticket
- If this is a follow-up: dont repeat the introduction, or say hi again, just continue the conversation
- If conversation has started: ALWAYS acknowledge what the employee just said, then respond naturally
- Be conversational, friendly, and expressive - use phrases like "That's interesting!", "Great point!", "I see what you mean"
- Only ask clarifying questions when absolutely necessary for ticket resolution
- Respect when employees give complete answers or want to move forward

Employee: {employee_data.get('full_name', 'Unknown')} - {employee_data.get('role_in_company', 'Employee')}
Expertise: {employee_data.get('expertise', 'General IT')}

Ticket Info:
- From: {ticket_data.get('user', 'Unknown user')}
- Issue: {ticket_data.get('description', 'No description')}
- Priority: {ticket_data.get('priority', 'Medium')}

REDIRECT SCENARIOS:
- If employee says they can't handle this issue, are the wrong person, or need someone else
- If they mention a specific colleague who should handle it instead
- If they say "this isn't my area" or "you need someone from [department/role]"
- If they ask to transfer or forward the ticket to another employee

CONVERSATION RULES:
1. ALWAYS respond to what they just said - acknowledge their input first
2. Only ask for more details if the solution is unclear or incomplete for the ticket
3. If they give clear answers, accept them gracefully: "That makes perfect sense, thank you!"
4. Be encouraging: "Perfect!", "That makes sense!", "Excellent suggestion!"
5. When you have a complete solution, say: "Wonderful! I think I have everything I need. Thank you so much for your help!"
6. If they request redirect, use the structured headers above and ask for specific details about who should handle it

RESPONSE FORMAT:
- Normal conversation: Just respond naturally
- Redirect requested: Start with the structured headers, then explain the redirect

TONE: Friendly, warm, conversational, appreciative of their expertise. Sound like a helpful colleague, not a robotic assistant."""
            else:
                # Solution generation system prompt - formats employee's solution professionally
                system_prompt = f"""You are an IT support documentation assistant. Based on the conversation between Anna (AI assistant) and {employee_data.get('full_name', 'Unknown')}, create a professional ticket resolution.

The employee {employee_data.get('full_name', 'Unknown')} ({employee_data.get('role_in_company', 'Employee')}) has provided their solution for:

Ticket: {ticket_data.get('subject', 'No subject')}
Issue: {ticket_data.get('description', 'No description')}

Your task is to format the employee's solution into a professional ticket response that includes:
1. The employee's recommended solution/decision
2. Any technical steps they provided
3. Professional formatting suitable for customer communication
4. Clear next steps or requirements

IMPORTANT: Base the solution primarily on what the employee said during the conversation. Do not add new technical details they didn't mention. Your job is to format and present their expertise professionally."""
            
            # Build conversation context
            conversation_context = ""
            if conversation_history and len(conversation_history) > 0:
                conversation_context = "\n\nPrevious conversation:\n"
                for speaker, msg in conversation_history[-30:]:  # Last 30 exchanges for extended memory
                    conversation_context += f"{speaker}: {msg}\n"
                conversation_context += f"\nUser: {message}\nAnna:"
            else:
                conversation_context = f"\n\nUser: {message}\nAnna:"
            
            data = {
                "contents": [{
                    "parts": [{"text": f"{system_prompt}{conversation_context}"}]
                }],
                "generationConfig": {
                    "temperature": 0.8,
                    "maxOutputTokens": 200 if is_employee else 400  # Increased for longer conversations
                }
            }
            
            response = requests.post(self.base_url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    return content.strip()
            
            return "Sorry, I couldn't process your request right now."
            
        except Exception as e:
            return f"Error: {str(e)}"


class VocalAssistantAgent(BaseAgent):
    """Agent specialized in handling voice calls with assigned employees."""
    
    def __init__(self, config: Dict[str, Any] = None, tools: List = None):
        super().__init__("VocalAssistant", config, tools)
        self.gemini = GeminiChat()
        self.tts = CloudTTS()
        self.recognizer = sr.Recognizer()
        # API key for Gemini transcription fallback
        self.api_key = "AIzaSyD-tvahGE1_oPquWN20h1lpdBcdZ7fUXlk"
    
    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process vocal call for assigned ticket."""
        try:
            print(f"\n🎤 VocalAssistant processing voice call...")
            print(f"   🔍 DEBUG: Input data keys: {list(input_data.keys())}")
            
            # Extract input data
            ticket_data = input_data.get("ticket_data", {})
            employee_data = input_data.get("employee_data", {})
            call_action = input_data.get("action", "initiate_call")
            
            print(f"   🔍 DEBUG: Call action: {call_action}")
            print(f"   🔍 DEBUG: Employee: {employee_data.get('full_name', 'Unknown')} ({employee_data.get('username', 'No username')})")
            print(f"   🔍 DEBUG: Ticket subject: {ticket_data.get('subject', 'No subject')}")
            print(f"   🔍 DEBUG: Ticket ID: {ticket_data.get('id', 'No ID')}")
            
            if call_action == "end_call":
                # Handle call completion and conversation analysis
                print(f"   📞 DEBUG: Processing CALL END...")
                
                conversation_data = input_data.get("conversation_data", {})
                conversation_summary = input_data.get("conversation_summary", "")
                call_duration = input_data.get("call_duration", "unknown")
                
                print(f"   📞 DEBUG: Call duration: {call_duration}")
                print(f"   📞 DEBUG: Conversation data available: {'Yes' if conversation_data else 'No'}")
                print(f"   📞 DEBUG: Conversation summary length: {len(conversation_summary)}")
                
                # Prepare the conversation analysis
                if conversation_summary:
                    # Use provided summary
                    final_conversation = conversation_summary
                elif conversation_data:
                    # Extract from conversation data
                    final_conversation = conversation_data.get("summary", conversation_data.get("response", ""))
                else:
                    # No conversation data available
                    final_conversation = "Call completed without conversation data"
                
                print(f"   📞 DEBUG: Final conversation length: {len(final_conversation)}")
                
                # 🆕 NEW: Analyze conversation for redirect requests
                if final_conversation and len(final_conversation.strip()) > 10:
                    print(f"   🔍 DEBUG: Analyzing conversation for redirect requests...")
                    redirect_analysis = self._analyze_conversation_for_redirect(final_conversation)
                    
                    if redirect_analysis.get("redirect_requested"):
                        print(f"   🔄 DEBUG: REDIRECT DETECTED in conversation!")
                        print(f"   🔄 DEBUG: Redirect info: {redirect_analysis.get('redirect_employee_info', {})}")
                        
                        # Add redirect markers to conversation summary for workflow detection
                        structured_summary = f"""REDIRECT_REQUESTED: True
USERNAME_TO_REDIRECT: {redirect_analysis.get('redirect_employee_info', {}).get('username', 'NONE')}
ROLE_OF_THE_REDIRECT_TO: {redirect_analysis.get('redirect_employee_info', {}).get('role', 'NONE')}
RESPONSIBILITIES: {redirect_analysis.get('redirect_employee_info', {}).get('responsibilities', 'NONE')}

ORIGINAL_CONVERSATION:
{final_conversation}"""
                        final_conversation = structured_summary
                        print(f"   🔄 DEBUG: Enhanced conversation with redirect markers")
                    else:
                        print(f"   ✅ DEBUG: No redirect detected in conversation")
                else:
                    print(f"   ⚠️ DEBUG: No conversation content to analyze for redirects")
                
                result = {
                    "agent": self.name,
                    "status": "call_completed",
                    "action": "end_call",
                    "conversation_summary": final_conversation,
                    "conversation_data": conversation_data,
                    "call_duration": call_duration,
                    "result": f"Voice call completed with {employee_data.get('full_name', 'Unknown')} for ticket {ticket_data.get('id', 'unknown')}"
                }
                
                print(f"   ✅ DEBUG: Call end result: {result}")
                print(f"   ✅ DEBUG: Status: {result.get('status')}")
                print(f"   ✅ DEBUG: Action: {result.get('action')}")
                return result
            
            if call_action == "initiate_call":
                # Prepare call data for UI
                call_info = {
                    "ticket_id": ticket_data.get("id", "unknown"),
                    "employee_name": employee_data.get("full_name", "Unknown"),
                    "employee_username": employee_data.get("username", "unknown"),
                    "ticket_subject": ticket_data.get("subject", "No subject"),
                    "call_status": "incoming"
                }
                
                print(f"   📋 DEBUG: Call info prepared: {call_info}")
                print(f"   📋 DEBUG: Returning call initiation info to workflow...")
                
                result = {
                    "agent": self.name,
                    "status": "call_initiated",
                    "action": "start_call",
                    "call_info": call_info,
                    "result": f"Voice call initiated with {employee_data.get('full_name', 'Unknown')} for ticket {ticket_data.get('id', 'unknown')}"
                }
                
                print(f"   ✅ DEBUG: VocalAssistant result: {result}")
                print(f"   ✅ DEBUG: Status: {result.get('status')}")
                print(f"   ✅ DEBUG: Action: {result.get('action')}")
                return result
            
            elif call_action == "initiate_redirect_call":
                redirect_reason = input_data.get("redirect_reason", {})
                print(f"   🔄 DEBUG: This is a REDIRECT call")
                print(f"   🔄 DEBUG: Redirect reason: {redirect_reason}")
                print(f"   🔄 DEBUG: Original employee requested redirect to: {employee_data.get('full_name', 'Unknown')}")
                
                # Similar to initiate_call but for redirected employee
                call_info = {
                    "ticket_id": ticket_data.get("id", "unknown"),
                    "employee_name": employee_data.get("full_name", "Unknown"),
                    "employee_username": employee_data.get("username", "unknown"),
                    "ticket_subject": ticket_data.get("subject", "No subject"),
                    "call_status": "redirected_incoming",
                    "redirect_reason": redirect_reason
                }
                
                result = {
                    "agent": self.name,
                    "status": "redirect_call_initiated",
                    "action": "start_redirect_call", 
                    "call_info": call_info,
                    "result": f"Redirect call initiated with {employee_data.get('full_name', 'Unknown')} for ticket {ticket_data.get('id', 'unknown')}"
                }
                
                print(f"   ✅ DEBUG: Redirect call result: {result}")
                return result
            
            elif call_action == "process_conversation":
                # Process conversation and generate solution
                conversation_history = input_data.get("conversation_history", [])
                
                # Generate professional solution from conversation
                conversation_summary = "\n".join([f"{speaker}: {message}" for speaker, message in conversation_history])
                
                solution = self.gemini.chat(
                    f"Generate a professional ticket resolution based on this conversation: {conversation_summary}",
                    ticket_data,
                    employee_data,
                    is_employee=False
                )
                
                return {
                    "agent": self.name,
                    "status": "call_completed",
                    "action": "solution_generated",
                    "solution": solution,
                    "conversation_history": conversation_history,
                    "result": "Voice call completed and solution generated"
                }
            
            else:
                return {
                    "agent": self.name,
                    "status": "error",
                    "result": f"Unknown call action: {call_action}"
                }
                
        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "result": f"VocalAssistant failed: {e}"
            }
    
    def transcribe_audio(self, audio_bytes) -> str:
        """Transcribe audio bytes to text using two-tier system: Google STT → Gemini AI recovery."""
        tmp_file_path = None
        try:
            # Save audio bytes to temporary file with .wav extension
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_file_path = tmp_file.name
            
            # Adjust recognizer settings for better accuracy
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
            self.recognizer.phrase_threshold = 0.3
            
            # Primary transcription using Google STT
            with sr.AudioFile(tmp_file_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language='en-US')
                
                # Clean up and return successful transcription
                os.unlink(tmp_file_path)
                return text
            
        except sr.UnknownValueError:
            # Google STT failed - try Gemini AI recovery
            print("🔄 Google STT failed, attempting Gemini AI transcription recovery...")
            try:
                transcription = self._transcribe_with_gemini(tmp_file_path if tmp_file_path else audio_bytes)
                if tmp_file_path and os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                return transcription
            except Exception as gemini_error:
                print(f"❌ Gemini transcription also failed: {gemini_error}")
                if tmp_file_path and os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                return "I'm having trouble understanding the audio. Could you please speak more clearly or try again?"
                
        except sr.RequestError as e:
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            return f"Speech recognition service error: {e}"
        except Exception as e:
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            return f"Error processing audio: {e}"
    
    def _transcribe_with_gemini(self, audio_input) -> str:
        """Use Gemini AI to transcribe audio when Google STT fails."""
        try:
            # Convert audio to base64 for Gemini API
            if isinstance(audio_input, str) and os.path.exists(audio_input):
                # Read from file path
                with open(audio_input, 'rb') as f:
                    audio_data = f.read()
            else:
                # Use audio bytes directly
                audio_data = audio_input
            
            # Convert to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            # Use Gemini's multimodal capabilities for audio transcription
            data = {
                "contents": [{
                    "parts": [
                        {"text": "Please transcribe this audio to text. Focus on extracting any spoken words, even if unclear. If you can make out partial words or phrases, include them with context. Return only the transcribed text without explanations."},
                        {
                            "inline_data": {
                                "mime_type": "audio/wav",
                                "data": audio_base64
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.1,  # Low temperature for accuracy
                    "maxOutputTokens": 150
                }
            }
            
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    transcription = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # Apply context-aware auto-correction
                    corrected_text = self._apply_context_correction(transcription)
                    
                    # print(f"✅ Gemini transcription successful: {corrected_text}")
                    return corrected_text
            
            # If Gemini API fails, return a helpful error
            raise Exception("Gemini API returned no valid transcription")
            
        except Exception as e:
            print(f"❌ Gemini transcription failed: {e}")
            raise e
    
    def _apply_context_correction(self, raw_transcription: str) -> str:
        """Apply context-aware correction to transcription using Gemini."""
        try:
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            correction_prompt = f"""Please correct any spelling errors, improve grammar, and enhance clarity in this transcribed text while preserving the original meaning. Focus on common speech-to-text errors like:
- Homophones (there/their, to/too/two)
- Technical terms that might be misheard
- Common words that sound similar
- Grammar issues from spoken language

Original transcription: "{raw_transcription}"

Return only the corrected text, no explanations."""
            
            data = {
                "contents": [{
                    "parts": [{"text": correction_prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 100
                }
            }
            
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent",
                headers=headers,
                json=data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    corrected = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    return corrected
                    
            # If correction fails, return original
            return raw_transcription
            
        except Exception as e:
            print(f"⚠️ Context correction failed, using raw transcription: {e}")
            return raw_transcription
    
    def process_voice_input(self, audio_bytes, ticket_data: Dict, employee_data: Dict, conversation_history: List = None) -> Tuple[str, str, Optional[bytes]]:
        """Process voice input and return transcription, response, and TTS audio."""
        # Transcribe audio
        transcription = self.transcribe_audio(audio_bytes)
        
        if "Sorry" in transcription or "Error" in transcription:
            return transcription, None, None
        
        # Get employee response using Gemini
        response = self.gemini.chat(transcription, ticket_data, employee_data, is_employee=True, conversation_history=conversation_history)
        
        # Generate TTS audio for employee response
        tts_audio_bytes = None
        if response:
            tts_audio_bytes = self.tts.synthesize_speech(response)
        
        return transcription, response, tts_audio_bytes
    
    def get_system_prompt(self) -> str:
        return """You are Vocal Assistant with Anna, an AI assistant that facilitates voice calls between IT support tickets and assigned employees.

Anna's primary responsibilities:
- Call assigned employees to get solutions for support tickets
- Explain ticket problems clearly to employees
- Guide employees to provide their expert solutions
- Extract complete solutions from employee conversations
- Format employee solutions into professional ticket responses
- End calls when complete solutions are obtained

Anna acts as a voice-enabled intermediary that connects human expertise with ticket resolution through natural conversation."""
    
    def _analyze_conversation_for_redirect(self, conversation_text: str) -> Dict[str, Any]:
        """Analyze conversation text to detect redirect requests and extract structured information."""
        print(f"   🔍 CONVERSATION ANALYSIS: Starting analysis...")
        print(f"   🔍 CONVERSATION ANALYSIS: Text length: {len(conversation_text)}")
        
        # AI prompt to analyze conversation for redirect requests
        analysis_prompt = f"""
Analyze this voice call conversation to detect if there was a redirect request.

CONVERSATION:
{conversation_text}

Look for patterns where:
1. Someone says they want to redirect, forward, transfer the call/ticket
2. Someone mentions another person's name to redirect to
3. Someone says another person would be better suited to handle this

If a redirect is requested, extract:
- The name/username of the person to redirect to
- Any role or department mentioned
- The reason for redirect

RESPOND IN THIS EXACT FORMAT:
REDIRECT_REQUESTED: [True/False]
USERNAME_TO_REDIRECT: [name or NONE]
ROLE_OF_THE_REDIRECT_TO: [role/department or NONE]
RESPONSIBILITIES: [reason for redirect or NONE]

EXAMPLES:
- "I meant redirect the call to sir" + "Sarah" → USERNAME_TO_REDIRECT: sarah
- "forward to DevOps team" → ROLE_OF_THE_REDIRECT_TO: DevOps
- "John would be better for this" → USERNAME_TO_REDIRECT: john

Be precise and only extract what is clearly mentioned.
The REDIRECT_REQUESTED is always False, unless a redirect is explicitly requested in the conversation.
"""

        try:
            # Use Gemini to analyze the conversation
            analysis_result = self.gemini.chat(
                analysis_prompt,
                {},  # No ticket data needed for analysis
                {},  # No employee data needed for analysis
                is_employee=False
            )
            
            print(f"   🔍 CONVERSATION ANALYSIS: AI result: {analysis_result[:200]}...")
            
            # Parse the structured response
            analysis_data = {"response": analysis_result}
            vocal_response = VocalResponse(analysis_data)
            
            redirect_info = {
                "redirect_requested": vocal_response.redirect_requested,
                "redirect_employee_info": vocal_response.redirect_employee_info
            }
            
            print(f"   🔍 CONVERSATION ANALYSIS: Parsed result: {redirect_info}")
            return redirect_info
            
        except Exception as e:
            print(f"   ❌ CONVERSATION ANALYSIS: Error analyzing conversation: {e}")
            return {"redirect_requested": False, "redirect_employee_info": {}}
