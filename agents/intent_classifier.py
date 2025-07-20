"""
Intent Classification Agent for the Medical AI System.
Routes patient messages to appropriate specialized agents.
"""

import os
from typing import Dict, Any
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.schema import HumanMessage
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class IntentClassifier:
    """Classifies patient intents and routes to appropriate agents."""
    
    def __init__(self):
        # Ensure API key is available
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            # Try to load from .env file
            try:
                from dotenv import load_dotenv
                load_dotenv()
                api_key = os.getenv("GROQ_API_KEY")
            except ImportError:
                pass
        
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
            
        self.llm = ChatGroq(
            temperature=0,
            model="llama-3.1-8b-instant",
            api_key=api_key
        )
        
        self.classification_prompt = PromptTemplate(
            input_variables=["message", "context"],
            template="""
You are a medical AI intent classifier. Analyze the patient's message and classify it into one of these categories:

CATEGORIES:
1. "emergency" - Urgent medical situations requiring immediate attention (chest pain, difficulty breathing, severe symptoms)
2. "appointment" - Scheduling, rescheduling, or canceling appointments
3. "medical_records" - Requesting medical history, test results, medications, or updating personal information
4. "routine" - General questions, FAQs, office hours, insurance, prescriptions, general health advice

EMERGENCY KEYWORDS: chest pain, heart attack, shortness of breath, difficulty breathing, severe headache, stroke, unconscious, bleeding heavily, severe allergic reaction, suicide, overdose, can't breathe, severe pain, emergency

Patient Message: {message}

Context: {context}

Classify this message and provide:
1. Primary intent (emergency/appointment/medical_records/routine)
2. Confidence level (1-10)
3. Brief reasoning
4. If emergency, specify urgency level (1-10)

Format your response as:
INTENT: [category]
CONFIDENCE: [1-10]
URGENCY: [1-10 if emergency, else 0]
REASONING: [brief explanation]
"""
        )
    
    def classify_intent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Classify the intent of a patient message."""
        message = state.get("message", "")
        context = state.get("context", "")
        
        if not message:
            return {
                **state,
                "intent": "routine",
                "confidence": 10,
                "urgency": 0,
                "reasoning": "Empty message defaulted to routine"
            }
        
        try:
            # Quick emergency detection
            emergency_keywords = [
                "chest pain", "heart attack", "shortness of breath", "difficulty breathing",
                "severe headache", "stroke", "unconscious", "bleeding heavily",
                "severe allergic reaction", "suicide", "overdose", "can't breathe",
                "severe pain", "emergency", "911", "ambulance"
            ]
            
            message_lower = message.lower()
            has_emergency_keyword = any(keyword in message_lower for keyword in emergency_keywords)
            
            if has_emergency_keyword:
                urgency = self._calculate_urgency(message_lower)
                return {
                    **state,
                    "intent": "emergency",
                    "confidence": 9,
                    "urgency": urgency,
                    "reasoning": "Emergency keywords detected"
                }
            
            # Use LLM for more nuanced classification
            prompt = self.classification_prompt.format(message=message, context=context)
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse LLM response
            result = self._parse_classification_response(response.content)
            
            logger.info(f"Classified intent: {result['intent']} (confidence: {result['confidence']})")
            
            return {
                **state,
                **result
            }
            
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Fallback to rule-based classification
            return self._fallback_classification(state)
    
    def _calculate_urgency(self, message: str) -> int:
        """Calculate urgency level based on message content."""
        high_urgency_keywords = ["chest pain", "heart attack", "can't breathe", "unconscious", "suicide"]
        medium_urgency_keywords = ["severe pain", "bleeding", "allergic reaction", "difficulty breathing"]
        
        if any(keyword in message for keyword in high_urgency_keywords):
            return 10
        elif any(keyword in message for keyword in medium_urgency_keywords):
            return 8
        else:
            return 6  # Default emergency urgency
    
    def _parse_classification_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM classification response."""
        result = {
            "intent": "routine",
            "confidence": 5,
            "urgency": 0,
            "reasoning": "Default classification"
        }
        
        try:
            lines = response.strip().split('\n')
            for line in lines:
                if line.startswith("INTENT:"):
                    result["intent"] = line.split(":", 1)[1].strip().lower()
                elif line.startswith("CONFIDENCE:"):
                    result["confidence"] = int(line.split(":", 1)[1].strip())
                elif line.startswith("URGENCY:"):
                    result["urgency"] = int(line.split(":", 1)[1].strip())
                elif line.startswith("REASONING:"):
                    result["reasoning"] = line.split(":", 1)[1].strip()
        except Exception as e:
            logger.error(f"Failed to parse classification response: {e}")
        
        return result
    
    def _fallback_classification(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback rule-based classification when LLM fails."""
        message = state.get("message", "").lower()
        
        # Emergency keywords
        if any(word in message for word in ["emergency", "urgent", "pain", "help"]):
            intent = "emergency"
            urgency = 7
        # Appointment keywords
        elif any(word in message for word in ["appointment", "schedule", "book", "cancel", "reschedule"]):
            intent = "appointment"
            urgency = 0
        # Medical records keywords
        elif any(word in message for word in ["records", "history", "medication", "prescription", "test results"]):
            intent = "medical_records"
            urgency = 0
        else:
            intent = "routine"
            urgency = 0
        
        return {
            **state,
            "intent": intent,
            "confidence": 6,
            "urgency": urgency,
            "reasoning": "Fallback rule-based classification"
        }

# Initialize classifier lazily
intent_classifier = None

def get_intent_classifier():
    """Get the intent classifier instance, creating it if needed."""
    global intent_classifier
    if intent_classifier is None:
        intent_classifier = IntentClassifier()
    return intent_classifier

def classify_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to classify intent from state."""
    classifier = get_intent_classifier()
    return classifier.classify_intent(state)
