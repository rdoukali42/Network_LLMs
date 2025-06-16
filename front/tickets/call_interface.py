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
    
    # Voice interface
    st.markdown("### 🎤 Voice Conversation")
    st.markdown("Speak into the microphone to discuss the ticket with the employee.")
    
    # Import audio recorder
    try:
        from audio_recorder_streamlit import audio_recorder
        
        # Audio recorder with flexible sample rate for better voice capture
        audio_bytes = audio_recorder(
            text="Click to record",
            recording_color="#ff4444",
            neutral_color="#28a745",
            icon_name="microphone",
            icon_size="3x",
            pause_threshold=2.0,
            sample_rate=22050,  # Standard rate that works well for speech recognition
            key="call_audio_recorder"
        )
        
        # Process audio input - removed hash collision blocking to allow repeated processing
        if audio_bytes:
            # Generate unique processing ID based on timestamp to avoid blocking similar audio
            processing_id = f"{time.time()}_{len(audio_bytes)}"
            last_processing_id = st.session_state.get('last_call_processing_id', None)
            
            # Only skip if it's the exact same recording in rapid succession (within 1 second)
            current_time = time.time()
            last_process_time = st.session_state.get('last_process_time', 0)
            
            if processing_id != last_processing_id or (current_time - last_process_time) > 1.0:
                st.session_state.last_call_processing_id = processing_id
                st.session_state.last_process_time = current_time
                
                with st.spinner("🔄 Processing voice input..."):
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
                    
                    if transcription and response:
                        # Add to conversation history
                        st.session_state.conversation_history.append(("You", transcription))
                        st.session_state.conversation_history.append(("Employee", response))
                        
                        # Show transcription
                        st.success(f"**You said:** {transcription}")
                        st.info(f"**Employee:** {response}")
                        
                        # Play employee response
                        if tts_audio_bytes:
                            st.audio(tts_audio_bytes, format='audio/mp3', autoplay=True)
                            
    except ImportError:
        st.error("Audio recording not available. Please install audio_recorder_streamlit.")
        st.code("pip install audio_recorder_streamlit")
    
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
            # Generate solution from conversation
            if st.session_state.conversation_history:
                generate_solution_from_call()
            else:
                st.session_state.call_active = False
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
            # Step 1: Extract employee solution from conversation
            initial_solution = st.session_state.vocal_chat.gemini.chat(
                f"Generate a professional ticket resolution based on this conversation: {conversation_summary}",
                ticket_data,
                employee_data,
                is_employee=False
            )
            
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
                        "stage": "synthesize",
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
        # End the call
        st.session_state.call_active = False
        st.session_state.call_info = None
        st.session_state.conversation_history = []
        st.rerun()
