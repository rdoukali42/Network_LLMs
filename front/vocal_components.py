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
            # print(f"🎤 TTS REQUEST: Synthesizing speech for text: '{text[:100]}{'...' if len(text) > 100 else ''}'")
            
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
                    # print(f"✅ TTS SUCCESS: Generated {len(base64.b64decode(audio_content))} bytes of audio")
                    return base64.b64decode(audio_content)
            
            print(f"⚠️ TTS API FAILED: Status {response.status_code}, falling back to gTTS")
            # Fallback to gTTS
            return self._fallback_tts(text)
            
        except Exception as e:
            print(f"❌ TTS ERROR: {e}, falling back to gTTS")
            return self._fallback_tts(text)
    
    def _fallback_tts(self, text: str) -> bytes:
        """Fallback to gTTS if Cloud TTS fails."""
        # print(f"🔄 TTS FALLBACK: Using gTTS for text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        if not GTTS_AVAILABLE:
            print("❌ gTTS not available, returning empty audio")
            return b""
        
        try:
            tts = gTTS(text=text, lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            audio_data = fp.read()
            # print(f"✅ gTTS SUCCESS: Generated {len(audio_data)} bytes of audio")
            return audio_data
        except Exception as e:
            print(f"❌ gTTS ERROR: {e}")
            return b""


class GeminiChat:
    """Google Gemini 1.5 Flash integration for employee role-playing."""
    
    def __init__(self):
        self.api_key = "AIzaSyD-tvahGE1_oPquWN20h1lpdBcdZ7fUXlk"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    def chat(self, message: str, ticket_data: Dict, employee_data: Dict, is_employee: bool = True, conversation_history: List = None) -> str:
        """Send message to Gemini and get response with ticket and employee context."""
        try:
            # print(f"🧠 GEMINI REQUEST: Chat request for {'employee conversation' if is_employee else 'solution generation'}")
            # print(f"   Message: '{message[:100]}{'...' if len(message) > 100 else ''}'")
            
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

CONVERSATION RULES:
1. ALWAYS respond to what they just said - acknowledge their input first
2. Only ask for more details if the solution is unclear or incomplete for the ticket
3. If they give clear answers, accept them gracefully: "That makes perfect sense, thank you!"
4. Be encouraging: "Perfect!", "That makes sense!", "Excellent suggestion!"
5. When you have a complete solution, say: "Wonderful! I think I have everything I need. Thank you so much for your help!"
6. SPECIAL HANDLING: If you receive unclear messages like "Please provide the audio" or "Please provide the audio file", treat this as a technical glitch and start the conversation naturally as you would when first contacting the employee about the ticket. Introduce yourself and explain why you're calling about this specific ticket.

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
                    # print(f"✅ GEMINI SUCCESS: Generated response: '{content[:100]}{'...' if len(content) > 100 else ''}'")
                    return content.strip()
            
            # print(f"⚠️ GEMINI API FAILED: Status {response.status_code}")
            return "Sorry, I couldn't process your request right now."
            
        except Exception as e:
            # print(f"❌ GEMINI ERROR: {str(e)}")
            return f"Error: {str(e)}"


class SmoothVocalChat:
    """Main vocal chat application for ticket system integration."""
    
    def __init__(self):
        self.gemini = GeminiChat()
        self.tts = CloudTTS()
        self.recognizer = sr.Recognizer()
        # API key for Gemini transcription fallback
        self.api_key = "AIzaSyD-tvahGE1_oPquWN20h1lpdBcdZ7fUXlk"
    
    def transcribe_audio(self, audio_bytes) -> str:
        """Transcribe audio bytes to text using two-tier system: Google STT → Gemini AI recovery."""
        # print(f"🎧 STT REQUEST: Starting transcription for {len(audio_bytes)} bytes of audio")
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
                # print("🔄 STT: Calling Google Speech Recognition API...")
                text = self.recognizer.recognize_google(audio, language='en-US')
                
                # print(f"✅ GOOGLE STT SUCCESS: '{text}'")
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
            print(f"❌ GOOGLE STT SERVICE ERROR: {e}")
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            return f"Speech recognition service error: {e}"
        except Exception as e:
            print(f"❌ STT GENERAL ERROR: {e}")
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
            return f"Error processing audio: {e}"
    
    def _transcribe_with_gemini(self, audio_input) -> str:
        """Use Gemini AI to transcribe audio when Google STT fails."""
        # print(f"🔄 GEMINI STT FALLBACK: Attempting Gemini AI transcription...")
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
            # print(f"📤 GEMINI STT: Sending {len(audio_base64)} chars of base64 audio to Gemini API...")
            
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
        print(f"🔧 CORRECTION REQUEST: Applying context correction to: '{raw_transcription}'")
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
                    print(f"✅ CORRECTION SUCCESS: '{raw_transcription}' → '{corrected}'")
                    return corrected
                    
            print(f"⚠️ CORRECTION API FAILED: Status {response.status_code}")
            # If correction fails, return original
            return raw_transcription
            
        except Exception as e:
            print(f"⚠️ Context correction failed, using raw transcription: {e}")
            return raw_transcription

    def process_voice_input(self, audio_bytes, ticket_data: Dict, employee_data: Dict, conversation_history: List = None) -> Tuple[str, str, Optional[bytes]]:
        # """Process voice input and return transcription, response, and TTS audio."""
        # print(f"\n🎯 VOICE PROCESSING: Starting complete voice input processing...")
        # print(f"   Audio size: {len(audio_bytes)} bytes")
        # print(f"   Ticket: {ticket_data.get('subject', 'No subject')}")
        # print(f"   Employee: {employee_data.get('full_name', 'Unknown')}")
        
        # Import streamlit to check session state
        try:
            import streamlit as st
            # Check if call is still active to prevent processing after END_CALL
            if not st.session_state.get('call_active', False):
                print("⏹️ CALL INACTIVE: Skipping processing as call is not active")
                return "Call has ended. No further processing.", None, None
        except:
            # If streamlit not available, continue processing
            pass
        
        # Transcribe audio
        transcription = self.transcribe_audio(audio_bytes)
        
        if "Sorry" in transcription or "Error" in transcription:
            print(f"❌ TRANSCRIPTION FAILED: {transcription}")
            return transcription, None, None
        
        # Double-check call state before generating response
        try:
            import streamlit as st
            if not st.session_state.get('call_active', False):
                return transcription, "Call has ended. No response generated.", None
        except:
            pass
        
        # Get employee response using Gemini
        response = self.gemini.chat(transcription, ticket_data, employee_data, is_employee=True, conversation_history=conversation_history)
        
        # Final check before TTS generation
        try:
            import streamlit as st
            if not st.session_state.get('call_active', False):
                return transcription, response, None  # Skip TTS if call ended
        except:
            pass
        
        # Generate TTS audio for employee response
        tts_audio_bytes = None
        if response:
            tts_audio_bytes = self.tts.synthesize_speech(response)
        
        return transcription, response, tts_audio_bytes
