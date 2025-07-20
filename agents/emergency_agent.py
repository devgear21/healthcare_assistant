"""
Emergency Agent for the Medical AI System.
Handles urgent medical situations and emergency escalation.
"""

import os
from typing import Dict, Any
from datetime import datetime
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from utils.alerting import send_emergency_alert, alert_manager
from utils.fhir_utils import get_patient_info
import logging

logger = logging.getLogger(__name__)

class EmergencyAgent:
    """Handles emergency medical situations and escalation."""
    
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0,
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.emergency_prompt = PromptTemplate(
            input_variables=["symptoms", "patient_info", "urgency"],
            template="""
You are an emergency medical AI assistant. A patient is reporting urgent symptoms.

PATIENT INFORMATION:
{patient_info}

REPORTED SYMPTOMS:
{symptoms}

URGENCY LEVEL: {urgency}/10

YOUR RESPONSE SHOULD:
1. Acknowledge the seriousness
2. Provide immediate safety advice
3. Recommend next steps (call 911, go to ER, etc.)
4. If urgency >= 8, strongly recommend emergency services
5. Be calm but urgent in tone

IMPORTANT:
- You are NOT replacing medical professionals
- Always recommend seeking immediate professional help for serious symptoms
- Provide basic first aid advice when appropriate
- Be clear about limitations

Respond with empathy and urgency appropriate to the situation.
"""
        )
        
        # Emergency protocols
        self.emergency_protocols = {
            "chest_pain": {
                "advice": "Sit down, stay calm, chew aspirin if not allergic, call 911 immediately",
                "urgency": 10,
                "call_911": True
            },
            "breathing_difficulty": {
                "advice": "Sit upright, try to stay calm, use rescue inhaler if available, call 911",
                "urgency": 9,
                "call_911": True
            },
            "severe_bleeding": {
                "advice": "Apply direct pressure to wound, elevate if possible, call 911",
                "urgency": 9,
                "call_911": True
            },
            "unconscious": {
                "advice": "Check breathing, place in recovery position if breathing, call 911 immediately",
                "urgency": 10,
                "call_911": True
            },
            "allergic_reaction": {
                "advice": "Use EpiPen if available, call 911, avoid allergen",
                "urgency": 8,
                "call_911": True
            }
        }
    
    def handle_emergency(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency situations."""
        message = state.get("message", "")
        urgency = state.get("urgency", 5)
        patient_id = state.get("patient_id", "unknown")
        
        logger.critical(f"Emergency alert triggered - Urgency: {urgency}/10")
        
        try:
            # Get patient information
            patient_info = get_patient_info(patient_id) if patient_id != "unknown" else None
            patient_summary = self._format_patient_info(patient_info) if patient_info else "Patient information not available"
            
            # Determine emergency type and protocol
            emergency_type = self._identify_emergency_type(message)
            protocol = self.emergency_protocols.get(emergency_type, {})
            
            # Generate AI response
            ai_response = self._generate_emergency_response(message, patient_summary, urgency)
            
            # Send emergency alerts
            alert_result = self._send_emergency_alerts(message, patient_summary, urgency, patient_id)
            
            # Prepare response
            response = self._build_emergency_response(ai_response, protocol, urgency, alert_result)
            
            logger.info(f"Emergency response generated for urgency level {urgency}")
            
            return {
                **state,
                "response": response,
                "emergency_type": emergency_type,
                "alert_sent": alert_result.get("alert_sent", False),
                "alert_id": alert_result.get("alert_id"),
                "next_action": "emergency_response_complete"
            }
            
        except Exception as e:
            logger.error(f"Emergency handling failed: {e}")
            return self._fallback_emergency_response(state)
    
    def _identify_emergency_type(self, message: str) -> str:
        """Identify the type of emergency from the message."""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["chest pain", "heart attack", "heart"]):
            return "chest_pain"
        elif any(word in message_lower for word in ["can't breathe", "shortness of breath", "breathing", "breathe"]):
            return "breathing_difficulty"
        elif any(word in message_lower for word in ["bleeding", "blood", "cut", "wound"]):
            return "severe_bleeding"
        elif any(word in message_lower for word in ["unconscious", "fainted", "passed out"]):
            return "unconscious"
        elif any(word in message_lower for word in ["allergic", "allergy", "swelling", "hives"]):
            return "allergic_reaction"
        else:
            return "general_emergency"
    
    def _generate_emergency_response(self, symptoms: str, patient_info: str, urgency: int) -> str:
        """Generate AI response for emergency situation."""
        try:
            prompt = self.emergency_prompt.format(
                symptoms=symptoms,
                patient_info=patient_info,
                urgency=urgency
            )
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to generate emergency response: {e}")
            return self._get_default_emergency_response(urgency)
    
    def _send_emergency_alerts(self, message: str, patient_info: str, urgency: int, patient_id: str) -> Dict:
        """Send emergency alerts to appropriate personnel."""
        try:
            alert_result = send_emergency_alert(
                patient_info=f"Patient ID: {patient_id}\n{patient_info}",
                symptoms=message,
                urgency_level=urgency
            )
            
            logger.critical(f"Emergency alert sent: {alert_result.get('alert_id')}")
            return alert_result
            
        except Exception as e:
            logger.error(f"Failed to send emergency alert: {e}")
            return {"alert_sent": False, "error": str(e)}
    
    def _build_emergency_response(self, ai_response: str, protocol: Dict, urgency: int, alert_result: Dict) -> str:
        """Build the complete emergency response message."""
        response_parts = []
        
        # Urgency indicator
        if urgency >= 9:
            response_parts.append("🚨 **IMMEDIATE EMERGENCY** 🚨")
        elif urgency >= 7:
            response_parts.append("⚠️ **URGENT MEDICAL SITUATION** ⚠️")
        else:
            response_parts.append("🏥 **Medical Attention Needed** 🏥")
        
        # AI response
        response_parts.append(ai_response)
        
        # Protocol advice
        if protocol.get("advice"):
            response_parts.append(f"\n**Immediate Actions:**\n{protocol['advice']}")
        
        # Call 911 recommendation
        if urgency >= 8 or protocol.get("call_911"):
            response_parts.append("\n🚨 **CALL 911 IMMEDIATELY** 🚨")
        
        # Alert status
        if alert_result.get("alert_sent"):
            response_parts.append(f"\n✅ Emergency services have been notified (Alert ID: {alert_result.get('alert_id', 'N/A')})")
        else:
            response_parts.append("\n📞 Please contact emergency services directly at 911")
        
        # Emergency contacts
        response_parts.append("\n**Emergency Contacts:**")
        response_parts.append("• Emergency Services: 911")
        response_parts.append("• Poison Control: 1-800-222-1222")
        response_parts.append("• Crisis Text Line: Text HOME to 741741")
        
        return "\n".join(response_parts)
    
    def _format_patient_info(self, patient_info: Dict) -> str:
        """Format patient information for emergency context."""
        if not patient_info:
            return "Patient information not available"
        
        info_parts = [
            f"Name: {patient_info.get('name', 'Unknown')}",
            f"Age: {patient_info.get('age', 'Unknown')}",
            f"Gender: {patient_info.get('gender', 'Unknown')}"
        ]
        
        # Add allergies if present
        allergies = patient_info.get('allergies', [])
        if allergies:
            info_parts.append(f"Allergies: {', '.join(allergies)}")
        
        # Add current medications
        medications = patient_info.get('medications', [])
        if medications:
            med_names = [med.get('name', 'Unknown') for med in medications[:3]]  # Top 3
            info_parts.append(f"Current Medications: {', '.join(med_names)}")
        
        # Add emergency contact
        emergency_contact = patient_info.get('emergency_contact')
        if emergency_contact:
            info_parts.append(f"Emergency Contact: {emergency_contact.get('name')} ({emergency_contact.get('phone')})")
        
        return "\n".join(info_parts)
    
    def _get_default_emergency_response(self, urgency: int) -> str:
        """Get default emergency response when AI generation fails."""
        if urgency >= 8:
            return """This appears to be a serious medical emergency. Please take the following immediate actions:

1. **Call 911 immediately** or go to the nearest emergency room
2. Stay calm and follow dispatcher instructions
3. If possible, have someone stay with you
4. Do not drive yourself if experiencing severe symptoms

Emergency services have been notified. This is not a substitute for professional medical care."""
        else:
            return """This may require urgent medical attention. Please consider:

1. Calling your doctor immediately
2. Going to urgent care or emergency room
3. Calling 911 if symptoms worsen
4. Having someone available to assist you

Please seek professional medical evaluation as soon as possible."""
    
    def _fallback_emergency_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback response when emergency handling fails."""
        urgency = state.get("urgency", 10)  # Default to high urgency for safety
        
        response = f"""🚨 EMERGENCY PROTOCOL ACTIVATED 🚨

I understand this is an urgent situation. Due to a system issue, I cannot provide detailed guidance right now.

**IMMEDIATE ACTIONS:**
• Call 911 immediately: **911**
• Go to the nearest emergency room
• Contact your doctor if possible

**This is an emergency situation requiring immediate professional medical attention.**

Alert ID: FALLBACK_{int(datetime.now().timestamp())}
"""
        
        return {
            **state,
            "response": response,
            "emergency_type": "system_fallback",
            "alert_sent": False,
            "next_action": "emergency_response_complete"
        }

# Initialize emergency agent
emergency_agent = EmergencyAgent()

def handle_emergency(state: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to handle emergency situations."""
    return emergency_agent.handle_emergency(state)
