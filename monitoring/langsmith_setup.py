"""
LangSmith monitoring and tracing setup for the Medical AI Agent.
"""

import os
from typing import Optional
from langsmith import Client, traceable
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.base import BaseCallbackHandler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalAICallbackHandler(BaseCallbackHandler):
    """Custom callback handler for Medical AI specific monitoring."""
    
    def __init__(self):
        super().__init__()
        self.session_id = None
        
    def on_chain_start(self, serialized, inputs, **kwargs):
        """Log when a chain starts."""
        logger.info(f"Chain started: {serialized.get('name', 'Unknown')}")
        
    def on_chain_end(self, outputs, **kwargs):
        """Log when a chain ends."""
        logger.info(f"Chain completed successfully")
        
    def on_chain_error(self, error, **kwargs):
        """Log when a chain encounters an error."""
        logger.error(f"Chain error: {error}")

def get_langsmith_client() -> Optional[Client]:
    """Initialize and return LangSmith client if API key is available."""
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not api_key or api_key == "your_key_here":
        logger.warning("LangSmith API key not configured. Monitoring disabled.")
        return None
    
    try:
        client = Client(api_key=api_key)
        logger.info("LangSmith client initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize LangSmith client: {e}")
        return None

def get_callback_manager() -> CallbackManager:
    """Get callback manager with minimal handlers to avoid conflicts."""
    handlers = [MedicalAICallbackHandler()]
    
    # Only add LangSmith tracing if properly configured
    api_key = os.getenv("LANGSMITH_API_KEY")
    if api_key and api_key != "your_key_here":
        # Enable LangSmith tracing via environment variables only
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        logger.info("LangSmith tracing enabled via environment variables")
    else:
        # Disable tracing if no API key
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        logger.info("LangSmith tracing disabled - no API key")
    
    return CallbackManager(handlers)

@traceable(name="medical_ai_trace")
def trace_medical_interaction(patient_input: str, agent_response: str, intent: str = None):
    """Trace medical interactions for monitoring and analysis."""
    trace_data = {
        "patient_input": patient_input,
        "agent_response": agent_response,
        "intent": intent,
        "timestamp": os.environ.get("TIMESTAMP", ""),
    }
    
    logger.info(f"Traced interaction - Intent: {intent}")
    return trace_data

def setup_monitoring():
    """Setup monitoring configuration."""
    # Load environment variables if not already loaded
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Check for LangSmith API key
    api_key = os.getenv("LANGSMITH_API_KEY")
    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
    
    if api_key and api_key != "your_key_here":
        # Set environment variables for LangSmith tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = langchain_api_key or api_key
        
        project_name = os.getenv("LANGCHAIN_PROJECT", "medical-ai-agent")
        os.environ["LANGCHAIN_PROJECT"] = project_name
        
        logger.info(f"LangSmith tracing enabled. Project: {project_name}")
    else:
        os.environ["LANGCHAIN_TRACING_V2"] = "false"
        logger.warning("LangSmith tracing disabled - no API key configured")
    
    return get_callback_manager()

# Initialize monitoring on import
callback_manager = setup_monitoring()
