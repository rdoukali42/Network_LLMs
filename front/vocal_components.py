#!/usr/bin/env python3
"""
Vocal Components for Streamlit integration
Simplified voice chat components extracted from smooth_vocal_gemini_fixed_copy.py
"""
import os
import io
import tempfile
import requests
import json
import base64
import speech_recognition as sr
from typing import Dict, List, Tuple, Optional

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
                # Anna AI Assistant system prompt - conversation-aware and friendly
                system_prompt = f"""You are Anna, a friendly AI assistant having a natural conversation with {employee_data.get('full_name', 'Unknown')} about a support ticket. You speak in a warm, human-like tone.

CONVERSATION FLOW:
- If this is the start of conversation: Introduce yourself warmly and explain the ticket
- Dont mention that you are a friendly AI assistant
- If conversation has started: ALWAYS acknowledge what the employee just said, then ask follow-up questions
- Be conversational, friendly, and expressive - use phrases like "That's interesting!", "Great point!", "I see what you mean"
- Ask clarifying questions based on their responses
- Build on their expertise naturally

Employee: {employee_data.get('full_name', 'Unknown')} - {employee_data.get('role_in_company', 'Employee')}
Expertise: {employee_data.get('expertise', 'General IT')}

Ticket Info:
- From: {ticket_data.get('user', 'Unknown user')}
- Issue: {ticket_data.get('description', 'No description')}
- Priority: {ticket_data.get('priority', 'Medium')}

CONVERSATION RULES:
1. ALWAYS respond to what they just said - acknowledge their input first
2. If they mention tools/methods, ask for more details: "That sounds great! Can you tell me more about..."
3. If they give vague answers, gently probe: "Interesting! What specifically would you recommend..."
4. Be encouraging: "Perfect!", "That makes sense!", "Excellent suggestion!"
5. When you have a complete solution, say: "Wonderful! I think I have everything I need. Thank you so much for your help!"

TONE: Friendly, warm, conversational, appreciative of their expertise. Sound like a helpful colleague, not a robotic assistant."""
            else:
                # Solution generation system prompt - formats employee's solution professionally
                system_prompt = f"""You are an IT support documentation assistant. Based on the conversation between Anna (AI assistant) and {employee_data.get('full_name', 'Unknown')}, create a professional ticket resolution.

The employee {employee_data.get('full_name', 'Unknown')} has provided their solution for:

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


class SmoothVocalChat:
    """Main vocal chat application for ticket system integration."""
    
    def __init__(self):
        self.gemini = GeminiChat()
        self.tts = CloudTTS()
        self.recognizer = sr.Recognizer()
    
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
