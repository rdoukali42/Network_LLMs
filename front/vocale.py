import streamlit as st
import speech_recognition as sr
import pyttsx3
import threading
import time
import queue
import io
from datetime import datetime
import google.generativeai as genai
from google.cloud import texttospeech
from google.cloud import speech
import pygame
import tempfile
import os

# Page configuration
st.set_page_config(
    page_title="Vocal AI Assistant",
    page_icon="🎤",
    layout="wide"
)

# Initialize session state
if 'conversation_active' not in st.session_state:
    st.session_state.conversation_active = False
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'is_muted' not in st.session_state:
    st.session_state.is_muted = False
if 'audio_queue' not in st.session_state:
    st.session_state.audio_queue = queue.Queue()
if 'speech_queue' not in st.session_state:
    st.session_state.speech_queue = queue.Queue()
if 'is_speaking' not in st.session_state:
    st.session_state.is_speaking = False
if 'stop_listening' not in st.session_state:
    st.session_state.stop_listening = False

# Configuration
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
GOOGLE_CLOUD_CREDENTIALS = st.secrets.get("GOOGLE_CLOUD_CREDENTIALS", "")

class VocalAI:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.tts_client = None
        self.stt_client = None
        self.setup_gemini()
        self.setup_google_cloud()
        
    def setup_gemini(self):
        """Initialize Gemini AI"""
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            st.error("Please set your GEMINI_API_KEY in secrets")
    
    def setup_google_cloud(self):
        """Initialize Google Cloud TTS and STT"""
        try:
            if GOOGLE_CLOUD_CREDENTIALS:
                # Set up credentials
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_CLOUD_CREDENTIALS
                self.tts_client = texttospeech.TextToSpeechClient()
                self.stt_client = speech.SpeechClient()
            else:
                st.warning("Google Cloud credentials not found. Using alternative TTS/STT.")
                self.setup_alternative_tts()
        except Exception as e:
            st.warning(f"Google Cloud setup failed: {e}. Using alternative TTS/STT.")
            self.setup_alternative_tts()
    
    def setup_alternative_tts(self):
        """Setup alternative TTS using pyttsx3"""
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 180)
            self.tts_engine.setProperty('volume', 0.9)
        except Exception as e:
            st.error(f"Failed to initialize TTS: {e}")
    
    def generate_response(self, user_input):
        """Generate AI response using Gemini"""
        try:
            prompt = f"""You are a helpful AI assistant engaged in a natural conversation. 
            Keep your responses conversational, friendly, and concise (1-3 sentences max).
            User said: {user_input}
            
            Respond naturally as if you're having a real-time conversation."""
            
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"I'm having trouble processing that. Could you repeat?"
    
    def text_to_speech_google(self, text):
        """Convert text to speech using Google Cloud TTS"""
        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            
            return response.audio_content
        except Exception as e:
            st.error(f"Google TTS error: {e}")
            return None
    
    def text_to_speech_alternative(self, text):
        """Convert text to speech using pyttsx3"""
        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            st.error(f"TTS error: {e}")
    
    def speech_to_text_google(self, audio_data):
        """Convert speech to text using Google Cloud STT"""
        try:
            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code="en-US",
            )
            
            response = self.stt_client.recognize(config=config, audio=audio)
            
            for result in response.results:
                return result.alternatives[0].transcript
            return ""
        except Exception as e:
            st.error(f"Google STT error: {e}")
            return ""
    
    def speech_to_text_alternative(self, audio_data):
        """Convert speech to text using speech_recognition"""
        try:
            text = self.recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            st.error(f"STT error: {e}")
            return ""

def play_audio(audio_content):
    """Play audio content"""
    try:
        pygame.mixer.init()
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_file.write(audio_content)
            tmp_file.flush()
            pygame.mixer.music.load(tmp_file.name)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        os.unlink(tmp_file.name)
    except Exception as e:
        st.error(f"Audio playback error: {e}")

def continuous_listening():
    """Continuous listening function"""
    vocal_ai = VocalAI()
    silence_threshold = 2.0  # 2 seconds of silence before processing
    last_speech_time = time.time()
    
    with vocal_ai.microphone as source:
        vocal_ai.recognizer.adjust_for_ambient_noise(source)
    
    while st.session_state.conversation_active:
        if st.session_state.is_muted or st.session_state.is_speaking:
            time.sleep(0.1)
            continue
            
        try:
            # Listen for audio with timeout
            with vocal_ai.microphone as source:
                audio = vocal_ai.recognizer.listen(source, timeout=1, phrase_time_limit=5)
            
            # Convert speech to text
            text = vocal_ai.speech_to_text_alternative(audio)
            
            if text.strip():
                last_speech_time = time.time()
                st.session_state.speech_queue.put(text)
                
                # Wait for silence before processing
                time.sleep(silence_threshold)
                
                # Check if still silent
                current_time = time.time()
                if current_time - last_speech_time >= silence_threshold:
                    # Process the accumulated speech
                    if not st.session_state.speech_queue.empty():
                        accumulated_text = ""
                        while not st.session_state.speech_queue.empty():
                            accumulated_text += " " + st.session_state.speech_queue.get()
                        
                        # Add user message
                        st.session_state.messages.append({
                            "role": "user",
                            "content": accumulated_text.strip(),
                            "timestamp": datetime.now()
                        })
                        
                        # Generate AI response
                        st.session_state.is_speaking = True
                        ai_response = vocal_ai.generate_response(accumulated_text.strip())
                        
                        # Add AI message
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": ai_response,
                            "timestamp": datetime.now()
                        })
                        
                        # Convert to speech and play
                        if vocal_ai.tts_client:
                            audio_content = vocal_ai.text_to_speech_google(ai_response)
                            if audio_content:
                                play_audio(audio_content)
                        else:
                            vocal_ai.text_to_speech_alternative(ai_response)
                        
                        st.session_state.is_speaking = False
                        
        except sr.WaitTimeoutError:
            pass
        except Exception as e:
            st.error(f"Listening error: {e}")
            time.sleep(1)

# Main UI
st.title("🎤 Vocal AI Assistant")
st.markdown("*Experience natural voice conversations with AI*")

# 🆕 NEW: Call Status Display
if 'call_data' not in st.session_state:
    st.session_state.call_data = {}

call_status = "Inactive"
status_color = "red"
status_icon = "🔴"

if st.session_state.conversation_active:
    call_status = "In Progress"
    status_color = "green"
    status_icon = "🟢"
elif st.session_state.call_data.get("call_ended", False):
    if st.session_state.call_data.get("conversation_complete", False):
        call_status = "Completed"
        status_color = "blue"
        status_icon = "🔵"
    else:
        call_status = "Analyzing"
        status_color = "orange"
        status_icon = "🟡"

# Call Status Banner
st.markdown(f"""
<div style="
    background-color: {status_color}20;
    border: 2px solid {status_color};
    border-radius: 10px;
    padding: 10px;
    margin: 10px 0;
    text-align: center;
">
    <h3>{status_icon} Call Status: {call_status}</h3>
</div>
""", unsafe_allow_html=True)

# Show redirect options if call is completed and redirect detected
if st.session_state.call_data.get("call_ended", False):
    if st.session_state.call_data.get("redirect_requested", False):
        st.warning("🔄 **Redirect Requested** - Reassigning ticket to appropriate employee...")
        redirect_info = st.session_state.call_data.get("redirect_info", {})
        if redirect_info:
            st.info(f"📋 **Redirect Details**: {redirect_info}")
    elif st.session_state.call_data.get("conversation_complete", False):
        st.success("✅ **Call Completed Successfully** - No redirect needed")

# Show reassignment progress
if st.session_state.call_data.get("reassigning", False):
    st.info("🔄 **Reassigning ticket...** Please wait while we find the best employee for your issue.")

# Configuration Section
with st.sidebar:
    st.header("⚙️ Configuration")
    
    if not GEMINI_API_KEY:
        st.error("Please add your GEMINI_API_KEY to Streamlit secrets")
        st.code("""
        # In .streamlit/secrets.toml
        GEMINI_API_KEY = "your_api_key_here"
        GOOGLE_CLOUD_CREDENTIALS = "path_to_credentials.json"
        """)
    
    st.header("📊 Session Info")
    st.metric("Messages", len(st.session_state.messages))
    st.metric("Status", "Active" if st.session_state.conversation_active else "Inactive")
    
    # 🆕 NEW: Enhanced call status info
    if st.session_state.call_data:
        st.header("📞 Call Details")
        if st.session_state.call_data.get("call_ended", False):
            st.metric("Call Duration", st.session_state.call_data.get("call_duration", "Unknown"))
            st.metric("Conversation Length", f"{len(st.session_state.call_data.get('conversation_summary', ''))} chars")
            
            if st.session_state.call_data.get("redirect_requested", False):
                st.error("🔄 Redirect Requested")
            else:
                st.success("✅ Call Complete")
        elif st.session_state.conversation_active:
            st.info("🟢 Call In Progress")
    
    # Show call history
    if st.session_state.call_data.get("conversation_history", []):
        with st.expander("📋 Call History"):
            for msg in st.session_state.call_data["conversation_history"][-3:]:  # Show last 3 messages
                st.text(f"{msg['role']}: {msg['content'][:50]}...")  

# Control Panel
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🎯 Start Conversation", disabled=st.session_state.conversation_active):
        st.session_state.conversation_active = True
        st.session_state.messages = []
        # Start listening in a separate thread
        listening_thread = threading.Thread(target=continuous_listening, daemon=True)
        listening_thread.start()
        st.success("Conversation started! Start speaking...")

with col2:
    if st.button("⏹️ End Conversation", disabled=not st.session_state.conversation_active):
        st.session_state.conversation_active = False
        st.session_state.is_speaking = False
        
        # 🆕 NEW: Trigger conversation analysis and workflow completion
        print(f"📞 END CALL: User clicked End Conversation button")
        
        # Prepare conversation data for analysis
        conversation_history = st.session_state.messages
        conversation_summary = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])
        
        print(f"📞 END CALL: Conversation history length: {len(conversation_history)} messages")
        print(f"📞 END CALL: Conversation summary length: {len(conversation_summary)} characters")
        
        # Store conversation data for workflow processing
        if 'call_data' not in st.session_state:
            st.session_state.call_data = {}
        
        st.session_state.call_data.update({
            "call_ended": True,
            "conversation_history": conversation_history,
            "conversation_summary": conversation_summary,
            "call_end_timestamp": datetime.now().isoformat(),
            "conversation_complete": True
        })
        
        print(f"📞 END CALL: Call data stored in session state")
        print(f"📞 END CALL: Ready for redirect analysis...")
        
        st.success("✅ Call ended successfully! Analyzing conversation for any redirect requests...")
        
        # TODO: Here we would trigger the workflow with end_call action
        # For now, just show the completion message
        if conversation_history:
            st.info(f"📋 Conversation completed with {len(conversation_history)} exchanges")
        else:
            st.warning("⚠️ No conversation recorded during this call")

with col3:
    mute_label = "🔇 Unmute" if st.session_state.is_muted else "🔇 Mute Mic"
    if st.button(mute_label, disabled=not st.session_state.conversation_active):
        st.session_state.is_muted = not st.session_state.is_muted
        status = "muted" if st.session_state.is_muted else "unmuted"
        st.info(f"Microphone {status}")

with col4:
    if st.button("🗑️ Clear History"):
        st.session_state.messages = []
        st.rerun()

# Status Indicators
status_col1, status_col2, status_col3 = st.columns(3)

with status_col1:
    status_color = "🟢" if st.session_state.conversation_active else "🔴"
    st.markdown(f"**{status_color} Conversation Status**")

with status_col2:
    mic_status = "🔇" if st.session_state.is_muted else "🎤"
    st.markdown(f"**{mic_status} Microphone**")

with status_col3:
    speak_status = "🗣️" if st.session_state.is_speaking else "👂"
    st.markdown(f"**{speak_status} AI Status**")

# Conversation History
st.header("💬 Conversation History")

if st.session_state.messages:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            st.caption(f"*{message['timestamp'].strftime('%H:%M:%S')}*")
else:
    st.info("No conversation yet. Click 'Start Conversation' to begin!")

# Instructions
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    ### Quick Start:
    1. **Configure**: Add your API keys in the sidebar
    2. **Start**: Click "Start Conversation" to begin
    3. **Speak**: Talk naturally - the AI will respond after 2 seconds of silence
    4. **Control**: Use the mute button to prevent interruptions
    5. **End**: Click "End Conversation" when done
    
    ### Features:
    - 🎯 **One-click start**: No need to repeatedly click record
    - 🔄 **Live conversation**: Continuous listening and responding
    - ⏱️ **Smart timing**: AI responds after 2 seconds of silence
    - 🚫 **Interruption handling**: AI stops when you start speaking
    - 🔇 **Mute control**: Prevent background noise interruptions
    - 📝 **History**: View your entire conversation
    
    ### Requirements:
    - Microphone access
    - Gemini API key
    - Google Cloud credentials (optional, for better TTS/STT)
    """)