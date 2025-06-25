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
    """Generate a solution from the voice call conversation through the proper backend workflow."""
    if not st.session_state.conversation_history:
        st.warning("No conversation to generate solution from.")
        return
    
    try:
        call_info = st.session_state.call_info
        ticket_data = call_info.get('ticket_data', {})
        employee_data = call_info.get('employee_data', {})
        
        # Generate conversation summary
        conversation_summary = "\n".join([f"{speaker}: {message}" for speaker, message in st.session_state.conversation_history])
        
        print("🔄 END_CALL: Starting solution generation...")
        print(f"🔄 END_CALL: Conversation history items: {len(st.session_state.conversation_history)}")
        print(f"🔄 END_CALL: Conversation summary length: {len(conversation_summary)}")
        print(f"🔄 END_CALL: Call info: {call_info}")
        print(f"🔄 END_CALL: Ticket data: {ticket_data}")
        
        with st.spinner("🔄 Processing call completion through backend workflow..."):
            
            print("🔄 END_CALL: Checking workflow client availability...")
            # Step 1: Send END_CALL through the proper backend workflow
            if (hasattr(st.session_state, 'workflow_client') and 
                st.session_state.workflow_client and 
                st.session_state.workflow_client.service_integration):
                print("🔄 END_CALL: Workflow client available - using existing service integration")
                
                # 🔧 CRITICAL FIX: Capture workflow reference BEFORE entering thread
                # Session state is not accessible from background threads
                workflow_client = st.session_state.workflow_client
                service_integration = workflow_client.service_integration
                print("🔄 END_CALL: Service integration references captured for thread execution")
                
                print(f"🔄 END_CALL: Sending conversation through backend workflow...")
                print(f"🔄 END_CALL: ✨ USING SIMPLIFIED SERVICE INTEGRATION APPROACH ✨")
                print(f"🔄 END_CALL: Processing conversation for solution generation")
                print(f"🔄 END_CALL: Conversation length: {len(conversation_summary)}")
                print(f"🔄 END_CALL: Employee: {employee_data.get('full_name', 'Unknown')}")
                
                # Add thread-safe timeout handling instead of signal
                import concurrent.futures
                import time
                
                def execute_workflow():
                    print("🔄 END_CALL: Starting workflow execution...")
                    start_time = time.time()
                    
                    # Use the captured service integration (no session state access needed)
                    print(f"🔄 END_CALL: Using captured service integration: {type(service_integration)}")
                    
                    # 🔧 FIXED: Use END_CALL workflow instead of regular query processing
                    print(f"🔄 END_CALL: 🔧 USING CALL COMPLETION WORKFLOW (not regular query)")
                    
                    # Create END_CALL state for proper call completion processing
                    end_call_state = {
                        "results": {
                            "vocal_assistant": {
                                "action": "end_call",
                                "status": "call_completed", 
                                "conversation_summary": conversation_summary,
                                "conversation_data": {
                                    "conversation_summary": conversation_summary,
                                    "response": conversation_summary
                                }
                            },
                            "ticket_data": ticket_data,
                            "employee_data": employee_data
                        },
                        "messages": [{"content": conversation_summary, "type": "user"}],
                        "metadata": {
                            "ticket_id": ticket_data.get('id'),
                            "employee_username": employee_data.get('username')
                        }
                    }
                    
                    print(f"🔄 END_CALL: 🔧 FIXED: Using process_end_call() method for proper routing")
                    print(f"🔄 END_CALL: 🔧 FIXED: END_CALL state prepared with conversation data")
                    
                    try:
                        # Use the multi-agent workflow's process_end_call method
                        workflow = service_integration.multi_agent_workflow
                        result = workflow.process_end_call(end_call_state)
                        
                        print(f"🔄 END_CALL: 🔧 FIXED: process_end_call() completed successfully")
                        print(f"🔄 END_CALL: Result: {result}")
                        
                        execution_time = time.time() - start_time
                        print(f"🔄 END_CALL: Workflow completed in {execution_time:.2f} seconds")
                        
                        return result
                        
                    except Exception as e:
                        print(f"❌ END_CALL: 🔧 process_end_call() failed: {e}")
                        execution_time = time.time() - start_time
                        print(f"🔄 END_CALL: Failed after {execution_time:.2f} seconds")
                        return {
                            "status": "error",
                            "error": f"Failed to process call completion: {str(e)}",
                            "conversation_summary": conversation_summary
                        }
                
                # Use ThreadPoolExecutor for thread-safe timeout
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    print("🔄 END_CALL: Submitting workflow task...")
                    future = executor.submit(execute_workflow)
                    
                    try:
                        print("🔄 END_CALL: Waiting for workflow result (30s timeout)...")
                        result = future.result(timeout=30)
                        
                        print(f"🔄 END_CALL: Workflow completed successfully!")
                        print(f"🔄 END_CALL: Result type: {type(result)}")
                        print(f"🔄 END_CALL: Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                        
                    except concurrent.futures.TimeoutError:
                        print("❌ END_CALL: Workflow execution timed out after 30 seconds")
                        st.error("⏰ Call processing timed out. Please try again.")
                        return
                        
                    except Exception as workflow_error:
                        print(f"❌ END_CALL: Workflow execution failed: {workflow_error}")
                        print(f"❌ END_CALL: Error type: {type(workflow_error)}")
                        import traceback
                        print(f"❌ END_CALL: Traceback: {traceback.format_exc()}")
                        st.error(f"❌ Workflow execution failed: {str(workflow_error)}")
                        return
                
                print(f"🔄 END_CALL: Processing workflow results...")
                print(f"🔄 END_CALL: Result type: {type(result)}")
                print(f"🔄 END_CALL: Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
                
                # Enhanced debugging for solution extraction
                print(f"🔄 END_CALL: === SOLUTION EXTRACTION DEBUG ===")
                
                # Check if a redirect was detected
                redirect_result = result.get("results", {}).get("redirect_info") if "results" in result else result.get("redirect_info")
                
                # 🔧 ENHANCED: Look for maestro final result in multiple locations with detailed logging
                print(f"🔄 END_CALL: Checking for maestro final result...")
                
                # Priority 1: Service integration returns response in 'result' field
                maestro_final_result = result.get("result")
                if maestro_final_result:
                    print(f"🔄 END_CALL: Found solution in 'result' field (service integration format): {str(maestro_final_result)[:100]}...")
                
                # Priority 2: Direct response field
                if not maestro_final_result:
                    maestro_final_result = result.get("response")
                    if maestro_final_result:
                        print(f"🔄 END_CALL: Found solution in 'response' field: {str(maestro_final_result)[:100]}...")
                
                # Priority 3: Final response field
                if not maestro_final_result:
                    maestro_final_result = result.get("final_response")
                    if maestro_final_result:
                        print(f"🔄 END_CALL: Found solution in 'final_response' field: {str(maestro_final_result)[:100]}...")
                
                # Priority 4: Synthesis field
                if not maestro_final_result:
                    maestro_final_result = result.get("synthesis")
                    if maestro_final_result:
                        print(f"🔄 END_CALL: Found solution in 'synthesis' field: {str(maestro_final_result)[:100]}...")
                
                # Priority 4: Results structure
                if not maestro_final_result and result.get("results"):
                    results = result.get("results", {})
                    print(f"🔄 END_CALL: Searching in results structure with keys: {list(results.keys())}")
                    
                    # Check various result fields
                    maestro_final_result = (
                        results.get("response") or
                        results.get("final_response") or 
                        results.get("synthesis") or
                        results.get("maestro_final") or
                        results.get("solution")
                    )
                    
                    if maestro_final_result:
                        print(f"🔄 END_CALL: Found solution in results structure: {str(maestro_final_result)[:100]}...")
                
                # Priority 5: Look for any field containing "final" or "solution"
                if not maestro_final_result and isinstance(result, dict):
                    print(f"🔄 END_CALL: Searching for solution-related fields...")
                    for key, value in result.items():
                        if any(keyword in key.lower() for keyword in ['final', 'solution', 'response', 'answer']):
                            if isinstance(value, str) and len(value.strip()) > 10:
                                maestro_final_result = value
                                print(f"🔄 END_CALL: Found solution in '{key}' field: {str(value)[:100]}...")
                                break
                            elif isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    if isinstance(sub_value, str) and len(sub_value.strip()) > 10:
                                        maestro_final_result = sub_value
                                        print(f"🔄 END_CALL: Found solution in '{key}.{sub_key}' field: {str(sub_value)[:100]}...")
                                        break
                                if maestro_final_result:
                                    break
                
                # 🔧 CHECK: Is this a redirect call initiation or just redirect detection?
                call_info_from_result = result.get("results", {}).get("call_info")
                vocal_action = result.get("results", {}).get("vocal_action")
                redirect_call_initiated = result.get("redirect_call_initiated", False)
                call_waiting = result.get("status") == "call_waiting"
                
                print(f"🔄 END_CALL: Redirect result: {redirect_result}")
                print(f"🔄 END_CALL: Maestro final result type: {type(maestro_final_result)}")
                print(f"🔄🔄🔄🔄 END_CALL: Maestro final result: {maestro_final_result if isinstance(maestro_final_result, str) else str(maestro_final_result)[:200]}...")
                print(f"🔄🔄🔄🔄 END_CALL: Direct final_response: {'Yes' if result.get('final_response') else 'No'}")
                print(f"🔄🔄🔄🔄 END_CALL: Direct synthesis: {'Yes' if result.get('synthesis') else 'No'}")
                print(f"🔄 END_CALL: Vocal action: {vocal_action}")
                print(f"🔄 END_CALL: Call waiting: {call_waiting}")
                print(f"🔄 END_CALL: Redirect call initiated: {redirect_call_initiated}")
                
                # 🔧 NEW LOGIC: Check if this is a redirect call initiation
                if redirect_result and (vocal_action == "start_call" or call_waiting or redirect_call_initiated):
                    print("🔄 END_CALL: REDIRECT CALL INITIATION DETECTED!")
                    
                    # This is a redirect call initiation - start new call with redirected employee
                    if call_info_from_result:
                        st.success(f"🔄 Ticket redirected to: {call_info_from_result.get('employee_name', 'Unknown')}")
                        st.info("📞 Initiating call with the new assignee...")
                        
                        # Update session state with new employee info
                        st.session_state.call_info = call_info_from_result
                        st.session_state.call_active = True
                        
                        # Show redirect details
                        if isinstance(redirect_result, dict):
                            st.markdown("### 🔄 Redirect Details")
                            for key, value in redirect_result.items():
                                if value and value != "NONE":
                                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                        
                        st.rerun()  # Restart the interface with new employee
                        return
                    else:
                        st.error("❌ Redirect detected but no call info available")
                        
                # If redirect was detected but no call initiation, show redirect confirmation
                elif redirect_result:
                    print("🔄 END_CALL: REDIRECT DETECTED AND PROCESSED!")
                    st.success("🔄 Redirect request detected and processed!")
                    st.info(f"📧 A redirect request has been sent. The workflow has handled the redirection automatically.")
                    
                    # Show redirect details if available
                    if isinstance(redirect_result, dict):
                        st.markdown("### 🔄 Redirect Details")
                        for key, value in redirect_result.items():
                            if value and value != "NONE":
                                st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                    
                    # For redirects, save a redirect confirmation to the ticket instead of a solution
                    redirect_confirmation = f"""Voice consultation completed with {employee_data.get('full_name', 'our technical expert')}.

**Ticket:** {ticket_data.get('subject', 'Support Request')}
**Expert:** {employee_data.get('full_name', 'Technical Specialist')} ({employee_data.get('role_in_company', 'IT Team')})

🔄 **REDIRECT PROCESSED**: A redirect request was detected during the call and has been automatically processed. The appropriate team member will be contacted to handle this request.

**Redirect Details:**
{chr(10).join([f"• {key.replace('_', ' ').title()}: {value}" for key, value in redirect_result.items() if value and value != "NONE"])}

If you need further assistance, please create a new support ticket."""
                    
                    ticket_id = call_info.get('ticket_id')
                    if ticket_id:
                        st.session_state.ticket_manager.update_employee_solution(ticket_id, redirect_confirmation)
                        st.success("✅ Redirect confirmation saved to ticket!")
                    
                    return  # Early return - no need to look for additional solutions
                
                else:
                    print("🔄 END_CALL: No redirect detected - looking for regular solution")
                
                print(f"🔄 END_CALL: === FINAL SOLUTION PROCESSING ===")
                
                # Extract the actual solution text
                final_solution = None
                if isinstance(maestro_final_result, dict):
                    # For dict results, look for common response keys
                    final_solution = (
                        maestro_final_result.get("result") or 
                        maestro_final_result.get("response") or
                        maestro_final_result.get("solution") or
                        maestro_final_result.get("answer") or
                        maestro_final_result.get("text")
                    )
                    print(f"� END_CALL: Extracted from dict using keys: {final_solution[:100] if final_solution else 'None'}...")
                elif isinstance(maestro_final_result, str) and len(maestro_final_result.strip()) > 20:
                    # Check if this looks like a real solution vs an error message
                    solution_text = maestro_final_result.strip()
                    
                    # Skip obvious error patterns
                    error_patterns = [
                        "query processing failed",
                        "workflow processing incomplete", 
                        "no response generated",
                        "error:",
                        "failed:",
                        "timeout",
                        "could not"
                    ]
                    
                    is_error = any(pattern.lower() in solution_text.lower() for pattern in error_patterns)
                    
                    if not is_error:
                        final_solution = solution_text
                        print(f"🔄 END_CALL: Valid solution text extracted: {final_solution[:100]}...")
                    else:
                        print(f"🔄 END_CALL: Detected error message, not a solution: {solution_text[:100]}...")
                
                # 🔧 ENHANCED: Additional fallback checks with better extraction
                if not final_solution:
                    print(f"🔄 END_CALL: No direct solution found, checking alternative locations...")
                    
                    # Check for direct response in root
                    if result.get("response") and isinstance(result["response"], str):
                        final_solution = result["response"].strip()
                        print(f"🔄 END_CALL: Found in root response: {final_solution[:100]}...")
                    
                    # Check for any string field with substantial content
                    elif isinstance(result, dict):
                        for key, value in result.items():
                            if isinstance(value, str) and len(value.strip()) > 50:
                                # Skip error messages and status fields
                                if not any(skip_word in key.lower() for skip_word in ['error', 'status', 'debug', 'log']):
                                    final_solution = value.strip()
                                    print(f"🔄 END_CALL: Found substantial text in '{key}': {final_solution[:100]}...")
                                    break
                
                print(f"🔄 END_CALL: Final solution extracted: {'Yes' if final_solution else 'No'}")
                if final_solution:
                    print(f"🔄 END_CALL: Final solution length: {len(final_solution)}")
                    print(f"🔄 END_CALL: Final solution preview: {final_solution[:100]}...")
                    print(f"🔄 END_CALL: Solution type: {'Maestro Final' if 'voice conversation' in final_solution else 'Other'}")
                else:
                    print(f"🔄 END_CALL: No final solution found - will use fallback")
                
                # Save solution to ticket
                if final_solution and final_solution.strip():
                    ticket_id = call_info.get('ticket_id')
                    if ticket_id:
                        st.session_state.ticket_manager.update_employee_solution(ticket_id, final_solution)
                        st.success("✅ Solution processed through backend workflow and saved!")
                        
                        # Show the final solution
                        st.markdown("### 📝 Final Solution")
                        st.success(final_solution)
                    else:
                        st.error("Could not save solution: No ticket ID found.")
                else:
                    # Fallback: Generate a basic solution if workflow didn't provide one
                    # This should only happen for legitimate call completions without redirects
                    st.warning("⚠️ Workflow completed but no solution generated. Creating completion confirmation...")
                    
                    fallback_solution = f"""Voice consultation completed with {employee_data.get('full_name', 'our technical expert')}.

**Ticket:** {ticket_data.get('subject', 'Support Request')}
**Expert:** {employee_data.get('full_name', 'Technical Specialist')} ({employee_data.get('role_in_company', 'IT Team')})

The call has been completed successfully. Any questions or issues discussed during the call have been addressed.

If you need further assistance, please create a new support ticket."""
                    
                    ticket_id = call_info.get('ticket_id')
                    if ticket_id:
                        st.session_state.ticket_manager.update_employee_solution(ticket_id, fallback_solution)
                        st.success("✅ Call completion confirmation saved!")
                        st.info(fallback_solution)
            
            else:
                # Fallback if workflow not available - use old method
                print("⚠️ END_CALL: Backend workflow not available. Using fallback method...")
                st.warning("⚠️ Backend workflow not available. Using fallback method...")
                
                # Create basic solution from conversation
                basic_solution = f"""Voice consultation completed with {employee_data.get('full_name', 'our technical expert')}.

**Issue:** {ticket_data.get('description', 'Technical support requested')}
**Expert:** {employee_data.get('full_name', 'Technical Specialist')} ({employee_data.get('role_in_company', 'IT Team')})

The call has been completed. Please refer to any instructions provided during the conversation.

If you need additional help, please create a new support ticket."""

                print(f"🔄 END_CALL: Fallback solution created (length: {len(basic_solution)})")
                
                ticket_id = call_info.get('ticket_id')
                if ticket_id:
                    print(f"🔄 END_CALL: Saving fallback solution to ticket {ticket_id}")
                    st.session_state.ticket_manager.update_employee_solution(ticket_id, basic_solution)
                    st.success("✅ Basic solution saved!")
                    st.info(basic_solution)
                else:
                    print("❌ END_CALL: No ticket ID found for saving solution")
                    st.error("❌ Could not save solution: No ticket ID found")
                
                ticket_id = call_info.get('ticket_id')
                if ticket_id:
                    st.session_state.ticket_manager.update_employee_solution(ticket_id, basic_solution)
                    st.success("✅ Basic solution saved!")
                    st.info(basic_solution)
    
    except Exception as e:
        print(f"❌ END_CALL CRITICAL ERROR: {str(e)}")
        print(f"❌ END_CALL ERROR TYPE: {type(e)}")
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ END_CALL TRACEBACK: {error_traceback}")
        
        st.error(f"❌ Error processing call completion: {str(e)}")
        st.error("📋 Check console for detailed error information")
        
        # Show abbreviated traceback to user
        with st.expander("🔍 Technical Details"):
            st.code(error_traceback)
    
    finally:
        print("🔄 END_CALL: Cleanup starting...")
        # Ensure complete cleanup of call state
        st.session_state.call_active = False
        st.session_state.call_info = None
        st.session_state.conversation_history = []
        
        # Clear any ongoing audio processing states
        if 'last_audio_process_time' in st.session_state:
            del st.session_state.last_audio_process_time
            print("🔄 END_CALL: Cleared last_audio_process_time")
        if 'last_audio_hash' in st.session_state:
            del st.session_state.last_audio_hash
            print("🔄 END_CALL: Cleared last_audio_hash")
        
        # Clear any vocal chat processing states that might cause re-answering
        if 'vocal_chat' in st.session_state and hasattr(st.session_state.vocal_chat, 'gemini'):
            # Reset any conversation memory in the AI chat
            try:
                st.session_state.vocal_chat.gemini.conversation_memory = []
                print("🔄 END_CALL: Cleared vocal chat memory")
            except:
                pass
        
        print("🔄 END_CALL: Cleanup completed, triggering rerun...")
        st.rerun()
