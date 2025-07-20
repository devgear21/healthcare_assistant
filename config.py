"""
Configuration settings for the Medical AI Agent.
Centralized configuration management for all components.
"""

import os
from dataclasses import dataclass
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    fhir_data_file: str = "data/sample_fhir_records.json"
    alert_history_file: str = "data/alert_history.json"
    backup_enabled: bool = True
    backup_interval_hours: int = 24

@dataclass
class AIConfig:
    """AI model configuration settings."""
    default_model: str = "llama-3.1-70b-versatile"
    temperature: float = 0.0
    max_tokens: int = 1000
    fallback_model: str = "llama-3.1-8b-instant"
    api_timeout: int = 30

@dataclass
class EmergencyConfig:
    """Emergency detection and alerting configuration."""
    urgency_threshold: int = 7  # Minimum urgency level to trigger alerts
    auto_alert_enabled: bool = True
    emergency_keywords: List[str] = None
    max_response_time: int = 5  # seconds
    
    def __post_init__(self):
        if self.emergency_keywords is None:
            self.emergency_keywords = [
                "chest pain", "heart attack", "shortness of breath", 
                "difficulty breathing", "severe headache", "stroke",
                "unconscious", "bleeding heavily", "severe allergic reaction",
                "suicide", "overdose", "can't breathe", "severe pain", "emergency"
            ]

@dataclass
class SecurityConfig:
    """Security and authentication configuration."""
    session_timeout_hours: int = 8
    max_login_attempts: int = 3
    require_patient_verification: bool = True
    log_all_access: bool = True
    encrypt_sensitive_data: bool = True
    secret_key: str = os.getenv("SECRET_KEY", "change-in-production")

@dataclass
class MonitoringConfig:
    """Monitoring and analytics configuration."""
    langsmith_enabled: bool = True
    trace_all_interactions: bool = True
    performance_monitoring: bool = True
    error_alerting: bool = True
    analytics_retention_days: int = 90

@dataclass
class UIConfig:
    """User interface configuration."""
    app_title: str = "Medical AI Assistant"
    app_icon: str = "🩺"
    max_message_history: int = 50
    auto_scroll: bool = True
    show_timestamps: bool = True
    theme: str = "light"  # light, dark, auto

@dataclass
class APIConfig:
    """API and integration configuration."""
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    langchain_api_key: str = os.getenv("LANGCHAIN_API_KEY", "")
    langsmith_api_key: str = os.getenv("LANGSMITH_API_KEY", "")
    rate_limit_per_minute: int = 60
    retry_attempts: int = 3

@dataclass
class AlertConfig:
    """Alert and notification configuration."""
    email_enabled: bool = os.getenv("EMAIL_ALERTS_ENABLED", "false").lower() == "true"
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    email_user: str = os.getenv("ALERT_EMAIL_USER", "")
    email_password: str = os.getenv("ALERT_EMAIL_PASSWORD", "")
    alert_recipients: List[str] = None
    
    def __post_init__(self):
        if self.alert_recipients is None:
            recipients_str = os.getenv("ALERT_RECIPIENTS", "")
            self.alert_recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]

class MedicalAIConfig:
    """Main configuration class for the Medical AI Agent."""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.ai = AIConfig()
        self.emergency = EmergencyConfig()
        self.security = SecurityConfig()
        self.monitoring = MonitoringConfig()
        self.ui = UIConfig()
        self.api = APIConfig()
        self.alerts = AlertConfig()
        
        # Environment-specific overrides
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Apply environment-specific settings
        self._apply_environment_settings()
    
    def _apply_environment_settings(self):
        """Apply environment-specific configuration overrides."""
        if self.environment == "production":
            # Production overrides
            self.ai.temperature = 0.0  # More deterministic responses
            self.security.require_patient_verification = True
            self.security.log_all_access = True
            self.monitoring.trace_all_interactions = True
            self.alerts.email_enabled = True
            
        elif self.environment == "development":
            # Development overrides
            self.ai.temperature = 0.1  # Slightly more creative
            self.security.require_patient_verification = False  # Easier testing
            self.debug = True
            
        elif self.environment == "testing":
            # Testing overrides
            self.database.fhir_data_file = "data/test_fhir_records.json"
            self.alerts.email_enabled = False  # No real alerts during testing
            self.api.rate_limit_per_minute = 1000  # Higher limits for testing
    
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check required API keys
        if not self.api.groq_api_key or self.api.groq_api_key == "your_groq_key_here":
            issues.append("Groq API key not configured")
        
        if self.monitoring.langsmith_enabled and (
            not self.api.langsmith_api_key or self.api.langsmith_api_key == "your_key_here"
        ):
            issues.append("LangSmith API key not configured but monitoring is enabled")
        
        # Check file paths
        if not os.path.exists(self.database.fhir_data_file):
            issues.append(f"FHIR data file not found: {self.database.fhir_data_file}")
        
        # Check alert configuration
        if self.alerts.email_enabled and not self.alerts.email_user:
            issues.append("Email alerts enabled but no email user configured")
        
        # Check security settings
        if self.environment == "production" and self.security.secret_key == "change-in-production":
            issues.append("Default secret key detected in production environment")
        
        return issues
    
    def get_settings_summary(self) -> Dict[str, Any]:
        """Get a summary of current settings."""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "ai_model": self.ai.default_model,
            "monitoring_enabled": self.monitoring.langsmith_enabled,
            "emergency_alerts": self.alerts.email_enabled,
            "security_level": "high" if self.security.require_patient_verification else "medium",
            "api_keys_configured": {
                "groq": bool(self.api.groq_api_key and self.api.groq_api_key != "your_groq_key_here"),
                "langsmith": bool(self.api.langsmith_api_key and self.api.langsmith_api_key != "your_key_here"),
                "langchain": bool(self.api.langchain_api_key and self.api.langchain_api_key != "your_key_here")
            }
        }
    
    def export_config(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return {
            "database": self.database.__dict__,
            "ai": self.ai.__dict__,
            "emergency": self.emergency.__dict__,
            "security": {k: v for k, v in self.security.__dict__.items() if k != "secret_key"},
            "monitoring": self.monitoring.__dict__,
            "ui": self.ui.__dict__,
            "alerts": {k: v for k, v in self.alerts.__dict__.items() if "password" not in k},
            "environment": self.environment,
            "debug": self.debug
        }

# Global configuration instance
config = MedicalAIConfig()

# Convenience functions
def get_config() -> MedicalAIConfig:
    """Get the global configuration instance."""
    return config

def validate_configuration() -> bool:
    """Validate the current configuration."""
    issues = config.validate_config()
    if issues:
        print("⚠️ Configuration Issues:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    return True

def print_config_summary():
    """Print a summary of the current configuration."""
    summary = config.get_settings_summary()
    
    print("📋 Medical AI Agent Configuration Summary")
    print("=" * 50)
    print(f"Environment: {summary['environment']}")
    print(f"Debug Mode: {summary['debug']}")
    print(f"AI Model: {summary['ai_model']}")
    print(f"Monitoring: {'Enabled' if summary['monitoring_enabled'] else 'Disabled'}")
    print(f"Emergency Alerts: {'Enabled' if summary['emergency_alerts'] else 'Disabled'}")
    print(f"Security Level: {summary['security_level']}")
    
    print("\nAPI Keys Status:")
    for api, configured in summary['api_keys_configured'].items():
        status = "✅ Configured" if configured else "❌ Not configured"
        print(f"   {api.title()}: {status}")

if __name__ == "__main__":
    print_config_summary()
    print(f"\nValidation: {'✅ Passed' if validate_configuration() else '❌ Failed'}")
