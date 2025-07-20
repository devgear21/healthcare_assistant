"""
Alerting utilities for emergency situations in the Medical AI Agent.
"""

import os
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)

class AlertingSystem:
    """Manages emergency alerts and notifications."""
    
    def __init__(self):
        self.email_enabled = os.getenv("EMAIL_ALERTS_ENABLED", "false").lower() == "true"
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("ALERT_EMAIL_USER", "")
        self.email_password = os.getenv("ALERT_EMAIL_PASSWORD", "")
        self.alert_recipients = os.getenv("ALERT_RECIPIENTS", "").split(",")
        
        # Emergency contacts
        self.emergency_contacts = [
            {"name": "Emergency Response Team", "phone": "911", "email": "emergency@hospital.com"},
            {"name": "On-Call Doctor", "phone": "+1-555-DOCTOR", "email": "oncall@hospital.com"},
            {"name": "Nursing Station", "phone": "+1-555-NURSE", "email": "nursing@hospital.com"}
        ]
    
    def send_email_alert(self, subject: str, message: str, priority: str = "HIGH") -> bool:
        """Send email alert to configured recipients."""
        if not self.email_enabled or not self.email_user:
            logger.warning("Email alerts not configured, logging alert instead")
            self._log_alert(subject, message, priority)
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = ", ".join(self.alert_recipients)
            msg['Subject'] = f"[{priority}] Medical AI Alert: {subject}"
            
            body = f"""
MEDICAL AI EMERGENCY ALERT

Priority: {priority}
Timestamp: {datetime.now().isoformat()}

Alert: {subject}

Details:
{message}

This is an automated alert from the Medical AI System.
Please respond immediately for HIGH priority alerts.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, self.alert_recipients, text)
            server.quit()
            
            logger.info(f"Email alert sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            self._log_alert(subject, message, priority)
            return False
    
    def send_emergency_alert(self, patient_info: str, symptoms: str, urgency_level: int = 10) -> Dict:
        """Send emergency alert with patient information."""
        timestamp = datetime.now().isoformat()
        
        alert_data = {
            "timestamp": timestamp,
            "patient_info": patient_info,
            "symptoms": symptoms,
            "urgency_level": urgency_level,
            "alert_id": f"EMRG_{int(datetime.now().timestamp())}"
        }
        
        subject = f"EMERGENCY - Patient Alert (Urgency: {urgency_level}/10)"
        message = f"""
EMERGENCY MEDICAL ALERT

Patient: {patient_info}
Symptoms: {symptoms}
Urgency Level: {urgency_level}/10
Alert ID: {alert_data['alert_id']}

IMMEDIATE RESPONSE REQUIRED

Recommended Actions:
- Contact patient immediately
- Dispatch emergency services if needed
- Update patient status in system
- Document response actions
        """
        
        # Send email alert
        email_sent = self.send_email_alert(subject, message, "EMERGENCY")
        
        # Log to alert history
        self._save_alert_history(alert_data)
        
        # In a real system, you would also:
        # - Send SMS alerts
        # - Trigger pager notifications
        # - Update hospital systems
        # - Create incident tickets
        
        logger.critical(f"Emergency alert triggered: {alert_data['alert_id']}")
        
        return {
            "alert_sent": True,
            "alert_id": alert_data['alert_id'],
            "email_sent": email_sent,
            "timestamp": timestamp,
            "contacts_notified": self.emergency_contacts
        }
    
    def send_routine_alert(self, message: str, category: str = "GENERAL") -> bool:
        """Send routine alert for non-emergency situations."""
        subject = f"Medical AI Notification - {category}"
        return self.send_email_alert(subject, message, "MEDIUM")
    
    def _log_alert(self, subject: str, message: str, priority: str):
        """Log alert when email sending fails."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "subject": subject,
            "message": message,
            "priority": priority,
            "method": "LOG_ONLY"
        }
        
        logger.warning(f"Alert logged (email failed): {json.dumps(log_entry)}")
    
    def _save_alert_history(self, alert_data: Dict):
        """Save alert to history file."""
        try:
            history_file = "data/alert_history.json"
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            
            # Load existing history
            history = []
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
            
            # Add new alert
            history.append(alert_data)
            
            # Keep only last 100 alerts
            history = history[-100:]
            
            # Save updated history
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
                
            logger.info(f"Alert saved to history: {alert_data['alert_id']}")
            
        except Exception as e:
            logger.error(f"Failed to save alert history: {e}")
    
    def get_alert_history(self, limit: int = 10) -> List[Dict]:
        """Get recent alert history."""
        try:
            history_file = "data/alert_history.json"
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
                return history[-limit:]
            return []
        except Exception as e:
            logger.error(f"Failed to load alert history: {e}")
            return []

# Global alert manager instance
alert_manager = AlertingSystem()

def send_alert(message: str, alert_type: str = "emergency", **kwargs) -> Dict:
    """Send an alert using the global alert manager."""
    if alert_type.lower() == "emergency":
        patient_info = kwargs.get("patient_info", "Unknown Patient")
        urgency = kwargs.get("urgency_level", 10)
        return alert_manager.send_emergency_alert(patient_info, message, urgency)
    else:
        category = kwargs.get("category", "GENERAL")
        success = alert_manager.send_routine_alert(message, category)
        return {"alert_sent": success, "type": "routine"}

def send_emergency_alert(patient_info: str, symptoms: str, urgency_level: int = 10) -> Dict:
    """Quick function to send emergency alert."""
    return alert_manager.send_emergency_alert(patient_info, symptoms, urgency_level)
