"""
Voice call interface and processing for ticket system.
"""

import streamlit as st
import time
import base64
from pathlib import Path


def show_active_call_interface():
    """Display the active voice call interface."""
    call_info = st.session_state.call_info
    
    # Add custom CSS for call interface
    st.markdown("""
    <style>
    .call-interface {
        background: linear-gradient(90deg, #28a745, #20c997);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Call header with animation
    st.markdown(f"""
    <div class='call-interface'>
        <h2>📞 Active Call</h2>
        <p><strong>Employee:</strong> {call_info.get('employee_name', 'Unknown')}</p>
        <p><strong>Ticket:</strong> {call_info.get('ticket_subject', 'No subject')}</p>
        <p><strong>Ticket ID:</strong> {call_info.get('ticket_id', 'Unknown')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize vocal chat if not exists
    if not st.session_state.vocal_chat:
        from vocal_components import SmoothVocalChat
        st.session_state.vocal_chat = SmoothVocalChat()
    
    # Voice interface with audio controls
    st.markdown("### 🎤 Voice Conversation")
    st.markdown("Speak into the microphone to discuss the ticket with the employee.")
    
    # Audio quality controls
    with st.expander("🔧 Audio Settings", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            # Microphone sensitivity control
            pause_threshold = st.slider(
                "Recording Sensitivity",
                min_value=0.5,
                max_value=4.0,
                value=2.0,
                step=0.5,
                help="Higher values = less sensitive (need louder voice)"
            )
            
        with col2:
            # Sample rate for noise reduction
            sample_rate = st.selectbox(
                "Audio Quality",
                options=[16000, 22050, 44100],
                index=0,  # Default to 16000 for better noise handling
                help="Lower rates reduce noise but may affect quality"
            )
    
    # Enhanced permission reminder with audio tips
    st.info("💡 Audio Tips: Speak clearly, minimize background noise, allow microphone access, and adjust sensitivity if needed.")
    
    # Import audio recorder
    try:
        from audio_recorder_streamlit import audio_recorder
        
        # Enhanced audio recorder configuration with user controls
        audio_bytes = audio_recorder(
            text="Click to record",
            recording_color="#ff4444",
            neutral_color="#28a745",
            icon_name="microphone",
            icon_size="3x",
            pause_threshold=pause_threshold,  # User-controlled sensitivity
            sample_rate=sample_rate,          # User-controlled quality
            key="call_audio_recorder"
        )
        
        # Improved processing - prevent duplicates but allow legitimate recordings
        if audio_bytes:
            current_time = time.time()
            last_process_time = st.session_state.get('last_audio_process_time', 0)
            last_audio_hash = st.session_state.get('last_audio_hash', '')
            
            # Create simple hash of audio to detect duplicates
            import hashlib
            audio_hash = hashlib.md5(audio_bytes).hexdigest()[:8]
            
            # Allow processing if:
            # 1. More than 1 second has passed (reduced from 2), OR
            # 2. Audio content is different (different hash)
            time_passed = (current_time - last_process_time) > 1.0
            audio_different = audio_hash != last_audio_hash
            
            if time_passed or audio_different:
                st.session_state.last_audio_process_time = current_time
                st.session_state.last_audio_hash = audio_hash
                
                # Check if call is still active before processing
                if not st.session_state.get('call_active', False):
                    st.info("Call has ended. No further audio processing.")
                    return
                
                with st.spinner("🔄 Processing voice input..."):
                    try:
                        # Double-check call state before processing
                        if not st.session_state.get('call_active', False):
                            st.info("Call ended during processing.")
                            return
                        
                        # Get ticket and employee data
                        ticket_data = call_info.get('ticket_data', {})
                        employee_data = call_info.get('employee_data', {})
                        
                        # Process voice input
                        transcription, response, tts_audio_bytes = st.session_state.vocal_chat.process_voice_input(
                            audio_bytes, 
                            ticket_data, 
                            employee_data, 
                            st.session_state.conversation_history
                        )
                        
                        if transcription:
                            # Always show what was understood
                            st.success(f"**You said:** {transcription}")
                            
                            # Add transcription to conversation history
                            st.session_state.conversation_history.append(("You", transcription))
                            
                            if response:
                                # Add employee response to conversation history
                                st.session_state.conversation_history.append(("Employee", response))
                                st.info(f"**Employee:** {response}")
                                
                                # Play employee response
                                if tts_audio_bytes:
                                    st.audio(tts_audio_bytes, format='audio/mp3', autoplay=True)
                            else:
                                # Handle case where transcription worked but response failed
                                st.warning("🤔 The employee is thinking... Please try asking again or rephrase your question.")
                                # Still add a placeholder to maintain conversation flow
                                st.session_state.conversation_history.append(("Employee", "I need a moment to process that. Could you please rephrase or try again?"))
                        else:
                            # Handle case where transcription failed
                            st.error("❌ Could not understand the audio. Please speak clearly and try again.")
                            st.info("💡 Tips: Speak clearly, check your microphone, and ensure there's minimal background noise.")
                                
                    except Exception as e:
                        st.error(f"❌ Processing failed: {str(e)}")
                        st.info("💡 Try recording again")
            else:
                if not time_passed:
                    st.info("⏳ Recording too quickly - please wait a moment...")
                elif not audio_different:
                    st.info("🔄 Same audio detected - please record something new...")
                            
    except ImportError:
        st.error("❌ Audio recording not available. Please install audio-recorder-streamlit")
        st.code("pip install audio-recorder-streamlit")
    
    # Conversation history
    if st.session_state.conversation_history:
        st.markdown("### 📝 Conversation History")
        with st.expander("View conversation", expanded=False):
            for speaker, message in st.session_state.conversation_history:
                icon = "🎧" if speaker == "You" else "👨‍💼"
                st.markdown(f"**{icon} {speaker}:** {message}")
    
    # Call controls
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📴 End Call", type="secondary", use_container_width=True):
            # Immediately set call_active to False to prevent any further processing
            st.session_state.call_active = False
            
            # Generate solution from conversation if exists
            if st.session_state.conversation_history:
                generate_solution_from_call()
            else:
                # Clear all call-related session state
                st.session_state.call_info = None
                st.session_state.conversation_history = []
                # Clear any ongoing processing states
                if 'last_audio_process_time' in st.session_state:
                    del st.session_state.last_audio_process_time
                if 'last_audio_hash' in st.session_state:
                    del st.session_state.last_audio_hash
                st.rerun()
                st.session_state.call_info = None
                st.session_state.conversation_history = []
                st.rerun()
    
    with col2:
        if st.button("⏸️ Hold Call", use_container_width=True):
            st.info("Call placed on hold. Use the sidebar to resume.")
            st.session_state.call_active = False
            # Keep call_info for resuming
            st.rerun()


def generate_solution_from_call():
    """Generate a solution from the voice call conversation and route through Maestro for final review."""
    if not st.session_state.conversation_history:
        st.warning("No conversation to generate solution from.")
        return
    
    try:
        # Initialize vocal chat if needed
        if not st.session_state.vocal_chat:
            from vocal_components import SmoothVocalChat
            st.session_state.vocal_chat = SmoothVocalChat()
        
        call_info = st.session_state.call_info
        ticket_data = call_info.get('ticket_data', {})
        employee_data = call_info.get('employee_data', {})
        
        # Generate initial solution from conversation
        conversation_summary = "\n".join([f"{speaker}: {message}" for speaker, message in st.session_state.conversation_history])
        
        with st.spinner("🔄 Processing conversation and generating solution..."):
            # Step 1: Generate solution without any TTS - Simple text-based approach
            # Extract the last meaningful employee response from conversation
            employee_responses = []
            for speaker, message in st.session_state.conversation_history:
                if speaker == "Employee" and len(message.strip()) > 10:
                    employee_responses.append(message.strip())
            
            # Create a professional solution based on employee responses
            if employee_responses:
                # Use the most recent and comprehensive employee response
                main_solution = employee_responses[-1]
                
                # Format into professional solution
                initial_solution = f"""Based on our conversation with {employee_data.get('full_name', 'our technical expert')}, here is the recommended solution:

**Expert Recommendation:**
{main_solution}

**Technical Context:**
- Issue: {ticket_data.get('description', 'Technical issue reported')}
- Expert: {employee_data.get('full_name', 'Technical Specialist')} ({employee_data.get('role_in_company', 'IT Team')})
- Priority: {ticket_data.get('priority', 'Medium')}

**Next Steps:**
Please follow the expert's recommendation above. If you need further assistance, feel free to create a new support ticket.

This solution was generated from a voice consultation with our technical team."""
            else:
                # Fallback if no clear employee responses
                initial_solution = f"""A voice consultation was completed with {employee_data.get('full_name', 'our technical expert')} regarding your support request.

**Issue:** {ticket_data.get('description', 'Technical support requested')}

**Consultation Summary:**
Our technical expert has reviewed your case and provided guidance during the call. Please refer to any notes or instructions that were shared during the conversation.

If you need additional clarification or have follow-up questions, please create a new support ticket with specific details about what you need help with.

**Expert:** {employee_data.get('full_name', 'Technical Specialist')} ({employee_data.get('role_in_company', 'IT Team')})
**Priority:** {ticket_data.get('priority', 'Medium')}"""
            
            if not initial_solution:
                st.error("Failed to generate solution from conversation.")
                return
            
            # Step 2: Route through Maestro for comprehensive final review
            if hasattr(st.session_state, 'workflow_client') and st.session_state.workflow_client and st.session_state.workflow_client.system:
                # Prepare input for Maestro final review
                maestro_input = f"""Voice Call Solution Review

Original Ticket:
Subject: {ticket_data.get('subject', 'No subject')}
Description: {ticket_data.get('description', 'No description')}
Priority: {ticket_data.get('priority', 'Medium')}
User: {ticket_data.get('user', 'Unknown')}

Employee Expert: {employee_data.get('full_name', 'Unknown')} ({employee_data.get('role_in_company', 'Employee')})

Voice Call Conversation Summary:
{conversation_summary}

Employee Solution:
{initial_solution}

Create a concise, professional email response to the customer that:
- Starts with "Subject: Re: {ticket_data.get('subject', 'No subject')}"
- Uses a friendly greeting addressing the user by name
- Provides a clear, direct answer based on what the employee explained
- Includes one brief practical tip or advice if relevant
- Credits the employee who helped (e.g., "This solution was suggested by [Employee Name], our [Role]")
- Ends with "Best, Support Team"

Keep the response SHORT and focused - no bullet points, no detailed steps, just a clear helpful answer in paragraph form."""

                # Access MaestroAgent directly instead of going through full workflow
                maestro_agent = st.session_state.workflow_client.system.agents.get("maestro")
                if maestro_agent:
                    # Call Maestro directly for solution synthesis only
                    maestro_result = maestro_agent.run({
                        "query": maestro_input,
                        "stage": "final_review",
                        "data_guardian_result": initial_solution  # Use the employee solution as the "data source"
                    })
                else:
                    maestro_result = None
                
                # Extract final solution from Maestro's response
                final_solution = None
                if maestro_result and isinstance(maestro_result, dict):
                    # Direct agent response format
                    final_solution = maestro_result.get("result")
                elif isinstance(maestro_result, str):
                    final_solution = maestro_result
                
                print(f"Maestro final solution: {final_solution[:200]}...")  # Debug output
                # Use Maestro's final conclusion if available, otherwise fall back to initial solution
                solution_to_save = final_solution if final_solution and final_solution.strip() else initial_solution
                
                # Update ticket with Maestro's final solution
                ticket_id = call_info.get('ticket_id')
                if ticket_id:
                    st.session_state.ticket_manager.update_employee_solution(ticket_id, solution_to_save)
                    st.success("✅ Solution reviewed by Maestro and saved to ticket!")
                    
                    # Show the final solution
                    st.markdown("### 📝 Final Solution (Reviewed by Maestro)")
                    st.success(solution_to_save)
                    
                    if final_solution and final_solution != initial_solution:
                        with st.expander("View Original Employee Solution"):
                            st.info(initial_solution)
                else:
                    st.error("Could not save solution: No ticket ID found.")
            else:
                # Fallback: Save initial solution if Maestro is not available
                ticket_id = call_info.get('ticket_id')
                if ticket_id:
                    st.session_state.ticket_manager.update_employee_solution(ticket_id, initial_solution)
                    st.success("✅ Solution generated and saved to ticket!")
                    st.warning("⚠️ Maestro review not available - saved employee solution directly.")
                    
                    # Show the solution
                    st.markdown("### 📝 Generated Solution")
                    st.success(initial_solution)
                else:
                    st.error("Could not save solution: No ticket ID found.")
    
    except Exception as e:
        st.error(f"Error generating solution: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
    
    finally:
        # Ensure complete cleanup of call state
        st.session_state.call_active = False
        st.session_state.call_info = None
        st.session_state.conversation_history = []
        
        # Clear any ongoing audio processing states
        if 'last_audio_process_time' in st.session_state:
            del st.session_state.last_audio_process_time
        if 'last_audio_hash' in st.session_state:
            del st.session_state.last_audio_hash
        
        # Clear any vocal chat processing states that might cause re-answering
        if 'vocal_chat' in st.session_state and hasattr(st.session_state.vocal_chat, 'gemini'):
            # Reset any conversation memory in the AI chat
            try:
                st.session_state.vocal_chat.gemini.conversation_memory = []
            except:
                pass
        
        st.rerun()
