"""
VoiceService for STT, TTS, and interactive voice chat logic for optimized_project.
Consolidates functionality from front/vocal_components.py and src/agents/vocal_assistant.py's embedded classes.
"""

import os
import io
import base64
import tempfile
from typing import Dict, Any, List, Tuple, Optional, Callable

import requests # For Google Cloud REST APIs if used
import speech_recognition as sr # For fallback STT or primary if configured
from langfuse import observe # Assuming Langfuse is kept

# TTS specific imports
try:
    from gtts import gTTS # Google Text-to-Speech (local fallback)
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# LLM for chat during calls - assuming Gemini via ChatGoogleGenerativeAI
from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_openai import ChatOpenAI # Example

# Configuration for this service will be passed in __init__

class VoiceService:
    """
    Provides Speech-to-Text (STT), Text-to-Speech (TTS), and interactive LLM chat capabilities.
    """

    def __init__(self, voice_service_config: Dict[str, Any], llm_config: Dict[str, Any]):
        """
        Initializes the VoiceService.
        Args:
            voice_service_config: Configuration for STT/TTS providers, API keys, etc.
                                  Example: {
                                      "tts_provider": "google_cloud",
                                      "stt_provider": "google_cloud",
                                      "google_cloud_tts_config": {...},
                                      "google_cloud_stt_config": {...},
                                      "gtts_lang": "en",
                                      "sr_pause_threshold": 0.8,
                                      "google_cloud_api_key": "AIza..." (or fetched from env)
                                  }
            llm_config: Configuration for the LLM used in interactive chat.
                        Example: {
                            "provider": "google_gemini",
                            "model_name": "gemini-pro",
                            "temperature": 0.7,
                            "api_key_env_var": "GEMINI_API_KEY"
                        }
        """
        self.config = voice_service_config
        self.llm_config = llm_config

        # Initialize STT Recognizer (used by speech_recognition library)
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = float(self.config.get("sr_pause_threshold", 0.8))
        self.recognizer.energy_threshold = int(self.config.get("sr_energy_threshold", 300))
        self.recognizer.dynamic_energy_threshold = bool(self.config.get("sr_dynamic_energy_threshold", True))

        # Initialize LLM for chat
        self.chat_llm = self._initialize_llm()

        # Google Cloud specific (if used) - API keys are typically managed by env vars
        # like GOOGLE_APPLICATION_CREDENTIALS or specific service API keys.
        self.google_cloud_api_key = self.config.get("google_cloud_api_key") # Could come from core_config
        self.google_tts_url = "https://texttospeech.googleapis.com/v1/text:synthesize"
        self.google_stt_url = "https://speech.googleapis.com/v1/speech:recognize" # Basic STT endpoint

    def _initialize_llm(self) -> Optional[Any]:
        """Initializes the LLM for interactive chat based on llm_config."""
        provider = self.llm_config.get("provider", "google_gemini")
        model_name = self.llm_config.get("model_name")
        temperature = self.llm_config.get("temperature", 0.7)
        api_key_env_var = self.llm_config.get("api_key_env_var")

        api_key = os.getenv(api_key_env_var) if api_key_env_var else None
        if api_key_env_var and not api_key:
            print(f"VoiceService: Warning - Env var {api_key_env_var} for chat LLM not set.")

        if not model_name:
            print("VoiceService: Warning - No model_name for chat LLM. Chat LLM not initialized.")
            return None
        try:
            if provider == "google_gemini":
                return ChatGoogleGenerativeAI(model=model_name, temperature=float(temperature), google_api_key=api_key)
            # Add other providers like OpenAI if needed
            # elif provider == "openai":
            #     return ChatOpenAI(model_name=model_name, temperature=float(temperature), openai_api_key=api_key)
            else:
                print(f"VoiceService: Unsupported LLM provider '{provider}' for chat.")
                return None
        except Exception as e:
            print(f"VoiceService: Error initializing chat LLM ({provider}): {e}")
            return None

    @observe()
    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """
        Transcribes audio bytes to text.
        Uses configured STT provider (e.g., Google Cloud STT, or SpeechRecognition library).
        Args:
            audio_bytes: The audio data in bytes.
            mime_type: The MIME type of the audio, important for some APIs like Google Cloud STT.
                       speech_recognition library often infers or works with WAV.
        Returns:
            The transcribed text, or an error message.
        """
        provider = self.config.get("stt_provider", "speech_recognition_fallback")
        # print(f"VoiceService: Transcribing with {provider}")

        if provider == "google_cloud_rest" and self.google_cloud_api_key:
            try:
                cfg = self.config.get("google_cloud_stt_config", {})
                api_url = f"{self.google_stt_url}?key={self.google_cloud_api_key}"

                # Encoding and sample rate must match the audio bytes
                # Common frontend encodings might be 'audio/webm;codecs=opus' or 'audio/ogg;codecs=opus'
                # These might need conversion to LINEAR16 for some Google STT options or use specific encoding settings.
                # For simplicity, this example assumes the mime_type and bytes are compatible with a simple config.

                recognition_config = {
                    "encoding": cfg.get("encoding", "LINEAR16"), # WAV is often LINEAR16
                    "sampleRateHertz": int(cfg.get("sample_rate_hertz", 16000)), # Common for voice
                    "languageCode": cfg.get("language_code", "en-US"),
                    "enableAutomaticPunctuation": True,
                }
                # If mime_type suggests opus or other, adjust encoding or use a more complex STT setup.
                if "opus" in mime_type.lower(): # A common case from web recorders
                    recognition_config["encoding"] = "WEBM_OPUS" # Requires sampleRateHertz to be 8000, 12000, 16000, 24000, or 48000

                payload = {
                    "config": recognition_config,
                    "audio": {"content": base64.b64encode(audio_bytes).decode('utf-8')}
                }
                response = requests.post(api_url, json=payload, timeout=20)
                response.raise_for_status()
                data = response.json()
                if data.get("results"):
                    return data["results"][0]["alternatives"][0]["transcript"]
                return "No transcription result from Google Cloud STT."
            except Exception as e:
                print(f"VoiceService: Google Cloud STT (REST) error: {e}")
                # Fallback to speech_recognition if Google Cloud fails and it's not already the fallback
                if provider != "speech_recognition_fallback":
                    return self._transcribe_with_speech_recognition(audio_bytes)
                return f"STT Error: {e}"

        # Default or fallback to SpeechRecognition library (uses Google Web Speech API by default)
        return self._transcribe_with_speech_recognition(audio_bytes)

    def _transcribe_with_speech_recognition(self, audio_bytes: bytes) -> str:
        """Helper for SpeechRecognition library based STT."""
        tmp_file_path = None
        try:
            # speech_recognition works best with WAV files.
            # If audio_bytes is not WAV, conversion might be needed or use a different recognizer method.
            # For now, assume it's compatible or can be handled by recognize_google.
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_file_path = tmp_file.name

            with sr.AudioFile(tmp_file_path) as source:
                # self.recognizer.adjust_for_ambient_noise(source, duration=0.2) # Can be slow
                audio_data = self.recognizer.record(source)

            # Uses Google Web Speech API by default (free, but rate limits apply)
            text = self.recognizer.recognize_google(audio_data, language=self.config.get("sr_language", "en-US"))
            return text
        except sr.UnknownValueError:
            return "Could not understand audio."
        except sr.RequestError as e:
            return f"Speech recognition service error: {e}"
        except Exception as e:
            return f"Error processing audio for STT: {e}"
        finally:
            if tmp_file_path and os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)

    @observe()
    def synthesize_speech(self, text_to_speak: str) -> Optional[bytes]:
        """
        Converts text to speech audio bytes.
        Uses configured TTS provider (e.g., Google Cloud TTS, or gTTS fallback).
        """
        provider = self.config.get("tts_provider", "gtts_fallback")
        # print(f"VoiceService: Synthesizing with {provider}")

        if provider == "google_cloud_rest" and self.google_cloud_api_key:
            try:
                cfg = self.config.get("google_cloud_tts_config", {})
                api_url = f"{self.google_tts_url}?key={self.google_cloud_api_key}"
                payload = {
                    "input": {"text": text_to_speak[:4999]}, # Google TTS limit 5000 bytes for text input
                    "voice": {
                        "languageCode": cfg.get("language_code", "en-US"),
                        "name": cfg.get("name", "en-US-Studio-O"), # Example high-quality voice
                        # "ssmlGender": cfg.get("ssml_gender", "FEMALE") # name implies gender
                    },
                    "audioConfig": {"audioEncoding": cfg.get("audio_encoding", "MP3")}
                }
                if "sample_rate_hertz" in cfg: # Optional for some audio encodings
                    payload["audioConfig"]["sampleRateHertz"] = int(cfg["sample_rate_hertz"])

                response = requests.post(api_url, json=payload, timeout=20)
                response.raise_for_status()
                audio_content_b64 = response.json().get('audioContent')
                if audio_content_b64:
                    return base64.b64decode(audio_content_b64)
                return None # Should not happen if status is 200
            except Exception as e:
                print(f"VoiceService: Google Cloud TTS (REST) error: {e}")
                if provider != "gtts_fallback": # Avoid infinite loop if gtts is the primary and fails
                    return self._synthesize_with_gtts(text_to_speak)
                return None

        # Default or fallback: gTTS
        return self._synthesize_with_gtts(text_to_speak)

    def _synthesize_with_gtts(self, text_to_speak: str) -> Optional[bytes]:
        """Helper for gTTS based synthesis."""
        if not GTTS_AVAILABLE:
            print("VoiceService: gTTS library not available for fallback TTS.")
            return None
        try:
            tts = gTTS(text=text_to_speak, lang=self.config.get("gtts_lang", "en"))
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as e:
            print(f"VoiceService: gTTS synthesis error: {e}")
            return None

    @observe()
    def get_chat_response(self, user_message: str, conversation_history: List[Dict[str, str]],
                          system_prompt_template: str,
                          ticket_data: Dict[str, Any], employee_data: Dict[str, Any]) -> str:
        """
        Gets a response from the configured chat LLM for interactive voice calls.
        Args:
            user_message: The latest message from the user (transcribed audio).
            conversation_history: List of previous messages [{"role": "user/assistant", "content": "..."}].
            system_prompt_template: A template string for the system prompt.
                                    It can contain placeholders like {employee_name}, {ticket_subject}.
            ticket_data: Contextual data about the ticket.
            employee_data: Contextual data about the employee on call.
        Returns:
            The LLM's text response.
        """
        if not self.chat_llm:
            return "I'm sorry, my chat capabilities are currently offline."

        # Format system prompt with context
        try:
            system_prompt = system_prompt_template.format(
                employee_name=employee_data.get("full_name", "Support Expert"),
                ticket_subject=ticket_data.get("subject", "the current issue"),
                user_name=ticket_data.get("user", "the user"), # User who created ticket
                # Add more placeholders as needed by the template
            )
        except KeyError as e:
            print(f"VoiceService: Missing key {e} for system_prompt_template. Using basic prompt.")
            system_prompt = "You are a helpful voice assistant."

        # Construct messages for Langchain LLM
        # Langchain expects a list of BaseMessage objects or specific dicts for some models.
        # For ChatGoogleGenerativeAI, it's usually a list of HumanMessage, AIMessage, SystemMessage.
        # A simple approach is list of dicts: {"role": "user/model", "parts": [{"text": content}]}

        messages_for_llm = [{"role": "system", "content": system_prompt}] if system_prompt else []

        # Add history (Langchain ChatGoogleGenerativeAI expects "user" and "model" roles)
        for msg in conversation_history:
            role = "user" if msg.get("role", "").lower() == "user" else "model"
            messages_for_llm.append({"role": role, "content": msg.get("content","")})

        messages_for_llm.append({"role": "user", "content": user_message})

        try:
            # print(f"VoiceService: Sending to chat LLM: {messages_for_llm}")
            ai_response_obj = self.chat_llm.invoke(messages_for_llm)
            # .content is typical for Langchain LLM responses
            return ai_response_obj.content if hasattr(ai_response_obj, 'content') else str(ai_response_obj)
        except Exception as e:
            print(f"VoiceService: Chat LLM invocation error: {e}")
            return "I encountered an issue trying to process that. Could you try again?"


    @observe()
    def process_interactive_turn(self, audio_bytes: bytes, mime_type: str,
                                 conversation_history: List[Dict[str, str]],
                                 chat_system_prompt_template: str,
                                 ticket_data: Dict[str, Any], employee_data: Dict[str, Any]
                                 ) -> Tuple[Optional[str], Optional[str], Optional[bytes]]:
        """
        Processes one turn of an interactive voice conversation: STT -> LLM Chat -> TTS.
        Args:
            audio_bytes: User's spoken audio.
            mime_type: Mime type of the audio bytes.
            conversation_history: Current history of the conversation.
            chat_system_prompt_template: System prompt template for the LLM.
            ticket_data: Contextual ticket data.
            employee_data: Contextual employee data.
        Returns:
            Tuple of (transcribed_text, llm_response_text, tts_audio_bytes_for_llm_response)
            Any can be None if a step fails.
        """
        transcribed_text = self.transcribe_audio(audio_bytes, mime_type=mime_type)
        if not transcribed_text or "Could not understand" in transcribed_text or "error" in transcribed_text.lower():
            # print(f"VoiceService: Transcription failed or not understood: {transcribed_text}")
            return transcribed_text, None, None # Return transcription error, no LLM/TTS

        llm_response_text = self.get_chat_response(
            user_message=transcribed_text,
            conversation_history=conversation_history,
            system_prompt_template=chat_system_prompt_template,
            ticket_data=ticket_data,
            employee_data=employee_data
        )
        if not llm_response_text:
            # print("VoiceService: LLM produced no response.")
            return transcribed_text, "I'm sorry, I didn't get a response from my brain.", None # Error from LLM

        tts_audio_bytes = self.synthesize_speech(llm_response_text)
        if not tts_audio_bytes:
            # print("VoiceService: TTS failed for LLM response.")
            # Return text response even if TTS fails
            return transcribed_text, llm_response_text, None

        return transcribed_text, llm_response_text, tts_audio_bytes

# Example Usage (for testing or if this module is run directly):
if __name__ == '__main__':
    # This setup is for standalone testing of this module.
    # In the actual app, configurations would come from CoreConfigLoader.
    print("Running VoiceService example...")

    # Mock configurations (replace with actual loading if testing seriously)
    # IMPORTANT: Set GEMINI_API_KEY and potentially GOOGLE_CLOUD_API_KEY in your environment!
    if not os.getenv("GEMINI_API_KEY"):
        print("FATAL: GEMINI_API_KEY environment variable not set. This example will likely fail.")
        exit()

    mock_voice_config = {
        "tts_provider": "gtts_fallback", # "google_cloud_rest" or "gtts_fallback"
        "stt_provider": "speech_recognition_fallback", # "google_cloud_rest" or "speech_recognition_fallback"
        "gtts_lang": "en-au",
        "sr_pause_threshold": 0.8,
        # "google_cloud_api_key": os.getenv("GOOGLE_CLOUD_API_KEY"), # For Google Cloud REST
        "google_cloud_tts_config": {"languageCode": "en-US", "name": "en-US-News-N"},
        "google_cloud_stt_config": {"languageCode": "en-US", "encoding": "LINEAR16", "sampleRateHertz": 16000}
    }
    mock_llm_config = {
        "provider": "google_gemini",
        "model_name": "gemini-pro", # Make sure this model is available with your key
        "temperature": 0.7,
        "api_key_env_var": "GEMINI_API_KEY"
    }

    voice_service = VoiceService(voice_service_config=mock_voice_config, llm_config=mock_llm_config)

    # 1. Test TTS
    print("\n--- Testing TTS ---")
    tts_text = "Hello from the Voice Service! This is a test of text to speech."
    audio_out_bytes = voice_service.synthesize_speech(tts_text)
    if audio_out_bytes:
        print(f"TTS generated {len(audio_out_bytes)} bytes of audio.")
        # In a real test, you'd save and play this, or verify its content.
        # with open("test_tts_output.mp3", "wb") as f:
        #     f.write(audio_out_bytes)
        # print("Saved TTS output to test_tts_output.mp3")
    else:
        print("TTS failed to generate audio.")

    # 2. Test STT (requires a sample audio file or live input)
    # For this example, we'll skip live STT. If you have a sample WAV:
    # print("\n--- Testing STT ---")
    # try:
    #     with open("path_to_your_sample.wav", "rb") as audio_file:
    #         sample_audio_bytes = audio_file.read()
    #     stt_text = voice_service.transcribe_audio(sample_audio_bytes, mime_type="audio/wav")
    #     print(f"STT transcribed: '{stt_text}'")
    # except FileNotFoundError:
    #     print("STT test skipped: sample audio file not found.")
    # except Exception as e:
    #     print(f"STT test error: {e}")


    # 3. Test LLM Chat
    print("\n--- Testing LLM Chat ---")
    if voice_service.chat_llm:
        history = [{"role": "user", "content": "What's the weather like?"}]
        user_msg = "And in Paris?"
        system_template = "You are a helpful assistant named Chatter. Employee is {employee_name}."
        mock_ticket = {"subject": "Weather query", "user": "TestUser"}
        mock_employee = {"full_name": "SupportSally"}

        chat_response = voice_service.get_chat_response(user_msg, history, system_template, mock_ticket, mock_employee)
        print(f"LLM Chat response for '{user_msg}': {chat_response}")
    else:
        print("Chat LLM not initialized, skipping chat test.")

    # 4. Test Interactive Turn (would require actual audio bytes for full test)
    print("\n--- Testing Interactive Turn (conceptual) ---")
    # This needs real audio_bytes to work.
    # dummy_audio_bytes = b"..." # Replace with actual audio
    # if dummy_audio_bytes != b"...":
    #     transcribed, llm_text, tts_audio = voice_service.process_interactive_turn(
    #         dummy_audio_bytes, "audio/wav", history, system_template, mock_ticket, mock_employee
    #     )
    #     print(f"Interactive Turn: Transcribed='{transcribed}', LLM='{llm_text}', TTS Audio Bytes='{len(tts_audio) if tts_audio else 0}'")
    # else:
    # print("Interactive turn test skipped: no dummy audio bytes provided.")

    print("\nVoiceService example finished.")
