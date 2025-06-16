#!/usr/bin/env python3
"""
Smooth Vocal Google Gemini Chat App - FIXED VERSION
A simplified Streamlit app for seamless voice conversation with Google Gemini.
Uses reliable Streamlit components and proper session state management.
"""
import os
import io
import tempfile
import streamlit as st
import requests
import json
import base64
import time
from datetime import datetime
import speech_recognition as sr
from pathlib import Path
from audio_recorder_streamlit import audio_recorder

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
    """Google Gemini 1.5 Flash integration."""
    
    def __init__(self):
        self.api_key = "AIzaSyD-tvahGE1_oPquWN20h1lpdBcdZ7fUXlk"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    def chat(self, message: str, is_ticket_owner: bool = True, conversation_history: list = None) -> str:
        """Send message to Gemini and get response with conversation context."""
        try:
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key
            }
            
            if is_ticket_owner:
                # Ticket owner role-play system prompt
                system_prompt = """You are role-playing as Alex, a software developer who submitted an urgent support ticket. Your problem: You need permission to use React for a front-end webpage project, but you're not sure if it's allowed by company policy.

Your persona:
- Name: Alex (Software Developer)  
- Problem: Need approval to use React.js for front-end development
- Tone: Slightly stressed but professional, eager to get approval quickly
- Background: Working on a new project with tight deadlines

IMPORTANT: Remember our conversation history. Don't repeat your introduction if we've already talked. Be natural and responsive to what has been discussed. Only introduce yourself at the very beginning of the call. Keep responses natural, conversational, and under 3 sentences."""
            else:
                # IT Support agent system prompt for solution generation
                system_prompt = """You are an experienced IT support agent writing a professional ticket resolution. Based on the conversation about React.js permission request, provide a clear, authoritative solution that includes:

1. Decision on the request (approved/denied/conditional)
2. Technical reasoning
3. Any necessary steps or requirements
4. Policy references if relevant

Write in a professional, helpful tone suitable for a support ticket response."""
            
            # Build conversation context
            conversation_context = ""
            if conversation_history and len(conversation_history) > 0:
                conversation_context = "\n\nPrevious conversation:\n"
                for speaker, msg in conversation_history[-6:]:  # Last 6 exchanges to keep context manageable
                    conversation_context += f"{speaker}: {msg}\n"
                conversation_context += f"\nIT Support: {message}\nAlex:"
            else:
                conversation_context = f"\n\nIT Support: {message}\nAlex:"
            
            data = {
                "contents": [{
                    "parts": [{"text": f"{system_prompt}{conversation_context}"}]
                }],
                "generationConfig": {
                    "temperature": 0.8,
                    "maxOutputTokens": 150 if is_ticket_owner else 300
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
    """Main vocal chat application with smooth user experience."""
    
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
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.record(source)
                
                # Try Google Speech Recognition
                text = self.recognizer.recognize_google(audio, language='en-US')
                
                # Clean up
                os.unlink(tmp_file_path)
                return text
            
        except sr.UnknownValueError:
            # Clean up file if it exists
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            return "Sorry, I couldn't understand the audio. Please speak clearly."
        except sr.RequestError as e:
            # Clean up file if it exists
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            return f"Speech recognition service error: {e}"
        except Exception as e:
            # Clean up file if it exists
            try:
                os.unlink(tmp_file_path)
            except:
                pass
            return f"Error processing audio: {e}"
    
    def process_voice_input(self, audio_bytes, is_ticket_owner: bool = True, conversation_history: list = None) -> tuple:
        """Process voice input and return transcription and response."""
        # Transcribe audio
        transcription = self.transcribe_audio(audio_bytes)
        
        if "Sorry" in transcription or "Error" in transcription:
            return transcription, None, None
        
        # Get Gemini response with conversation context
        response = self.gemini.chat(transcription, is_ticket_owner, conversation_history)
        
        # Generate TTS audio only for ticket owner responses
        tts_audio_bytes = None
        if is_ticket_owner:
            tts_audio_bytes = self.tts.synthesize_speech(response)
        
        return transcription, response, tts_audio_bytes


def main():
    """Main Streamlit app for Ticket Owner Simulation."""
    st.set_page_config(
        page_title="IT Support Call Simulation", 
        page_icon="📞",
        layout="centered"
    )
    
    # Hide Streamlit UI elements for cleaner look
    hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
            
            /* Phone Component Styles */
            .phone-container {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
            }
            
            .phone {
                width: 100px;
                height: 180px;
                background: linear-gradient(145deg, #2c3e50, #34495e);
                border-radius: 15px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.3);
                position: relative;
                cursor: pointer;
                transition: all 0.3s ease;
                border: 2px solid #7f8c8d;
            }
            
            .phone:hover {
                transform: translateY(-3px) scale(1.05);
                box-shadow: 0 15px 30px rgba(0,0,0,0.4);
                border-color: #27ae60;
            }
            
            .phone-clickable {
                cursor: pointer;
            }
            
            .phone-clickable:hover .phone-icon {
                color: #2ecc71;
                transform: scale(1.2);
            }
            
            .phone-screen {
                width: 80px;
                height: 140px;
                background: #1a1a1a;
                border-radius: 10px;
                margin: 10px auto 0;
                position: relative;
                overflow: hidden;
            }
            
            .phone-content {
                padding: 10px;
                text-align: center;
                color: white;
                height: 100%;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
            }
            
            .phone-icon {
                font-size: 30px;
                margin-bottom: 8px;
                color: #27ae60;
                animation: pulse 2s infinite;
            }
            
            .phone-text {
                font-size: 8px;
                color: #ecf0f1;
                font-weight: bold;
                line-height: 1.2;
            }
            
            .phone-button {
                width: 25px;
                height: 25px;
                background: #27ae60;
                border-radius: 50%;
                margin: 8px auto 0;
                display: flex;
                justify-content: center;
                align-items: center;
                font-size: 12px;
                color: white;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .phone-button:hover {
                background: #2ecc71;
                transform: scale(1.1);
            }
            
            /* Call interface styles */
            .call-interface {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 300px;
                background: white;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                border: 2px solid #28a745;
                z-index: 1000;
                padding: 20px;
            }
            
            .call-header {
                text-align: center;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }
            
            .call-status {
                font-size: 14px;
                color: #28a745;
                font-weight: bold;
            }
            
            .caller-name {
                font-size: 16px;
                color: #333;
                margin-top: 5px;
            }
            
            @keyframes pulse {
                0% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.1); opacity: 0.7; }
                100% { transform: scale(1); opacity: 1; }
            }
            
            .ringing {
                animation: ring 0.5s infinite;
            }
            
            @keyframes ring {
                0%, 100% { transform: rotate(0deg); }
                25% { transform: rotate(-5deg); }
                75% { transform: rotate(5deg); }
            }
            
            /* Hide audio player controls */
            .stAudio {
                display: none !important;
            }
            
            audio {
                display: none !important;
            }
            </style>
            """
    st.markdown(hide_st_style, unsafe_allow_html=True)
    
    # Initialize session state
    if 'vocal_chat' not in st.session_state:
        st.session_state.vocal_chat = SmoothVocalChat()
    if 'last_audio_hash' not in st.session_state:
        st.session_state.last_audio_hash = None
    if 'conversation_turn' not in st.session_state:
        st.session_state.conversation_turn = 0
    if 'call_state' not in st.session_state:
        st.session_state.call_state = "pre_call"  # pre_call, during_call, post_call
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'greeting_given' not in st.session_state:
        st.session_state.greeting_given = False
    if 'solution_generated' not in st.session_state:
        st.session_state.solution_generated = False
    if 'show_phone' not in st.session_state:
        st.session_state.show_phone = False
    if 'call_active' not in st.session_state:
        st.session_state.call_active = False
    
    # Main layout
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Center the interface
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Main content - always show ticket info
        st.markdown("""
        <div style='text-align: center;'>
            <h1 style='color: #2E86AB; margin-bottom: 20px;'>📞 IT Support Call Simulation</h1>
            <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 20px 0;'>
                <h3 style='color: #dc3545;'>🔥 URGENT TICKET</h3>
                <p><strong>Ticket #3:</strong> Language Permission Request</p>
                <p><strong>Issue:</strong> "Can I use React in the front-end webpage?"</p>
                <p><strong>Reporter:</strong> Alex (Software Developer)</p>
                <p><strong>Priority:</strong> Urgent</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Show call button if no phone is showing
        if not st.session_state.show_phone and not st.session_state.call_active:
            if st.button("📞 Call Ticket Owner", key="phone_button", use_container_width=True):
                st.session_state.show_phone = True
                st.rerun()
        
        # Show conversation interface if call is active
        if st.session_state.call_active:
            st.markdown("### 🎤 Voice Conversation with Alex")
            st.markdown("""
            <div style='text-align: center; color: #666; margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-radius: 8px;'>
                <p><strong>🔊 Voice-Only Mode</strong><br>
                Listen to Alex and respond using the microphone below.<br>
                Conversation is audio-only for a more natural experience.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Voice recorder for IT support responses
            audio_bytes = audio_recorder(
                text="",
                recording_color="#ff4444", 
                neutral_color="#28a745",
                icon_name="microphone",
                icon_size="4x",
                pause_threshold=2.0,
                sample_rate=41000,
                key="call_mic"
            )
            
            # Process audio input
            if audio_bytes:
                audio_hash = hash(audio_bytes)
                
                if audio_hash != st.session_state.last_audio_hash:
                    st.session_state.last_audio_hash = audio_hash
                    
                    # Show processing status
                    with st.spinner("🔄 Processing..."):
                        transcription, response, tts_audio_bytes = st.session_state.vocal_chat.process_voice_input(
                            audio_bytes, 
                            is_ticket_owner=True, 
                            conversation_history=st.session_state.conversation_history
                        )
                    
                    # Auto-play Alex's response (no transcript shown)
                    if response and tts_audio_bytes:
                        st.audio(tts_audio_bytes, format='audio/mp3', autoplay=True)
                        
                        # Store conversation
                        st.session_state.conversation_history.append(("IT Support", transcription))
                        st.session_state.conversation_history.append(("Alex", response))
            
            # End call button
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                if st.button("📴 End Call & Generate Solution", key="end_call", use_container_width=True):
                    st.session_state.call_state = "post_call"
                    st.session_state.call_active = False
                    st.session_state.show_phone = False
                    st.rerun()

        # Show solution if generated
        if st.session_state.call_state == "post_call":
            st.markdown("### 📝 Ticket Resolution")
            
            if not st.session_state.solution_generated:
                # Generate solution based on conversation
                conversation_summary = "\n".join([f"{speaker}: {message}" for speaker, message in st.session_state.conversation_history])
                
                solution_prompt = f"""Based on this IT support call conversation about React.js permission:

{conversation_summary}

Generate a professional ticket resolution that addresses Alex's request to use React for front-end development."""
                
                with st.spinner("🔄 Generating ticket solution..."):
                    solution = st.session_state.vocal_chat.gemini.chat(solution_prompt, is_ticket_owner=False)
                    st.session_state.solution_generated = solution
            
            # Display the solution
            if st.session_state.solution_generated:
                st.markdown(f"""
                <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; margin: 15px 0; border-left: 5px solid #28a745;'>
                    <h4 style='color: #28a745; margin-bottom: 10px;'>✅ Ticket Resolution</h4>
                    <div style='background-color: white; padding: 15px; border-radius: 8px; font-size: 14px;'>
                        {st.session_state.solution_generated.replace('\n', '<br>')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Conversation history
            with st.expander("📋 View Full Conversation", expanded=False):
                for speaker, message in st.session_state.conversation_history:
                    speaker_icon = "📞" if speaker == "Alex" else "🎧"
                    st.markdown(f"**{speaker_icon} {speaker}:** {message}")
            
            # Reset button
            col_a, col_b, col_c = st.columns([1, 2, 1])
            with col_b:
                if st.button("🔄 Start New Simulation", key="reset", use_container_width=True):
                    # Reset all session state
                    for key in ['call_state', 'conversation_history', 'greeting_given', 'solution_generated', 'last_audio_hash', 'show_phone', 'call_active']:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.session_state.call_state = "pre_call"
                    st.rerun()

        st.markdown("""
        <div style='text-align: center; color: #666; margin-top: 20px;'>
            <p>Click the call button to start the simulation.<br>
            The AI will role-play as Alex seeking help with React permission.</p>
        </div>
        """, unsafe_allow_html=True)

    # Phone widget in bottom-right corner
    if st.session_state.show_phone and not st.session_state.call_active:
        # Use columns to position the button correctly
        col_left, col_right = st.columns([9, 1])
        
        with col_right:
            # Create the answer button positioned at bottom right
            st.markdown("""
            <style>
            .answer-phone-btn {
                position: fixed !important;
                bottom: 20px !important;
                right: 20px !important;
                width: 100px !important;
                height: 180px !important;
                background: transparent !important;
                border: none !important;
                z-index: 1001 !important;
                cursor: pointer !important;
                border-radius: 15px !important;
                padding: 0 !important;
                margin: 0 !important;
            }
            
            .answer-phone-btn:hover {
                background: rgba(39, 174, 96, 0.1) !important;
                border: 2px solid rgba(39, 174, 96, 0.3) !important;
            }
            
            .answer-phone-btn div {
                display: none !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Answer call button that will be positioned over the phone
            answer_clicked = st.button(
                "📞", 
                key="phone_answer_overlay",
                help="Click to answer Alex's call",
                use_container_width=False
            )
        
        # Phone component visual
        st.markdown("""
        <div class="phone-container">
            <div class="phone ringing phone-clickable" id="phone-device">
                <div class="phone-screen">
                    <div class="phone-content">
                        <div class="phone-icon">📞</div>
                        <div class="phone-text">Alex Calling<br>React Issue</div>
                        <div class="phone-text" style="font-size: 6px; margin-top: 5px; color: #27ae60;">👆 Tap to Answer</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # JavaScript to position the button exactly over the phone
        st.markdown("""
        <script>
        setTimeout(function() {
            // Find the answer button
            const buttons = document.querySelectorAll('button[data-testid="baseButton-secondary"]');
            let answerButton = null;
            
            buttons.forEach(btn => {
                if (btn.textContent.includes('📞') && btn.title && btn.title.includes('Alex')) {
                    answerButton = btn;
                }
            });
            
            if (answerButton) {
                // Style the button to overlay the phone exactly
                answerButton.style.position = 'fixed';
                answerButton.style.bottom = '20px';
                answerButton.style.right = '20px';
                answerButton.style.width = '100px';
                answerButton.style.height = '180px';
                answerButton.style.background = 'transparent';
                answerButton.style.border = 'none';
                answerButton.style.zIndex = '1001';
                answerButton.style.cursor = 'pointer';
                answerButton.style.borderRadius = '15px';
                answerButton.style.color = 'transparent';
                answerButton.style.fontSize = '0px';
                
                // Hide button text
                answerButton.innerHTML = '';
                
                // Add hover effect
                answerButton.onmouseenter = function() {
                    this.style.background = 'rgba(39, 174, 96, 0.1)';
                    this.style.border = '2px solid rgba(39, 174, 96, 0.3)';
                };
                
                answerButton.onmouseleave = function() {
                    this.style.background = 'transparent';
                    this.style.border = 'none';
                };
            }
        }, 200);
        </script>
        """, unsafe_allow_html=True)
        
        # Play ringing sound with hidden controls
        with open("/Users/level3/Desktop/LLM_Track/Network/Media/old_phone.mp3", "rb") as audio_file:
            audio_bytes = audio_file.read()
        
        # Use base64 encoding for HTML5 audio with hidden controls
        import base64
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        st.markdown(f"""
        <audio id="ringing-sound" autoplay loop style="display: none;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
        </audio>
        """, unsafe_allow_html=True)
        
        # Handle answer button click
        if answer_clicked:
            # Stop the ringing sound
            st.markdown("""
            <script>
            var audio = document.getElementById('ringing-sound');
            if (audio) audio.pause();
            </script>
            """, unsafe_allow_html=True)
            
            # Start call
            st.session_state.call_active = True
            st.session_state.show_phone = False
            
            # Generate dynamic greeting
            greeting_prompt = "IT Support has just answered your call. Introduce yourself and explain your React permission problem."
            greeting = st.session_state.vocal_chat.gemini.chat(
                greeting_prompt, 
                is_ticket_owner=True, 
                conversation_history=[]
            )
            
            # Store greeting in history
            st.session_state.conversation_history.append(("Alex", greeting))
            st.session_state.greeting_given = True
            st.rerun()

    # Active call interface in bottom-right corner
    if st.session_state.call_active:
        st.markdown(f"""
        <div class="call-interface">
            <div class="call-header">
                <div class="call-status">📞 CALL ACTIVE</div>
                <div class="caller-name">Alex (Developer)</div>
            </div>
            <div style="text-align: center; font-size: 12px; color: #666;">
                Use microphone above to respond
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Show Alex's greeting if just answered
        if st.session_state.greeting_given and len(st.session_state.conversation_history) == 1:
            greeting = st.session_state.conversation_history[0][1]
            
            # Generate TTS for greeting (no transcript shown)
            tts_audio_bytes = st.session_state.vocal_chat.tts.synthesize_speech(greeting)
            if tts_audio_bytes:
                st.audio(tts_audio_bytes, format='audio/mp3', autoplay=True)


if __name__ == "__main__":
    main()
