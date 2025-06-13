"""
Chat interface component for Streamlit app.
Handles the main chat functionality using the AI workflow.
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

# Add paths for imports
project_root = Path(__file__).parent.parent
front_dir = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(front_dir))

from auth import logout
from workflow_client import WorkflowClient

def show_chat_interface():
    """Display the main chat interface."""
    # Header with user info and logout
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title(f"🤖 AI Chat System - Welcome {st.session_state.username}")
    
    with col2:
        if st.button("Logout", use_container_width=True):
            logout()
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Initialize workflow client
    if "workflow_client" not in st.session_state:
        st.session_state.workflow_client = WorkflowClient()
    
    # Display chat history
    display_chat_history()
    
    # Chat input
    handle_chat_input()

def display_chat_history():
    """Display the chat history."""
    if st.session_state.chat_history:
        st.markdown("### Chat History")
        
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(f"**{message['timestamp']}**")
                    st.markdown(message["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(f"**{message['timestamp']}**")
                    st.markdown(message["content"])
    else:
        st.markdown("### Start a conversation")
        st.info("👋 Hello! I'm your AI assistant. Ask me anything!")

def handle_chat_input():
    """Handle user input and generate responses."""
    # Chat input
    user_input = st.chat_input("Type your message here...")
    
    if user_input:
        # Add user message to history
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": timestamp
        })
        
        # Show user message immediately
        with st.chat_message("user"):
            st.markdown(f"**{timestamp}**")
            st.markdown(user_input)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.workflow_client.process_query(user_input)
                    
                    if response and response.get("status") == "success":
                        ai_response = response.get("result", "I apologize, but I couldn't generate a response.")
                    else:
                        ai_response = f"Error: {response.get('error', 'Unknown error occurred')}"
                        
                except Exception as e:
                    ai_response = f"Error processing your request: {str(e)}"
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                st.markdown(f"**{timestamp}**")
                st.markdown(ai_response)
                
                # Add AI response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": timestamp
                })

def clear_chat_history():
    """Clear the chat history."""
    st.session_state.chat_history = []
    st.rerun()

# Add clear chat button in sidebar
if st.session_state.get("authenticated", False):
    with st.sidebar:
        st.markdown("### Chat Controls")
        if st.button("Clear Chat History", use_container_width=True):
            clear_chat_history()
