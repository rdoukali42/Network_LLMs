"""
Voice call interface for the Optimized Streamlit app.
Handles display of active call, voice input/output, and solution generation post-call.
"""

import streamlit as st
import time
import hashlib # For audio hash to prevent quick duplicate processing
from typing import Any, Optional, Dict, List

# Assuming this file is in optimized_project/app/
OPTIMIZED_PROJECT_ROOT_CALL_UI = Path(__file__).resolve().parent.parent
if str(OPTIMIZED_PROJECT_ROOT_CALL_UI) not in st.session_state.get("sys_path_optimized_project", []):
    import sys
    sys.path.insert(0, str(OPTIMIZED_PROJECT_ROOT_CALL_UI))

from config import app_config
# VoiceService client will be instantiated and passed or managed via session state.
# from core.services.voice_service import VoiceService
# TicketManager will be passed or managed via session state.
# from data_management.ticket_store import TicketManager
# AppWorkflowClient for Maestro review will be passed or managed via session state.
# from .workflow_client import AppWorkflowClient


# Helper function to ensure voice service client is available
def _get_voice_service_client() -> Optional[Any]:
    if app_config.SESSION_KEYS["voice_service_client"] not in st.session_state:
        # This implies VoiceService client should be initialized elsewhere and put in session state,
        # e.g., when AISystem starts or when a call is accepted.
        # For this refactor, let's assume it's initialized in tickets_ui.py or main_app.py
        # and stored in st.session_state[app_config.SESSION_KEYS["voice_service_client"]]
        # If not, this UI component cannot function.
        # As a fallback for now, if not in session, try to init (bad for prod, ok for refactor step)
        try:
            from core.services import VoiceService
            from config.core_config import CoreConfigLoader # For VoiceService config

            cfg_loader = CoreConfigLoader(base_project_root=OPTIMIZED_PROJECT_ROOT_CALL_UI)
            core_cfg = cfg_loader.load_config_yaml()
            voice_cfg = core_cfg.get("voice_service", {})
            llm_cfg_for_voice = core_cfg.get("models", {}).get(voice_cfg.get("chat_llm_model_key", "voice_service_llm_model"), {})
            llm_cfg_for_voice.setdefault("api_key_env_var", core_cfg.get("api_keys",{}).get("default_llm_api_key_env_var", "GEMINI_API_KEY"))


            st.session_state[app_config.SESSION_KEYS["voice_service_client"]] = VoiceService(
                voice_service_config=voice_cfg,
                llm_config=llm_cfg_for_voice
            )
            # print("call_ui.py: VoiceService client initialized and stored in session state.")
        except Exception as e:
            print(f"call_ui.py: Failed to auto-initialize VoiceService client: {e}")
            st.session_state[app_config.SESSION_KEYS["voice_service_client"]] = None

    return st.session_state[app_config.SESSION_KEYS["voice_service_client"]]

def _get_ticket_manager_instance() -> Optional[Any]:
    # Similar to VoiceService, TicketManager should be initialized elsewhere (e.g., tickets_ui)
    # and stored in session state.
    if app_config.SESSION_KEYS["ticket_manager"] not in st.session_state:
        try:
            from data_management.ticket_store import TicketManager
            st.session_state[app_config.SESSION_KEYS["ticket_manager"]] = TicketManager(project_root_path=OPTIMIZED_PROJECT_ROOT_CALL_UI)
        except Exception as e:
            print(f"call_ui.py: Failed to auto-initialize TicketManager: {e}")
            st.session_state[app_config.SESSION_KEYS["ticket_manager"]] = None
    return st.session_state[app_config.SESSION_KEYS["ticket_manager"]]

def _get_workflow_client_instance() -> Optional[Any]:
    if app_config.SESSION_KEYS["workflow_client"] not in st.session_state:
        try:
            from .workflow_client import AppWorkflowClient # Relative import
            st.session_state[app_config.SESSION_KEYS["workflow_client"]] = AppWorkflowClient()
        except Exception as e:
            print(f"call_ui.py: Failed to auto-initialize AppWorkflowClient: {e}")
            st.session_state[app_config.SESSION_KEYS["workflow_client"]] = None
    return st.session_state[app_config.SESSION_KEYS["workflow_client"]]


def show_active_call_interface():
    """Displays the UI for an active voice call."""

    call_info_key = app_config.SESSION_KEYS["call_info"]
    convo_history_key = app_config.SESSION_KEYS["conversation_history"]
    call_active_key = app_config.SESSION_KEYS["call_active"]

    call_info_data = st.session_state.get(call_info_key)
    if not call_info_data:
        st.error("Call information is missing. Cannot display call interface.")
        return

    voice_service = _get_voice_service_client()
    if not voice_service:
        st.error("Voice service is not available. Call interface cannot function.")
        return

    # Extract necessary data from call_info_data (which was prepared by VocalAssistantAgent or availability_ui)
    # This data was originally in call_info['call_info'] from the DB notification.
    # The structure of call_info_data should be:
    # { "ticket_id": ..., "employee_name": ..., "ticket_subject": ...,
    #   "ticket_data_snapshot": {...}, "employee_data_snapshot": {...} }
    employee_name = call_info_data.get('employee_name', 'Support Expert')
    ticket_subject = call_info_data.get('ticket_subject', 'N/A')
    ticket_id = call_info_data.get('ticket_id', 'N/A')

    # These snapshots are crucial for the VoiceService context
    ticket_context_data = call_info_data.get('ticket_data_snapshot', {})
    employee_context_data = call_info_data.get('employee_data_snapshot', {})


    st.markdown(f"""
    <div style='background:linear-gradient(90deg, #28a745, #20c997); color:white; padding:20px; border-radius:10px; text-align:center; margin-bottom:20px;'>
        <h2>📞 Active Call</h2>
        <p><strong>With:</strong> {employee_name}</p>
        <p><strong>Regarding Ticket:</strong> {ticket_subject} (ID: {ticket_id})</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🎤 Voice Conversation")
    st.markdown(f"Speak into the microphone to discuss the ticket with {employee_name}.")

    # Audio recorder (assuming audio_recorder_streamlit is in requirements.txt)
    try:
        from audio_recorder_streamlit import audio_recorder
        # Audio settings (could be moved to app_config if needed)
        pause_thresh = st.session_state.get("call_ui_pause_threshold", 2.0) # seconds
        sample_rate_hz = st.session_state.get("call_ui_sample_rate", 16000) # Hz

        # UI for audio settings (optional, can be simplified)
        with st.expander("🎤 Audio Settings", expanded=False):
            pause_thresh = st.slider("Recording Sensitivity (silence duration to stop)", 0.5, 5.0, pause_thresh, 0.5, key="call_pause_thresh")
            st.session_state.call_ui_pause_threshold = pause_thresh
            # Sample rate might be fixed by STT provider needs.
            # sample_rate_hz = st.selectbox("Audio Quality (Sample Rate)", [16000, 22050, 44100, 48000],
            #                                index=[16000, 22050, 44100, 48000].index(sample_rate_hz), key="call_sample_rate")
            # st.session_state.call_ui_sample_rate = sample_rate_hz


        audio_bytes = audio_recorder(
            text="Click to Record / Speak", recording_color="#e84343", neutral_color="#6aa36f",
            icon_name="microphone", icon_size="2x", pause_threshold=pause_thresh, sample_rate=sample_rate_hz,
            key="call_audio_input_recorder"
        )

        if audio_bytes:
            current_time = time.time()
            last_audio_time = st.session_state.get("call_last_audio_proc_time", 0)
            audio_hash_val = hashlib.md5(audio_bytes).hexdigest()[:10]
            last_audio_hash_val = st.session_state.get("call_last_audio_hash", "")

            # Basic debounce/deduplication
            if (current_time - last_audio_time > 1.0) or (audio_hash_val != last_audio_hash_val) :
                st.session_state.call_last_audio_proc_time = current_time
                st.session_state.call_last_audio_hash = audio_hash_val

                if not st.session_state.get(call_active_key, False):
                    st.info("Call has ended. Audio not processed.")
                    return

                with st.spinner("Processing your voice..."):
                    # Use VoiceService for the STT -> LLM -> TTS turn
                    # The chat system prompt needs to be defined.
                    chat_prompt_template = """You are {employee_name}, a helpful support expert from our company.
You are on a call with {user_name} regarding ticket: '{ticket_subject}'.
Be conversational and try to resolve their issue based on the information they provide.
Your expertise includes: {employee_expertise} (This is a placeholder, actual expertise should be in employee_context_data)
Current conversation:""" # VoiceService will append history and user message

                    # Extract expertise for prompt, or use a generic term
                    employee_expertise_str = employee_context_data.get("expertise", "various company systems and policies")


                    transcribed, llm_text, tts_audio = voice_service.process_interactive_turn(
                        audio_bytes=audio_bytes,
                        mime_type=f"audio/wav", # audio_recorder_streamlit provides WAV
                        conversation_history=st.session_state.get(convo_history_key, []),
                        chat_system_prompt_template=chat_prompt_template.format(
                            employee_name=employee_name, # This is AI playing the employee
                            user_name=ticket_context_data.get("user", "the user"), # User who submitted ticket
                            ticket_subject=ticket_subject,
                            employee_expertise=employee_expertise_str
                        ),
                        ticket_data=ticket_context_data,
                        employee_data=employee_context_data # This is the "expert" AI is playing
                    )

                    if transcribed and "Could not understand" not in transcribed and "error" not in transcribed.lower():
                        st.success(f"**You said:** {transcribed}")
                        st.session_state.setdefault(convo_history_key, []).append({"role": "user", "content": transcribed})
                        if llm_text:
                            st.info(f"**{employee_name} (AI):** {llm_text}")
                            st.session_state[convo_history_key].append({"role": "assistant", "content": llm_text})
                            if tts_audio:
                                st.audio(tts_audio, format="audio/mp3", autoplay=True)
                            else:
                                st.warning("Could not generate audio response for the assistant.")
                        else:
                             st.warning(f"{employee_name} (AI) had trouble responding. Please try again.")
                    elif transcribed:
                        st.error(f"**Transcription:** {transcribed}")
                    else:
                        st.error("Failed to transcribe audio.")
            # else: # Debounced
            #     st.caption("Recording too quick or same audio detected.")

    except ImportError:
        st.error("Audio recording component (audio-recorder-streamlit) not found. Please install it.")
        st.code("pip install audio-recorder-streamlit")
    except Exception as e:
        st.error(f"An error occurred with the audio recorder or voice processing: {e}")
        import traceback
        traceback.print_exc()


    # Conversation History Display
    if st.session_state.get(convo_history_key):
        st.markdown("--- \n### 💬 Conversation Log")
        with st.container(height=300): # Scrollable container
            for msg in st.session_state[convo_history_key]:
                icon = "🙂" if msg["role"] == "user" else "🤖"
                st.markdown(f"**{icon} {msg['role'].capitalize()}:** {msg['content']}")
        st.markdown("---")


    # Call Controls
    end_col, hold_col = st.columns(2)
    with end_col:
        if st.button("📴 End Call", type="primary", use_container_width=True, key="call_end_btn"):
            st.session_state[call_active_key] = False # Immediately stop processing further audio
            if st.session_state.get(convo_history_key):
                _generate_and_save_solution_from_call(
                    call_info_data=call_info_data,
                    conversation_history=st.session_state[convo_history_key]
                )
            else:
                st.info("Call ended. No conversation to process.")

            # Clean up call-specific session state
            _clear_call_session_state()
            st.rerun() # Go back to main ticket interface

    with hold_col: # "Hold Call" is more like "Pause and Return to Ticket View"
        if st.button("⏸️ Pause & View Tickets", use_container_width=True, key="call_hold_btn"):
            # Call remains "active" in backend DB if needed, but UI goes back.
            # For this simplified version, "Hold" will be similar to End, but without solution processing.
            # Or, it just sets call_active to False for UI, but keeps call_info to be resumed.
            # For now, let's make it a soft end from UI perspective.
            st.session_state[call_active_key] = False
            st.info("Call paused. You can resume from the sidebar if implementation allows, or it will be considered ended.")
            # To truly support "Hold & Resume", availability_ui would need to show a "Resume Call" button
            # if call_info is still present but call_active is false.
            # For now, this will just effectively end the UI part of the call.
            st.rerun()


def _clear_call_session_state():
    """Clears session state variables related to an active call."""
    keys_to_del = [
        app_config.SESSION_KEYS["call_info"],
        app_config.SESSION_KEYS["conversation_history"],
        app_config.SESSION_KEYS["vocal_chat"], # Old key, ensure cleared
        "call_last_audio_proc_time",
        "call_last_audio_hash"
    ]
    # call_active is set to False, not deleted, to signify no call is active.
    st.session_state[app_config.SESSION_KEYS["call_active"]] = False
    for key in keys_to_del:
        if key in st.session_state:
            del st.session_state[key]

def _generate_and_save_solution_from_call(call_info_data: Dict[str, Any], conversation_history: List[Dict[str,str]]):
    """Generates solution from call history and saves it to the ticket."""
    ticket_manager = _get_ticket_manager_instance()
    workflow_client = _get_workflow_client_instance()

    if not ticket_manager or not workflow_client or not workflow_client.is_ai_system_ready():
        st.error("Cannot generate solution: TicketManager or AI System (for Maestro review) is not available.")
        return

    ticket_id = call_info_data.get("ticket_id")
    # These snapshots were stored in call_info_data by availability_ui when call was accepted
    ticket_context_data = call_info_data.get("ticket_data_snapshot", {})
    employee_context_data = call_info_data.get("employee_data_snapshot", {}) # This is the "expert" AI was playing

    if not ticket_id:
        st.error("Ticket ID missing, cannot save solution.")
        return

    conversation_summary_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history])

    with st.spinner("Generating solution from call and getting Maestro review..."):
        # Step 1: Create a simple initial solution text (can be improved by an LLM call too)
        # This is the employee's (AI playing employee) solution from the call.
        ai_responses = [msg['content'] for msg in conversation_history if msg['role'] == 'assistant' and msg['content'].strip()]
        if ai_responses:
            employee_solution_text = ai_responses[-1] # Last AI response as the solution
        else:
            employee_solution_text = "No specific solution articulated by the assistant during the call. Conversation summary: " + conversation_summary_text[:200] + "..."

        initial_solution_formatted = f"""
Solution based on voice call with {employee_context_data.get('full_name', 'Support Expert')}:

**Expert's Key Points / Recommendation:**
{employee_solution_text}

**Call Context:**
- Ticket: {ticket_context_data.get('subject', 'N/A')} (ID: {ticket_id})
- User: {ticket_context_data.get('user', 'N/A')}
- Call Summary (brief): {conversation_summary_text[:300]}...
"""
        # Step 2: Send to Maestro for review (as in original HRAgent)
        # The AISystem needs to expose its agents or have a specific method for this.
        # Assuming workflow_client.system.agents is accessible as in original.
        maestro_agent = workflow_client.system.agents.get("maestro")
        final_solution_to_save = initial_solution_formatted # Fallback

        if maestro_agent:
            maestro_review_prompt = f"""Review and refine the following voice call solution into a customer-facing email.
Original Ticket User: {ticket_context_data.get('user', 'Valued Customer')}
Ticket Subject: {ticket_context_data.get('subject', 'Your Recent Support Request')}
Employee on Call (AI): {employee_context_data.get('full_name', 'Support Expert')} ({employee_context_data.get('role_in_company', 'Specialist')})
Conversation Summary:
{conversation_summary_text}

Proposed Solution from Call:
{initial_solution_formatted}

Task: Create a concise, professional email response for the customer:
- Start with "Subject: Re: {ticket_context_data.get('subject', 'Your Support Ticket')}"
- Friendly greeting to {ticket_context_data.get('user', 'Valued Customer')}.
- Clearly state the solution or outcome based on the call.
- If applicable, add one brief practical tip.
- Credit the AI expert: "This was discussed with {employee_context_data.get('full_name', 'our support specialist')}."
- End with "Best regards, Support Team".
- Keep it short, clear, and in paragraph form.
"""
            try:
                maestro_result = maestro_agent.run({
                    "query": maestro_review_prompt, # The full prompt is the "query" here
                    "stage": "final_review"
                    # data_guardian_result not directly relevant here, prompt has all context
                })
                reviewed_solution = maestro_result.get("result")
                if reviewed_solution and reviewed_solution.strip():
                    final_solution_to_save = reviewed_solution
                    st.success("Solution reviewed and refined by Maestro AI.")
                else:
                    st.warning("Maestro review did not return a refined solution, using initial version.")
            except Exception as e:
                st.warning(f"Error during Maestro review: {e}. Using initial solution.")
        else:
            st.warning("Maestro agent not available for solution review. Using initial solution.")

        # Step 3: Update ticket
        if ticket_manager.update_employee_solution(ticket_id, final_solution_to_save):
            st.success(f"Solution saved for ticket {ticket_id}!")
            st.markdown("### Final Solution:")
            st.markdown(final_solution_to_save)
        else:
            st.error(f"Failed to save solution for ticket {ticket_id}.")
