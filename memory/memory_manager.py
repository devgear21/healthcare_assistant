"""
Memory management for the Medical AI Agent using LangChain.
Maintains conversation history and medical context across interactions.
"""

import os
from typing import Dict, List, Any, Optional
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class MemoryManager:
    """Manages conversation memory and medical context for patients."""
    
    def __init__(self, patient_id: str = None):
        self.patient_id = patient_id or "default_patient"
        self.conversation_memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="chat_history"
        )
        self.medical_context = {}
        self.session_start = datetime.now()
        
        # Initialize summary memory for longer conversations
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(temperature=0, model="llama-3.1-8b-instant", api_key=os.getenv("GROQ_API_KEY"))
            self.summary_memory = ConversationSummaryBufferMemory(
                llm=llm,
                max_token_limit=1000,
                return_messages=True
            )
        except Exception as e:
            logger.warning(f"Could not initialize summary memory: {e}")
            self.summary_memory = None
    
    def save_interaction(self, user_input: str, ai_response: str, metadata: Dict = None):
        """Save a user-AI interaction to memory."""
        try:
            # Save to conversation memory
            self.conversation_memory.save_context(
                {"input": user_input}, 
                {"output": ai_response}
            )
            
            # Save to summary memory if available
            if self.summary_memory:
                self.summary_memory.save_context(
                    {"input": user_input}, 
                    {"output": ai_response}
                )
            
            # Store additional metadata
            if metadata:
                self.medical_context.update(metadata)
                
            logger.info(f"Saved interaction for patient {self.patient_id}")
            
        except Exception as e:
            logger.error(f"Failed to save interaction: {e}")
    
    def get_conversation_history(self) -> List[BaseMessage]:
        """Get the conversation history as a list of messages."""
        try:
            return self.conversation_memory.chat_memory.messages
        except Exception as e:
            logger.error(f"Failed to get conversation history: {e}")
            return []
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation if available."""
        if self.summary_memory:
            try:
                return self.summary_memory.predict_new_summary(
                    self.get_conversation_history(), ""
                )
            except Exception as e:
                logger.error(f"Failed to get conversation summary: {e}")
        
        # Fallback: return basic info
        messages = self.get_conversation_history()
        return f"Conversation with {len(messages)} messages since {self.session_start}"
    
    def update_medical_context(self, context_update: Dict):
        """Update medical context information."""
        self.medical_context.update(context_update)
        logger.info(f"Updated medical context for patient {self.patient_id}")
    
    def get_medical_context(self) -> Dict:
        """Get current medical context."""
        return self.medical_context.copy()
    
    def get_relevant_history(self, query: str, max_messages: int = 5) -> List[BaseMessage]:
        """Get relevant conversation history based on query."""
        messages = self.get_conversation_history()
        
        # Simple relevance: return last N messages
        # In a production system, you might use embedding similarity
        return messages[-max_messages:] if messages else []
    
    def clear_memory(self):
        """Clear all memory (use with caution)."""
        self.conversation_memory.clear()
        if self.summary_memory:
            self.summary_memory.clear()
        self.medical_context.clear()
        logger.info(f"Cleared memory for patient {self.patient_id}")
    
    def export_session(self) -> Dict:
        """Export current session data."""
        return {
            "patient_id": self.patient_id,
            "session_start": self.session_start.isoformat(),
            "conversation_history": [
                {
                    "type": type(msg).__name__,
                    "content": msg.content
                } for msg in self.get_conversation_history()
            ],
            "medical_context": self.medical_context,
            "summary": self.get_conversation_summary()
        }
    
    def load_session(self, session_data: Dict):
        """Load session data from export."""
        try:
            self.patient_id = session_data.get("patient_id", self.patient_id)
            self.medical_context = session_data.get("medical_context", {})
            
            # Reconstruct conversation history
            for msg_data in session_data.get("conversation_history", []):
                if msg_data["type"] == "HumanMessage":
                    self.conversation_memory.chat_memory.add_user_message(msg_data["content"])
                elif msg_data["type"] == "AIMessage":
                    self.conversation_memory.chat_memory.add_ai_message(msg_data["content"])
                    
            logger.info(f"Loaded session for patient {self.patient_id}")
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")

# Global memory manager for simple use cases
default_memory = MemoryManager()

def get_memory_manager(patient_id: str = None) -> MemoryManager:
    """Get a memory manager for a specific patient."""
    if patient_id:
        return MemoryManager(patient_id)
    return default_memory
