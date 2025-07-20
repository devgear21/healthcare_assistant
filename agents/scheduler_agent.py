"""
Scheduler Agent for the Medical AI System.
Handles appointment booking, rescheduling, and cancellation.
"""

import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from utils.fhir_utils import (
    get_patient_appointments, 
    get_available_doctors, 
    get_doctor_availability,
    book_appointment,
    fhir_manager
)
import logging
import re

logger = logging.getLogger(__name__)

class SchedulerAgent:
    """Handles appointment scheduling, rescheduling, and cancellation."""
    
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.scheduling_prompt = PromptTemplate(
            input_variables=["request", "patient_info", "available_slots", "current_appointments"],
            template="""
You are a medical appointment scheduling assistant. Help the patient with their scheduling request.

PATIENT INFORMATION:
{patient_info}

CURRENT APPOINTMENTS:
{current_appointments}

SCHEDULING REQUEST:
{request}

AVAILABLE TIME SLOTS:
{available_slots}

INSTRUCTIONS:
1. Understand what the patient wants (book, reschedule, cancel, check appointments)
2. If booking: suggest appropriate time slots and doctors
3. If rescheduling: identify the appointment and suggest new times
4. If canceling: confirm which appointment to cancel
5. Provide clear, helpful responses with specific options
6. Ask for clarification if the request is unclear

Provide a helpful response and specify any actions that need to be taken.
"""
        )
    
    def handle_schedule(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle appointment scheduling requests."""
        message = state.get("message", "")
        patient_id = state.get("patient_id", "patient-001")  # Default for demo
        
        logger.info(f"Processing scheduling request for patient {patient_id}")
        
        try:
            # Analyze the scheduling request
            request_type = self._analyze_request_type(message)
            
            # Get patient's current appointments
            current_appointments = get_patient_appointments(patient_id)
            
            # Handle different types of requests
            if request_type == "book":
                response = self._handle_booking_request(message, patient_id, current_appointments)
            elif request_type == "reschedule":
                response = self._handle_reschedule_request(message, patient_id, current_appointments)
            elif request_type == "cancel":
                response = self._handle_cancel_request(message, patient_id, current_appointments)
            elif request_type == "check":
                response = self._handle_check_appointments(patient_id, current_appointments)
            else:
                response = self._handle_general_scheduling(message, patient_id, current_appointments)
            
            return {
                **state,
                "response": response,
                "request_type": request_type,
                "next_action": "scheduling_complete"
            }
            
        except Exception as e:
            logger.error(f"Scheduling request failed: {e}")
            return {
                **state,
                "response": "I apologize, but I'm having trouble accessing the scheduling system right now. Please call our office at (555) 123-4567 to schedule your appointment.",
                "request_type": "error",
                "next_action": "scheduling_complete"
            }
    
    def _analyze_request_type(self, message: str) -> str:
        """Analyze the type of scheduling request."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["book", "schedule", "make appointment", "new appointment"]):
            return "book"
        elif any(word in message_lower for word in ["reschedule", "change", "move", "different time"]):
            return "reschedule"
        elif any(word in message_lower for word in ["cancel", "delete", "remove"]):
            return "cancel"
        elif any(word in message_lower for word in ["check", "see", "view", "list", "my appointments"]):
            return "check"
        else:
            return "general"
    
    def _handle_booking_request(self, message: str, patient_id: str, current_appointments: List[Dict]) -> str:
        """Handle new appointment booking requests."""
        try:
            # Extract preferred details from message
            preferred_details = self._extract_scheduling_details(message)
            
            # Get available doctors
            available_doctors = get_available_doctors(preferred_details.get("specialty"))
            
            if not available_doctors:
                return "I'm sorry, but we don't have any doctors available for that specialty right now. Please call our office at (555) 123-4567 for assistance."
            
            # Generate available time slots
            available_slots = self._get_available_time_slots(available_doctors, preferred_details)
            
            # Format patient info for context
            patient_info = f"Patient ID: {patient_id}"
            current_appts_text = self._format_appointments(current_appointments)
            
            # Use AI to generate response
            ai_response = self._generate_scheduling_response(
                message, patient_info, available_slots, current_appts_text
            )
            
            # If specific details were extracted, try to book automatically
            if self._can_auto_book(preferred_details, available_slots):
                booking_result = self._attempt_auto_booking(patient_id, preferred_details, available_slots)
                if booking_result:
                    return f"{ai_response}\n\n✅ **Appointment Booked Successfully!**\n{booking_result}"
            
            return ai_response
            
        except Exception as e:
            logger.error(f"Booking request failed: {e}")
            return "I'm having trouble accessing our scheduling system. Here are our available options:\n\n📞 **Call us:** (555) 123-4567\n🌐 **Online portal:** patient.hospital.com\n\nOur office hours are Monday-Friday 8 AM to 6 PM, Saturday 9 AM to 2 PM."
    
    def _handle_reschedule_request(self, message: str, patient_id: str, current_appointments: List[Dict]) -> str:
        """Handle appointment rescheduling requests."""
        if not current_appointments:
            return "I don't see any current appointments to reschedule. Would you like to book a new appointment instead?"
        
        # Show current appointments and ask for clarification
        appointments_text = "Here are your current appointments:\n\n"
        for i, appt in enumerate(current_appointments, 1):
            appointments_text += f"{i}. **{appt.get('doctor', 'Unknown Doctor')}** - {appt.get('date')} at {appt.get('time')}\n"
            appointments_text += f"   Type: {appt.get('type', 'Consultation')}\n\n"
        
        appointments_text += "Which appointment would you like to reschedule? Please specify the doctor name or date."
        
        # Get available slots for rescheduling
        available_doctors = get_available_doctors()
        available_slots = self._get_available_time_slots(available_doctors)
        
        if available_slots:
            appointments_text += f"\n\n**Available New Times:**\n{available_slots}"
        
        return appointments_text
    
    def _handle_cancel_request(self, message: str, patient_id: str, current_appointments: List[Dict]) -> str:
        """Handle appointment cancellation requests."""
        if not current_appointments:
            return "I don't see any current appointments to cancel."
        
        # Show current appointments
        appointments_text = "Here are your current appointments:\n\n"
        for i, appt in enumerate(current_appointments, 1):
            appointments_text += f"{i}. **{appt.get('doctor', 'Unknown Doctor')}** - {appt.get('date')} at {appt.get('time')}\n"
            appointments_text += f"   Type: {appt.get('type', 'Consultation')}\n\n"
        
        appointments_text += "Which appointment would you like to cancel? Please specify the doctor name or date.\n\n"
        appointments_text += "⚠️ **Cancellation Policy:** Please cancel at least 24 hours in advance to avoid fees."
        
        return appointments_text
    
    def _handle_check_appointments(self, patient_id: str, current_appointments: List[Dict]) -> str:
        """Handle requests to check current appointments."""
        if not current_appointments:
            return "You don't have any upcoming appointments scheduled.\n\nWould you like to book a new appointment? I can help you find available times with our doctors."
        
        appointments_text = "📅 **Your Upcoming Appointments:**\n\n"
        for appt in current_appointments:
            appointments_text += f"• **{appt.get('doctor', 'Unknown Doctor')}**\n"
            appointments_text += f"  📅 {appt.get('date')} at {appt.get('time')}\n"
            appointments_text += f"  🏥 {appt.get('type', 'Consultation')}\n"
            appointments_text += f"  📋 Status: {appt.get('status', 'Scheduled').title()}\n\n"
        
        appointments_text += "Need to make changes? I can help you reschedule or cancel appointments."
        
        return appointments_text
    
    def _handle_general_scheduling(self, message: str, patient_id: str, current_appointments: List[Dict]) -> str:
        """Handle general scheduling inquiries."""
        response = "I'm here to help with your appointments! I can assist you with:\n\n"
        response += "📅 **Booking new appointments**\n"
        response += "🔄 **Rescheduling existing appointments**\n"
        response += "❌ **Canceling appointments**\n"
        response += "📋 **Checking your current appointments**\n\n"
        
        # Show available doctors
        available_doctors = get_available_doctors()
        if available_doctors:
            response += "**Available Doctors:**\n"
            for doctor in available_doctors:
                response += f"• {doctor.get('name')} - {doctor.get('specialty')}\n"
        
        response += "\nWhat would you like to do with your appointments?"
        
        return response
    
    def _extract_scheduling_details(self, message: str) -> Dict[str, Any]:
        """Extract scheduling details from the message."""
        details = {}
        
        # Extract date preferences
        date_patterns = [
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",  # MM/DD/YYYY or MM-DD-YYYY
            r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)",
            r"(tomorrow|next week|this week)",
            r"(morning|afternoon|evening)"
        ]
        
        message_lower = message.lower()
        for pattern in date_patterns:
            match = re.search(pattern, message_lower)
            if match:
                details["preferred_time"] = match.group(1)
                break
        
        # Extract doctor/specialty preferences
        if "cardiologist" in message_lower or "heart" in message_lower:
            details["specialty"] = "Cardiology"
        elif "dermatologist" in message_lower or "skin" in message_lower:
            details["specialty"] = "Dermatology"
        elif "general" in message_lower or "primary" in message_lower:
            details["specialty"] = "Internal Medicine"
        
        return details
    
    def _get_available_time_slots(self, doctors: List[Dict], preferences: Dict = None) -> str:
        """Get formatted available time slots."""
        slots_text = ""
        
        for doctor in doctors[:3]:  # Show top 3 doctors
            doctor_slots = get_doctor_availability(doctor.get("id", ""))
            if doctor_slots:
                slots_text += f"**{doctor.get('name')} ({doctor.get('specialty')})**:\n"
                for slot in doctor_slots[:3]:  # Show first 3 slots
                    slots_text += f"  • {slot}\n"
                slots_text += "\n"
        
        if not slots_text:
            slots_text = "Please call (555) 123-4567 to check current availability."
        
        return slots_text
    
    def _format_appointments(self, appointments: List[Dict]) -> str:
        """Format appointments for display."""
        if not appointments:
            return "No current appointments"
        
        formatted = ""
        for appt in appointments:
            formatted += f"• {appt.get('doctor')} - {appt.get('date')} at {appt.get('time')}\n"
        
        return formatted
    
    def _generate_scheduling_response(self, request: str, patient_info: str, available_slots: str, current_appointments: str) -> str:
        """Generate AI response for scheduling."""
        try:
            prompt = self.scheduling_prompt.format(
                request=request,
                patient_info=patient_info,
                available_slots=available_slots,
                current_appointments=current_appointments
            )
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to generate scheduling response: {e}")
            return f"Here are the available time slots:\n\n{available_slots}\n\nPlease let me know which time works best for you!"
    
    def _can_auto_book(self, details: Dict, available_slots: str) -> bool:
        """Check if we can automatically book based on provided details."""
        # For now, return False to require manual confirmation
        # In a production system, you might auto-book for very specific requests
        return False
    
    def _attempt_auto_booking(self, patient_id: str, details: Dict, available_slots: str) -> str:
        """Attempt to automatically book an appointment."""
        # This would contain logic to parse available slots and book
        # For now, return a success message
        return "Appointment scheduled for tomorrow at 10:00 AM with Dr. Smith"

# Initialize scheduler agent
scheduler_agent = SchedulerAgent()

def handle_schedule(state: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to handle scheduling requests."""
    return scheduler_agent.handle_schedule(state)
