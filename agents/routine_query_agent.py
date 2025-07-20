"""
Routine Query Agent for the Medical AI System.
Handles general questions, FAQs, and routine medical information.
"""

import os
from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
from utils.fhir_utils import fhir_manager
import logging

logger = logging.getLogger(__name__)

class RoutineQueryAgent:
    """Handles routine questions, FAQs, and general medical information."""
    
    def __init__(self):
        self.llm = ChatGroq(
            temperature=0.3,  # Slightly higher temperature for more natural responses
            model="llama-3.1-8b-instant",
            api_key=os.getenv("GROQ_API_KEY")
        )
        
        self.routine_prompt = PromptTemplate(
            input_variables=["question", "relevant_faqs", "context"],
            template="""
You are a helpful medical office assistant AI. Answer the patient's question using the provided information and your knowledge.

PATIENT QUESTION:
{question}

RELEVANT FAQ INFORMATION:
{relevant_faqs}

ADDITIONAL CONTEXT:
{context}

GUIDELINES:
1. Be helpful, professional, and empathetic
2. Use the FAQ information when relevant
3. For medical advice: Always recommend consulting with healthcare providers
4. For office procedures: Provide clear, specific information
5. If unsure: Direct to call the office or speak with medical staff
6. Keep responses concise but complete
7. Use a warm, caring tone appropriate for healthcare

IMPORTANT DISCLAIMERS:
- You cannot provide specific medical diagnoses or treatment recommendations
- Always recommend consulting healthcare providers for medical concerns
- For urgent matters, direct patients to appropriate care levels

Provide a helpful, accurate response to the patient's question.
"""
        )
        
        # Common medical topics and responses
        self.topic_responses = {
            "office_hours": "Our office hours are:\n• Monday-Friday: 8:00 AM - 6:00 PM\n• Saturday: 9:00 AM - 2:00 PM\n• Sunday: Closed\n• Holidays: Closed",
            "insurance": "We accept most major insurance plans including Blue Cross Blue Shield, Aetna, Cigna, UnitedHealthcare, and Medicare. Please contact our office to verify your specific plan coverage.",
            "prescription_refills": "For prescription refills, you can:\n• Use our patient portal online\n• Call our office during business hours\n• Contact your pharmacy directly\n\nPlease allow 2-3 business days for processing.",
            "lab_results": "Lab results are typically available within 2-3 business days. You can check your results through:\n• Our patient portal\n• Calling our office\n• MyChart app if enrolled",
            "preparation": "For your appointment, please bring:\n• Valid photo ID\n• Insurance card\n• List of current medications\n• Any relevant medical records\n• Arrive 15 minutes early for check-in"
        }
    
    def handle_routine(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Handle routine queries and general questions."""
        message = state.get("message", "")
        context = state.get("context", "")
        
        logger.info("Processing routine query")
        
        try:
            # Search for relevant FAQs
            relevant_faqs = self._find_relevant_faqs(message)
            
            # Check for common topics
            topic_response = self._check_common_topics(message)
            
            if topic_response:
                response = topic_response
            else:
                # Generate AI response using FAQs and context
                response = self._generate_routine_response(message, relevant_faqs, context)
            
            # Add helpful follow-up suggestions
            response = self._add_followup_suggestions(response, message)
            
            return {
                **state,
                "response": response,
                "query_type": "routine",
                "faqs_used": len(relevant_faqs),
                "next_action": "routine_complete"
            }
            
        except Exception as e:
            logger.error(f"Routine query handling failed: {e}")
            return {
                **state,
                "response": self._get_fallback_response(),
                "query_type": "routine_error",
                "next_action": "routine_complete"
            }
    
    def _find_relevant_faqs(self, question: str) -> List[Dict]:
        """Find FAQs relevant to the question."""
        try:
            # Search FAQs using keyword matching
            relevant_faqs = fhir_manager.search_faqs(question)
            
            # If no direct matches, try individual words
            if not relevant_faqs:
                words = question.lower().split()
                for word in words:
                    if len(word) > 3:  # Skip short words
                        faqs = fhir_manager.search_faqs(word)
                        relevant_faqs.extend(faqs)
                        if len(relevant_faqs) >= 3:  # Limit to avoid too many results
                            break
            
            return relevant_faqs[:3]  # Return top 3 relevant FAQs
            
        except Exception as e:
            logger.error(f"FAQ search failed: {e}")
            return []
    
    def _check_common_topics(self, message: str) -> str:
        """Check if the message relates to common topics with predefined responses."""
        message_lower = message.lower()
        
        # Office hours
        if any(word in message_lower for word in ["hours", "open", "closed", "time"]):
            return self.topic_responses["office_hours"]
        
        # Insurance
        elif any(word in message_lower for word in ["insurance", "coverage", "plan", "billing"]):
            return self.topic_responses["insurance"]
        
        # Prescription refills
        elif any(word in message_lower for word in ["prescription", "refill", "medication", "pills"]):
            return self.topic_responses["prescription_refills"]
        
        # Lab results
        elif any(word in message_lower for word in ["lab", "test", "results", "blood work"]):
            return self.topic_responses["lab_results"]
        
        # Appointment preparation
        elif any(word in message_lower for word in ["bring", "prepare", "preparation", "what to bring"]):
            return self.topic_responses["preparation"]
        
        return None
    
    def _generate_routine_response(self, question: str, relevant_faqs: List[Dict], context: str) -> str:
        """Generate AI response for routine queries."""
        try:
            # Format FAQs for the prompt
            faqs_text = ""
            if relevant_faqs:
                for faq in relevant_faqs:
                    faqs_text += f"Q: {faq.get('question', '')}\n"
                    faqs_text += f"A: {faq.get('answer', '')}\n\n"
            else:
                faqs_text = "No specific FAQ information available for this question."
            
            prompt = self.routine_prompt.format(
                question=question,
                relevant_faqs=faqs_text,
                context=context
            )
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            logger.error(f"Failed to generate routine response: {e}")
            return self._get_fallback_response()
    
    def _add_followup_suggestions(self, response: str, original_question: str) -> str:
        """Add helpful follow-up suggestions to the response."""
        question_lower = original_question.lower()
        
        # Add relevant follow-up suggestions based on the question type
        followup = "\n\n"
        
        if any(word in question_lower for word in ["appointment", "schedule", "book"]):
            followup += "💡 **Need help with appointments?** I can help you schedule, reschedule, or check your upcoming appointments."
        
        elif any(word in question_lower for word in ["symptom", "pain", "feeling", "sick"]):
            followup += "⚠️ **For medical concerns:** Please consult with our healthcare providers. If urgent, don't hesitate to call or visit."
        
        elif any(word in question_lower for word in ["billing", "payment", "cost"]):
            followup += "💰 **Billing questions?** Our billing department is available at (555) 123-4568 or billing@hospital.com."
        
        elif any(word in question_lower for word in ["portal", "online", "website"]):
            followup += "🌐 **Online services:** Visit our patient portal at patient.hospital.com to access your records, schedule appointments, and more."
        
        else:
            followup += "❓ **Still have questions?** Feel free to ask me anything else, or call our office at (555) 123-4567."
        
        # Always add contact information
        followup += "\n\n📞 **Contact Us:**\n"
        followup += "• Phone: (555) 123-4567\n"
        followup += "• Emergency: 911\n"
        followup += "• Online: patient.hospital.com"
        
        return response + followup
    
    def _get_fallback_response(self) -> str:
        """Get fallback response when other methods fail."""
        return """I apologize, but I'm having trouble accessing our information system right now. 

For immediate assistance, please:

📞 **Call our office:** (555) 123-4567
🕐 **Office Hours:** Monday-Friday 8 AM - 6 PM, Saturday 9 AM - 2 PM
🌐 **Online Portal:** patient.hospital.com
📧 **Email:** info@hospital.com

**Common Information:**
• Office hours: Monday-Friday 8 AM - 6 PM, Saturday 9 AM - 2 PM
• We accept most major insurance plans
• Prescription refills: Allow 2-3 business days
• Lab results: Available in 2-3 business days
• For appointments: Call or use our online portal

**Emergency:** If this is urgent, please call 911 or visit the emergency room.

Is there anything specific I can help you with once our system is back online?"""

    def get_general_health_info(self, topic: str) -> str:
        """Provide general health information on common topics."""
        health_info = {
            "hydration": "Staying hydrated is important for overall health. Aim for 8 glasses of water daily, more if you're active or in hot weather. Signs of good hydration include pale yellow urine and feeling energetic.",
            
            "exercise": "Regular exercise is beneficial for physical and mental health. Aim for at least 150 minutes of moderate exercise weekly. Always consult your doctor before starting a new exercise program.",
            
            "sleep": "Quality sleep is essential for health. Most adults need 7-9 hours nightly. Good sleep hygiene includes consistent bedtimes, avoiding screens before bed, and creating a comfortable sleep environment.",
            
            "nutrition": "A balanced diet includes fruits, vegetables, lean proteins, and whole grains. Limit processed foods, sugar, and excessive sodium. Consult our nutritionist for personalized dietary advice.",
            
            "stress": "Managing stress is important for overall wellness. Techniques include deep breathing, meditation, regular exercise, and talking to friends or professionals. Don't hesitate to seek support when needed."
        }
        
        return health_info.get(topic.lower(), "For specific health information, please consult with our healthcare providers who can give you personalized advice based on your individual health needs.")

# Initialize routine query agent
routine_agent = RoutineQueryAgent()

def handle_routine(state: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to handle routine queries."""
    return routine_agent.handle_routine(state)
