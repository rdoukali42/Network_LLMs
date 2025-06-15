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
from .base_agent import BaseAgent

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
                # Anna AI Assistant system prompt - facilitates getting solution FROM employee
                system_prompt = f"""You are Anna, an AI assistant calling {employee_data.get('full_name', 'Unknown')} to get their help with a support ticket. Your role is to:

1. INTRODUCE yourself: "Hi, this is Anna, the AI assistant from IT support"
2. EXPLAIN the ticket problem clearly to the employee
3. ASK the employee for their expert solution and recommendations
4. GUIDE them to provide specific steps, commands, or procedures
5. CLARIFY any unclear parts of their solution
6. END THE CALL when you have received a complete solution

You are calling {employee_data.get('full_name', 'Unknown')}, who is a {employee_data.get('role_in_company', 'Employee')} with expertise in: {employee_data.get('expertise', 'General IT')}

Ticket Details:
- Submitted by: {ticket_data.get('user', 'Unknown user')}
- Description: {ticket_data.get('description', 'No description')}
- Category: {ticket_data.get('category', 'General')}
- Priority: {ticket_data.get('priority', 'Medium')}

IMPORTANT: You are Anna calling the REAL employee. You need their expertise to solve this ticket. Ask them directly: "Can you help me understand how to solve this?" or "What would you recommend for this issue?" 

If the employee asks about who submitted the ticket, you can tell them it was submitted by {ticket_data.get('user', 'a user')}.

When you have received a complete solution with specific steps from the employee, politely say: "Thank you! I have all the information I need. You can end the call now and I'll document your solution."

Wait for the employee to speak and provide their solution. Keep your questions brief and focused on getting their expert input."""
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
    
    @observe()
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process vocal call for assigned ticket."""
        try:
            print(f"🎤 VocalAssistant processing voice call...")
            
            # Extract input data
            ticket_data = input_data.get("ticket_data", {})
            employee_data = input_data.get("employee_data", {})
            call_action = input_data.get("action", "initiate_call")
            
            if call_action == "initiate_call":
                # Prepare call data for UI
                call_info = {
                    "ticket_id": ticket_data.get("id", "unknown"),
                    "employee_name": employee_data.get("full_name", "Unknown"),
                    "employee_username": employee_data.get("username", "unknown"),
                    "ticket_subject": ticket_data.get("subject", "No subject"),
                    "call_status": "incoming"
                }
                
                return {
                    "agent": self.name,
                    "status": "call_initiated",
                    "action": "start_call",
                    "call_info": call_info,
                    "result": f"Voice call initiated with {employee_data.get('full_name', 'Unknown')} for ticket {ticket_data.get('id', 'unknown')}"
                }
            
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
        """Transcribe audio bytes to text using SpeechRecognition."""
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
            
            # Transcribe using speech_recognition with error handling
            with sr.AudioFile(tmp_file_path) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language='en-US')
                
                # Clean up
                os.unlink(tmp_file_path)
                return text
            
        except sr.UnknownValueError:
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            return "Sorry, I couldn't understand the audio. Please speak clearly."
        except sr.RequestError as e:
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            return f"Speech recognition service error: {e}"
        except Exception as e:
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            return f"Error processing audio: {e}"
    
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
