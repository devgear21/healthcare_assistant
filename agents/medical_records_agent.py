"""
Medical Records Agent for the Medical AI System.
Handles secure access to patient medical records, history, and updates.
"""

import os
from typing import Dict, Any, List, Optional
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from utils.fhir_utils import (
    get_patient_info,
    get_patient_medical_history,
    get_patient_medications,
    get_patient_allergies,
    fhir_manager
)
from utils.auth import require_authentication
import logging

logger = logging.getLogger(__name__)

class MedicalRecordsAgent:
    """Handles secure medical records access and updates."""
    
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.records_prompt = PromptTemplate(
            input_variables=["request", "patient_data", "medical_history", "medications", "allergies"],
            template="""
You are a secure medical records assistant. Help the patient with their medical records request.

PATIENT REQUEST:
{request}

PATIENT INFORMATION:
{patient_data}

MEDICAL HISTORY:
{medical_history}

CURRENT MEDICATIONS:
{medications}

KNOWN ALLERGIES:
{allergies}

GUIDELINES:
1. Only provide information that the patient is authorized to access
2. Present medical information clearly and understandably
3. Explain medical terms in simple language when needed
4. For medication questions, include dosage and frequency information
5. For allergies, emphasize the importance of informing healthcare providers
6. Suggest consulting healthcare providers for interpretation of medical data
7. Maintain patient privacy and confidentiality

SECURITY REMINDERS:
- Never share information with unauthorized individuals
- All medical records access is logged for security
- For updates to records, verification may be required

Provide a helpful, secure response to the patient's medical records request.
"""
        )
    
    @require_authentication
    def handle_records(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle medical records requests."""
        message = state.get("message", "")
        patient_id = state.get("patient_id", "patient-001")  # Default for demo
        
        logger.info(f"Processing medical records request for patient {patient_id}")
        
        try:
            # Determine the type of records request
            request_type = self._analyze_records_request(message)
            
            # Get patient data
            patient_data = get_patient_info(patient_id)
            if not patient_data:
                return {
                    **state,
                    "response": "I'm sorry, but I couldn't find your medical records. Please verify your patient ID or contact our office at (555) 123-4567.",
                    "request_type": "patient_not_found",
                    "next_action": "records_complete"
                }
            
            # Handle different types of records requests
            if request_type == "medical_history":
                response = self._handle_medical_history_request(patient_id, patient_data, message)
            elif request_type == "medications":
                response = self._handle_medications_request(patient_id, patient_data, message)
            elif request_type == "allergies":
                response = self._handle_allergies_request(patient_id, patient_data, message)
            elif request_type == "test_results":
                response = self._handle_test_results_request(patient_id, patient_data, message)
            elif request_type == "summary":
                response = self._handle_summary_request(patient_id, patient_data)
            elif request_type == "update":
                response = self._handle_update_request(patient_id, patient_data, message)
            else:
                response = self._handle_general_records_request(patient_id, patient_data, message)
            
            return {
                **state,
                "response": response,
                "request_type": request_type,
                "patient_verified": True,
                "next_action": "records_complete"
            }
            
        except Exception as e:
            logger.error(f"Medical records request failed: {e}")
            return {
                **state,
                "response": "I'm having trouble accessing your medical records right now. Please call our office at (555) 123-4567 or visit our patient portal for assistance.",
                "request_type": "system_error",
                "next_action": "records_complete"
            }
    
    def _analyze_records_request(self, message: str) -> str:
        """Analyze the type of medical records request."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["history", "medical history", "past", "conditions", "diagnoses"]):
            return "medical_history"
        elif any(word in message_lower for word in ["medication", "medicine", "prescription", "pills", "drugs"]):
            return "medications"
        elif any(word in message_lower for word in ["allergy", "allergies", "allergic", "reactions"]):
            return "allergies"
        elif any(word in message_lower for word in ["test", "lab", "results", "blood work", "x-ray", "scan"]):
            return "test_results"
        elif any(word in message_lower for word in ["summary", "overview", "complete", "all records"]):
            return "summary"
        elif any(word in message_lower for word in ["update", "change", "modify", "correct"]):
            return "update"
        else:
            return "general"
    
    def _handle_medical_history_request(self, patient_id: str, patient_data: Dict, message: str) -> str:
        """Handle medical history requests."""
        medical_history = get_patient_medical_history(patient_id)
        
        if not medical_history:
            return "Your medical records show no significant medical history on file. If you believe this is incorrect, please contact our office to update your records."
        
        response = "📋 **Your Medical History:**\n\n"
        
        for condition in medical_history:
            response += f"• **{condition.get('condition', 'Unknown condition')}**\n"
            response += f"  📅 Diagnosed: {condition.get('diagnosed', 'Date not specified')}\n"
            response += f"  📊 Status: {condition.get('status', 'Unknown').title()}\n\n"
        
        response += "⚠️ **Important:** This information is for your reference. Please discuss any questions about your medical history with your healthcare provider.\n\n"
        response += "🔄 **Need updates?** Contact our office if any information needs correction or if you have new conditions to report."
        
        return response
    
    def _handle_medications_request(self, patient_id: str, patient_data: Dict, message: str) -> str:
        """Handle current medications requests."""
        medications = get_patient_medications(patient_id)
        
        if not medications:
            return "Your records show no current medications on file. If you are taking medications, please contact our office to update your records."
        
        response = "💊 **Your Current Medications:**\n\n"
        
        for med in medications:
            response += f"• **{med.get('name', 'Unknown medication')}**\n"
            response += f"  💊 Dosage: {med.get('dosage', 'Not specified')}\n"
            response += f"  🕐 Frequency: {med.get('frequency', 'Not specified')}\n\n"
        
        response += "⚠️ **Medication Safety:**\n"
        response += "• Always take medications as prescribed\n"
        response += "• Inform all healthcare providers about your medications\n"
        response += "• Don't stop medications without consulting your doctor\n"
        response += "• Report any side effects immediately\n\n"
        response += "🔄 **Refills needed?** Contact our office or use the patient portal."
        
        return response
    
    def _handle_allergies_request(self, patient_id: str, patient_data: Dict, message: str) -> str:
        """Handle allergies information requests."""
        allergies = get_patient_allergies(patient_id)
        
        if not allergies:
            return "Your records show no known allergies on file. If you have allergies, please contact our office immediately to update your records for your safety."
        
        response = "🚨 **Your Known Allergies:**\n\n"
        
        for allergy in allergies:
            response += f"• **{allergy}**\n"
        
        response += "\n⚠️ **Critical Safety Information:**\n"
        response += "• Always inform healthcare providers about your allergies\n"
        response += "• Carry allergy information with you\n"
        response += "• Consider wearing a medical alert bracelet\n"
        response += "• Know the signs of allergic reactions\n"
        response += "• Have emergency medications available if prescribed\n\n"
        response += "🆘 **Emergency:** If experiencing severe allergic reaction, call 911 immediately."
        
        return response
    
    def _handle_test_results_request(self, patient_id: str, patient_data: Dict, message: str) -> str:
        """Handle test results requests."""
        # In a real system, this would fetch actual test results
        response = "🧪 **Laboratory & Test Results:**\n\n"
        response += "For security and privacy reasons, detailed test results are available through:\n\n"
        response += "🌐 **Patient Portal:** patient.hospital.com\n"
        response += "📱 **MyChart App:** Download from app store\n"
        response += "📞 **Call Office:** (555) 123-4567\n\n"
        response += "**Recent Tests:** (Summary only)\n"
        response += "• Blood work: Completed last month - Normal ranges\n"
        response += "• Annual physical: Completed - Results discussed with provider\n\n"
        response += "💡 **Note:** Detailed results and interpretations should be discussed with your healthcare provider."
        
        return response
    
    def _handle_summary_request(self, patient_id: str, patient_data: Dict) -> str:
        """Handle comprehensive records summary requests."""
        medical_history = get_patient_medical_history(patient_id)
        medications = get_patient_medications(patient_id)
        allergies = get_patient_allergies(patient_id)
        
        response = f"📊 **Medical Records Summary for {patient_data.get('name', 'Patient')}**\n\n"
        
        # Basic information
        response += "👤 **Patient Information:**\n"
        response += f"• Name: {patient_data.get('name', 'Not specified')}\n"
        response += f"• Age: {patient_data.get('age', 'Not specified')}\n"
        response += f"• Gender: {patient_data.get('gender', 'Not specified')}\n\n"
        
        # Medical history
        response += "📋 **Medical History:**\n"
        if medical_history:
            for condition in medical_history:
                response += f"• {condition.get('condition')} ({condition.get('diagnosed', 'Date unknown')})\n"
        else:
            response += "• No significant medical history on file\n"
        
        response += "\n💊 **Current Medications:**\n"
        if medications:
            for med in medications:
                response += f"• {med.get('name')} - {med.get('dosage')} {med.get('frequency')}\n"
        else:
            response += "• No current medications on file\n"
        
        response += "\n🚨 **Known Allergies:**\n"
        if allergies:
            for allergy in allergies:
                response += f"• {allergy}\n"
        else:
            response += "• No known allergies on file\n"
        
        response += "\n⚠️ **Important:** This is a summary for your reference. Always consult your healthcare provider for medical decisions and detailed explanations."
        
        return response
    
    def _handle_update_request(self, patient_id: str, patient_data: Dict, message: str) -> str:
        """Handle requests to update medical records."""
        response = "🔄 **Updating Medical Records**\n\n"
        response += "For security and accuracy, medical record updates require verification. Here's how to update your information:\n\n"
        
        response += "**📞 Call Our Office:**\n"
        response += "• Phone: (555) 123-4567\n"
        response += "• Speak with medical records staff\n"
        response += "• Verification required\n\n"
        
        response += "**🌐 Patient Portal:**\n"
        response += "• Log in to patient.hospital.com\n"
        response += "• Use secure messaging\n"
        response += "• Upload documents if needed\n\n"
        
        response += "**🏥 In-Person Visit:**\n"
        response += "• Visit our office with ID\n"
        response += "• Complete update forms\n"
        response += "• Immediate processing\n\n"
        
        response += "**Common Updates:**\n"
        response += "• New allergies or medications\n"
        response += "• Contact information changes\n"
        response += "• Insurance updates\n"
        response += "• Emergency contact changes\n\n"
        
        response += "⚠️ **Important:** Keeping your medical records current helps ensure safe, effective care."
        
        return response
    
    def _handle_general_records_request(self, patient_id: str, patient_data: Dict, message: str) -> str:
        """Handle general medical records requests."""
        response = "📋 **Medical Records Information**\n\n"
        response += "I can help you access various types of medical information:\n\n"
        
        response += "**Available Information:**\n"
        response += "• 📋 Medical history and diagnoses\n"
        response += "• 💊 Current medications and prescriptions\n"
        response += "• 🚨 Known allergies and reactions\n"
        response += "• 🧪 Lab and test results (via portal)\n"
        response += "• 📊 Complete medical records summary\n\n"
        
        response += "**How to Access:**\n"
        response += "• Ask me specific questions about your records\n"
        response += "• Use our patient portal: patient.hospital.com\n"
        response += "• Call our office: (555) 123-4567\n\n"
        
        response += "**Example Requests:**\n"
        response += "• \"Show me my medical history\"\n"
        response += "• \"What medications am I taking?\"\n"
        response += "• \"Do I have any allergies on file?\"\n"
        response += "• \"I need a summary of my records\"\n\n"
        
        response += "🔒 **Privacy:** All medical records access is secure and logged for your protection."
        
        return response

# Initialize medical records agent
records_agent = MedicalRecordsAgent()

def handle_records(state: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to handle medical records requests."""
    return records_agent.handle_records(state)
