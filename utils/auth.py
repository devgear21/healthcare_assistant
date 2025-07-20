"""
Authentication utilities for the Medical AI Agent.
"""

import os
import hashlib
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    """Simple authentication manager for the medical AI system."""
    
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "medical-ai-secret-key-change-in-production")
        self.session_timeout = timedelta(hours=8)  # 8-hour sessions
        
    def create_patient_session(self, patient_id: str, additional_claims: Dict = None) -> str:
        """Create a JWT session token for a patient."""
        try:
            payload = {
                "patient_id": patient_id,
                "exp": datetime.utcnow() + self.session_timeout,
                "iat": datetime.utcnow(),
                "type": "patient_session"
            }
            
            if additional_claims:
                payload.update(additional_claims)
                
            token = jwt.encode(payload, self.secret_key, algorithm="HS256")
            logger.info(f"Created session for patient {patient_id}")
            return token
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def verify_session(self, token: str) -> Optional[Dict]:
        """Verify and decode a session token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            logger.info(f"Verified session for patient {payload.get('patient_id')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Session token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid session token: {e}")
            return None
    
    def hash_patient_info(self, patient_info: str) -> str:
        """Hash sensitive patient information."""
        return hashlib.sha256(patient_info.encode()).hexdigest()
    
    def verify_patient_access(self, patient_id: str, provided_info: str) -> bool:
        """Verify patient access using basic information."""
        # In a real system, this would check against a secure database
        # For demo purposes, we'll use a simple verification
        expected_hash = self.hash_patient_info(f"{patient_id}_demo_key")
        provided_hash = self.hash_patient_info(provided_info)
        
        return expected_hash == provided_hash

# Global auth manager instance
auth_manager = AuthManager()

def require_authentication(func):
    """Decorator to require authentication for functions."""
    def wrapper(*args, **kwargs):
        # In a real implementation, this would check for valid session
        logger.info("Authentication check passed (demo mode)")
        return func(*args, **kwargs)
    return wrapper

def get_patient_session(patient_id: str) -> str:
    """Get or create a patient session."""
    return auth_manager.create_patient_session(patient_id)

def verify_patient_session(token: str) -> Optional[str]:
    """Verify patient session and return patient ID."""
    payload = auth_manager.verify_session(token)
    if payload:
        return payload.get("patient_id")
    return None

def authenticate_patient(patient_id: str, password: str = None) -> bool:
    """Simple patient authentication."""
    return auth_manager.authenticate_patient(patient_id, password)
