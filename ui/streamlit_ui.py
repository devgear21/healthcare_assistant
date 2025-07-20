"""
Streamlit User Interface for the Medical AI Agent.
Provides a web-based chat interface for patients to interact with the AI.
"""

import streamlit as st
import os
import sys
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from medical_graph.medical_graph import process_patient_message, get_patient_conversation_history, clear_patient_conversation
from utils.fhir_utils import get_patient_info, search_patients
from monitoring.langsmith_setup import setup_monitoring

# Configure page
st.set_page_config(
    page_title="🩺 Medical AI Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize monitoring
setup_monitoring()

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "patient_id" not in st.session_state:
        st.session_state.patient_id = None
    
    if "patient_info" not in st.session_state:
        st.session_state.patient_info = None
    
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False

def render_sidebar():
    """Render the sidebar with patient information and controls."""
    st.sidebar.title("🩺 Medical AI Assistant")
    st.sidebar.markdown("---")
    
    # Patient identification
    st.sidebar.subheader("👤 Patient Information")
    
    # Patient ID input
    patient_id = st.sidebar.text_input(
        "Patient ID",
        value=st.session_state.patient_id or "",
        placeholder="e.g., patient-001",
        help="Enter your patient ID to access personalized services"
    )
    
    # Patient search
    search_query = st.sidebar.text_input(
        "Or search by name",
        placeholder="Enter patient name",
        help="Search for patient by name"
    )
    
    if search_query:
        patients = search_patients(search_query)
        if patients:
            patient_options = [f"{p['id']} - {p['name']}" for p in patients]
            selected = st.sidebar.selectbox("Select Patient", patient_options)
            if selected:
                patient_id = selected.split(" - ")[0]
    
    # Update patient info when ID changes
    if patient_id != st.session_state.patient_id:
        st.session_state.patient_id = patient_id
        if patient_id:
            st.session_state.patient_info = get_patient_info(patient_id)
        else:
            st.session_state.patient_info = None
    
    # Display patient information
    if st.session_state.patient_info:
        st.sidebar.success(f"✅ Logged in as: {st.session_state.patient_info['name']}")
        
        with st.sidebar.expander("📋 Patient Details"):
            st.write(f"**Name:** {st.session_state.patient_info.get('name', 'N/A')}")
            st.write(f"**Age:** {st.session_state.patient_info.get('age', 'N/A')}")
            st.write(f"**Gender:** {st.session_state.patient_info.get('gender', 'N/A')}")
            
            # Show allergies if any
            allergies = st.session_state.patient_info.get('allergies', [])
            if allergies:
                st.write(f"**⚠️ Allergies:** {', '.join(allergies)}")
    
    else:
        st.sidebar.info("💡 Enter your Patient ID for personalized service")
    
    st.sidebar.markdown("---")
    
    # Quick actions
    st.sidebar.subheader("🚀 Quick Actions")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("📅 Schedule", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": "I need to schedule an appointment",
                "timestamp": datetime.now()
            })
            st.rerun()
    
    with col2:
        if st.button("📋 Records", use_container_width=True):
            st.session_state.messages.append({
                "role": "user", 
                "content": "Show me my medical records",
                "timestamp": datetime.now()
            })
            st.rerun()
    
    col3, col4 = st.sidebar.columns(2)
    
    with col3:
        if st.button("💊 Medications", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": "What medications am I taking?",
                "timestamp": datetime.now()
            })
            st.rerun()
    
    with col4:
        if st.button("❓ FAQ", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": "What are your office hours?",
                "timestamp": datetime.now()
            })
            st.rerun()
    
    st.sidebar.markdown("---")
    
    # Emergency button
    if st.sidebar.button("🚨 EMERGENCY", type="primary", use_container_width=True):
        st.session_state.messages.append({
            "role": "user",
            "content": "This is a medical emergency",
            "timestamp": datetime.now()
        })
        st.rerun()
    
    st.sidebar.markdown("---")
    
    # Conversation controls
    st.sidebar.subheader("💬 Conversation")
    
    if st.sidebar.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        if st.session_state.patient_id:
            clear_patient_conversation(st.session_state.patient_id)
        st.rerun()
    
    # Show conversation stats
    if st.session_state.messages:
        st.sidebar.info(f"📊 Messages: {len(st.session_state.messages)}")

def render_example_prompts():
    """Render example prompts for users."""
    st.subheader("💡 Try asking me about:")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🏥 Appointments**
        - "Schedule an appointment"
        - "When is my next appointment?"
        - "Cancel my appointment"
        - "Reschedule for next week"
        """)
    
    with col2:
        st.markdown("""
        **📋 Medical Records**
        - "Show my medical history"
        - "What medications am I on?"
        - "Do I have any allergies?"
        - "Give me a summary of my records"
        """)
    
    with col3:
        st.markdown("""
        **❓ General Questions**
        - "What are your office hours?"
        - "How do I get prescription refills?"
        - "What insurance do you accept?"
        - "How do I access my lab results?"
        """)

def render_message(message: Dict, is_user: bool = True):
    """Render a chat message."""
    if is_user:
        with st.chat_message("user", avatar="👤"):
            st.write(message["content"])
            if "timestamp" in message:
                st.caption(f"🕐 {message['timestamp'].strftime('%H:%M:%S')}")
    else:
        with st.chat_message("assistant", avatar="🩺"):
            st.markdown(message["content"])
            if "timestamp" in message:
                st.caption(f"🕐 {message['timestamp'].strftime('%H:%M:%S')}")

def main():
    """Main Streamlit application."""
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main content area
    st.title("🩺 Medical AI Assistant")
    st.markdown("*Your intelligent healthcare companion*")
    
    # Safety disclaimer
    with st.expander("⚠️ Important Safety Information", expanded=False):
        st.warning("""
        **MEDICAL DISCLAIMER:**
        - This AI assistant is for informational purposes only
        - It cannot replace professional medical advice, diagnosis, or treatment
        - For emergencies, call 911 immediately
        - Always consult your healthcare provider for medical decisions
        - Do not use this for urgent medical situations
        """)
    
    # Chat interface
    st.markdown("---")
    
    # Always show conversation section
    st.subheader("💬 Conversation")
    
    # Display conversation history
    if st.session_state.messages:
        for message in st.session_state.messages:
            if message["role"] == "user":
                render_message(message, is_user=True)
            else:
                render_message(message, is_user=False)
    
    else:
        # Show welcome message and examples when no conversation yet
        st.markdown("""
        ### 👋 Welcome to your Medical AI Assistant!
        
        I'm here to help you with:
        - 📅 **Scheduling appointments**
        - 📋 **Accessing medical records** 
        - 💊 **Medication information**
        - ❓ **General health questions**
        - 🚨 **Emergency situations** (though please call 911 for true emergencies)
        """)
        
        render_example_prompts()
        
        st.markdown("---")
        st.info("💡 **Tip:** Enter your Patient ID in the sidebar for personalized service!")
    
    # Chat input
    user_input = st.chat_input(
        "Type your message here... (e.g., 'Schedule an appointment' or 'Show my medications')",
        key="chat_input"
    )
    
    if user_input:
        st.write("🐛 DEBUG: User input received:", user_input)  # Debug
        
        # Add user message
        user_message = {
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        }
        st.session_state.messages.append(user_message)
        st.write("🐛 DEBUG: User message added to session")  # Debug
        
        # Process with AI agent
        with st.spinner("🤔 Processing your request..."):
            try:
                st.write("🐛 DEBUG: Calling process_patient_message...")  # Debug
                
                # Get AI response
                ai_response = process_patient_message(
                    message=user_input,
                    patient_id=st.session_state.patient_id,
                    context=""
                )
                
                st.write("🐛 DEBUG: Got AI response:", ai_response[:100] + "...")  # Debug
                
                # Add AI response
                ai_message = {
                    "role": "assistant",
                    "content": ai_response,
                    "timestamp": datetime.now()
                }
                st.session_state.messages.append(ai_message)
                st.write("🐛 DEBUG: AI message added to session")  # Debug
                
            except Exception as e:
                st.write("🐛 DEBUG: Exception occurred:", str(e))  # Debug
                st.error(f"Sorry, I encountered an error: {str(e)}")
                st.info("Please try again or contact our office at (555) 123-4567")
        
        # Force rerun to show new messages
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        🏥 Medical AI Assistant | For non-emergency use only | Call 911 for emergencies<br>
        Office: (555) 123-4567 | Portal: patient.hospital.com
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
