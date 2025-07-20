"""
Main Medical AI Agent using LangGraph for workflow orchestration.
Coordinates all specialized agents and manages conversation flow.
"""

import os
from typing import Dict, Any, List, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain.schema import BaseMessage, HumanMessage, AIMessage

# Load environment variables
load_dotenv()

# Define the state schema as a TypedDict
class MedicalAIState(TypedDict):
    messages: List[BaseMessage]
    patient_id: str
    message: str
    intent: str
    confidence: int
    urgency: int
    reasoning: str
    response: str
    context: str
    session_data: dict
    next_action: str
    error: str

from agents.intent_classifier import classify_intent
from agents.scheduler_agent import handle_schedule
from agents.routine_query_agent import handle_routine
from agents.emergency_agent import handle_emergency
from agents.medical_records_agent import handle_records
from memory.memory_manager import get_memory_manager
from monitoring.langsmith_setup import callback_manager, trace_medical_interaction
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MedicalAgentState:
    """State management for the Medical AI Agent."""
    
    def __init__(self):
        self.messages: List[BaseMessage] = []
        self.patient_id: str = ""
        self.message: str = ""
        self.intent: str = ""
        self.confidence: int = 0
        self.urgency: int = 0
        self.reasoning: str = ""
        self.response: str = ""
        self.context: str = ""
        self.session_data: Dict[str, Any] = {}
        self.next_action: str = ""
        self.error: str = ""

class MedicalAIAgent:
    """Main Medical AI Agent class using LangGraph."""
    
    def __init__(self):
        self.graph = self._build_graph()
        self.memory_managers = {}  # Store memory managers per patient
        
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for the medical AI agent."""
        
        # Create the graph with the TypedDict state
        workflow = StateGraph(MedicalAIState)
        
        # Add nodes for each agent
        workflow.add_node("intent_classifier", self._intent_classifier_node)
        workflow.add_node("emergency_agent", self._emergency_agent_node)
        workflow.add_node("scheduler_agent", self._scheduler_agent_node)
        workflow.add_node("routine_agent", self._routine_agent_node)
        workflow.add_node("records_agent", self._records_agent_node)
        workflow.add_node("response_builder", self._response_builder_node)
        workflow.add_node("memory_updater", self._memory_updater_node)
        
        # Set entry point
        workflow.set_entry_point("intent_classifier")
        
        # Add conditional edges based on intent classification
        workflow.add_conditional_edges(
            "intent_classifier",
            self._route_by_intent,
            {
                "emergency": "emergency_agent",
                "appointment": "scheduler_agent",
                "routine": "routine_agent",
                "medical_records": "records_agent",
                "error": "response_builder"
            }
        )
        
        # All agents route to response builder
        workflow.add_edge("emergency_agent", "response_builder")
        workflow.add_edge("scheduler_agent", "response_builder")
        workflow.add_edge("routine_agent", "response_builder")
        workflow.add_edge("records_agent", "response_builder")
        
        # Response builder routes to memory updater
        workflow.add_edge("response_builder", "memory_updater")
        
        # Memory updater ends the workflow
        workflow.add_edge("memory_updater", END)
        
        return workflow.compile()
    
    def _intent_classifier_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for intent classification."""
        try:
            logger.info("Processing intent classification")
            result = classify_intent(state)
            return result
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {**state, "intent": "error", "error": str(e)}
    
    def _emergency_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for emergency handling."""
        try:
            logger.info("Processing emergency request")
            result = handle_emergency(state)
            return result
        except Exception as e:
            logger.error(f"Emergency agent failed: {e}")
            return {**state, "response": "Emergency system error. Please call 911 immediately.", "error": str(e)}
    
    def _scheduler_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for appointment scheduling."""
        try:
            logger.info("Processing scheduling request")
            result = handle_schedule(state)
            return result
        except Exception as e:
            logger.error(f"Scheduler agent failed: {e}")
            return {**state, "response": "I'm having trouble with the scheduling system. Please call (555) 123-4567.", "error": str(e)}
    
    def _routine_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for routine queries."""
        try:
            logger.info("Processing routine query")
            result = handle_routine(state)
            return result
        except Exception as e:
            logger.error(f"Routine agent failed: {e}")
            return {**state, "response": "I'm having trouble processing your request. Please call our office for assistance.", "error": str(e)}
    
    def _records_agent_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for medical records."""
        try:
            logger.info("Processing medical records request")
            result = handle_records(state)
            return result
        except Exception as e:
            logger.error(f"Medical records agent failed: {e}")
            return {**state, "response": "I'm having trouble accessing medical records. Please call our office or use the patient portal.", "error": str(e)}
    
    def _response_builder_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for building final response."""
        try:
            response = state.get("response", "")
            
            if not response:
                response = "I apologize, but I couldn't process your request. Please contact our office at (555) 123-4567 for assistance."
            
            # Add timestamp and session info
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Build final response with metadata
            final_response = response
            
            # Add appropriate closing based on intent
            intent = state.get("intent", "")
            if intent == "emergency":
                final_response += "\n\n⚠️ **Remember:** This AI assistant cannot replace professional medical care. Always consult healthcare providers for medical decisions."
            elif intent == "appointment":
                final_response += "\n\n📅 **Next Steps:** I'll help you with any additional scheduling needs."
            elif intent == "medical_records":
                final_response += "\n\n🔒 **Privacy:** Your medical information is secure and access is logged."
            else:
                final_response += "\n\n💡 **How else can I help?** Feel free to ask about appointments, medical records, or general questions."
            
            return {
                **state,
                "response": final_response,
                "timestamp": timestamp,
                "final_response_built": True
            }
            
        except Exception as e:
            logger.error(f"Response builder failed: {e}")
            return {
                **state,
                "response": "I apologize for the technical difficulty. Please contact our office at (555) 123-4567.",
                "error": str(e)
            }
    
    def _memory_updater_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Node for updating conversation memory."""
        try:
            patient_id = state.get("patient_id", "default_patient")
            message = state.get("message", "")
            response = state.get("response", "")
            intent = state.get("intent", "")
            
            # Get or create memory manager for this patient
            if patient_id not in self.memory_managers:
                self.memory_managers[patient_id] = get_memory_manager(patient_id)
            
            memory_manager = self.memory_managers[patient_id]
            
            # Save the interaction
            metadata = {
                "intent": intent,
                "confidence": state.get("confidence", 0),
                "urgency": state.get("urgency", 0),
                "timestamp": state.get("timestamp", ""),
                "session_id": state.get("session_data", {}).get("session_id", "")
            }
            
            memory_manager.save_interaction(message, response, metadata)
            
            # Trace the interaction for monitoring
            trace_medical_interaction(message, response, intent)
            
            logger.info(f"Updated memory for patient {patient_id}")
            
            return {
                **state,
                "memory_updated": True,
                "conversation_complete": True
            }
            
        except Exception as e:
            logger.error(f"Memory update failed: {e}")
            return {**state, "memory_error": str(e)}
    
    def _route_by_intent(self, state: Dict[str, Any]) -> str:
        """Route to appropriate agent based on classified intent."""
        intent = state.get("intent", "routine")
        
        if intent == "emergency":
            return "emergency"
        elif intent == "appointment":
            return "appointment"
        elif intent == "medical_records":
            return "medical_records"
        elif intent == "routine":
            return "routine"
        else:
            return "error"
    
    def process_message(self, message: str, patient_id: str = None, context: str = "") -> Dict[str, Any]:
        """Process a patient message through the medical AI agent."""
        try:
            # Prepare initial state
            initial_state = {
                "message": message,
                "patient_id": patient_id or "default_patient",
                "context": context,
                "messages": [HumanMessage(content=message)],
                "session_data": {
                    "session_id": f"session_{int(datetime.now().timestamp())}",
                    "start_time": datetime.now().isoformat()
                }
            }
            
            logger.info(f"Processing message for patient {patient_id}: {message[:50]}...")
            
            # Run the graph without problematic callbacks for now
            result = self.graph.invoke(initial_state)
            
            logger.info("Message processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please contact our office at (555) 123-4567 for immediate assistance.",
                "error": str(e),
                "intent": "system_error"
            }
    
    def get_conversation_history(self, patient_id: str) -> List[Dict]:
        """Get conversation history for a patient."""
        if patient_id in self.memory_managers:
            memory_manager = self.memory_managers[patient_id]
            messages = memory_manager.get_conversation_history()
            return [
                {
                    "type": type(msg).__name__,
                    "content": msg.content,
                    "timestamp": getattr(msg, 'timestamp', '')
                }
                for msg in messages
            ]
        return []
    
    def clear_patient_memory(self, patient_id: str):
        """Clear conversation memory for a patient."""
        if patient_id in self.memory_managers:
            self.memory_managers[patient_id].clear_memory()
            logger.info(f"Cleared memory for patient {patient_id}")

# Initialize the medical AI agent
medical_ai_agent = MedicalAIAgent()

def process_patient_message(message: str, patient_id: str = None, context: str = "") -> str:
    """
    Main function to process patient messages.
    
    Args:
        message: The patient's message
        patient_id: Optional patient identifier
        context: Optional additional context
    
    Returns:
        The agent's response
    """
    result = medical_ai_agent.process_message(message, patient_id, context)
    return result.get("response", "I apologize, but I couldn't process your request.")

def get_patient_conversation_history(patient_id: str) -> List[Dict]:
    """Get conversation history for a patient."""
    return medical_ai_agent.get_conversation_history(patient_id)

def clear_patient_conversation(patient_id: str):
    """Clear conversation history for a patient."""
    medical_ai_agent.clear_patient_memory(patient_id)
