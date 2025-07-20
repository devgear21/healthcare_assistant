"""
Quick start script for the Medical AI Agent.
Sets up the environment and launches the application.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_virtual_environment():
    """Check if virtual environment is activated."""
    venv_active = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    if venv_active:
        print("✅ Virtual environment is active")
        return True
    else:
        print("⚠️ Virtual environment not detected")
        print("   Recommendation: Activate your virtual environment first")
        return False

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_environment_file():
    """Check if .env file exists and has required variables."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️ .env file not found")
        create_env = input("Would you like to create a sample .env file? (y/n): ")
        
        if create_env.lower() == 'y':
            create_sample_env()
        return False
    
    # Check for required variables
    with open(env_file, 'r') as f:
        content = f.read()
    
    required_vars = ["GROQ_API_KEY", "LANGCHAIN_API_KEY", "LANGSMITH_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if var not in content or f"{var}=your_groq_key_here" in content or f"{var}=your_key_here" in content:
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️ Missing or unconfigured environment variables: {', '.join(missing_vars)}")
        print("   Please update your .env file with actual API keys")
        return False
    
    print("✅ Environment file configured")
    return True

def create_sample_env():
    """Create a sample .env file."""
    sample_content = """# Medical AI Agent Environment Variables

# Groq API Key (required for AI functionality with Llama models)
GROQ_API_KEY=your_groq_key_here

# LangChain/LangSmith API Keys (for monitoring and tracing)
LANGCHAIN_API_KEY=your_langchain_key_here
LANGSMITH_API_KEY=your_langsmith_key_here

# LangSmith Configuration
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=medical-ai-agent

# Application Settings
ENVIRONMENT=development
DEBUG=true

# Email Alert Configuration (optional)
EMAIL_ALERTS_ENABLED=false
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
ALERT_EMAIL_USER=your_email@gmail.com
ALERT_EMAIL_PASSWORD=your_app_password
ALERT_RECIPIENTS=admin@hospital.com,emergency@hospital.com

# Security (change in production)
SECRET_KEY=medical-ai-secret-key-change-in-production
"""
    
    with open(".env", "w") as f:
        f.write(sample_content)
    
    print("✅ Sample .env file created")
    print("   Please edit .env and add your actual API keys")

def run_tests():
    """Run system tests."""
    print("🧪 Running system tests...")
    
    try:
        result = subprocess.run([
            sys.executable, "test_system.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ System tests passed")
            return True
        else:
            print("⚠️ Some tests failed")
            print(result.stdout)
            return False
            
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def launch_application():
    """Launch the Streamlit application."""
    print("🚀 Launching Medical AI Agent...")
    
    try:
        # Change to the correct directory
        os.chdir(Path(__file__).parent)
        
        # Launch Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "ui/streamlit_ui.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to launch application: {e}")

def main():
    """Main setup and launch function."""
    print("🩺 Medical AI Agent - Quick Start")
    print("=" * 50)
    
    # Check system requirements
    if not check_python_version():
        return
    
    # Check virtual environment
    check_virtual_environment()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed: Could not install dependencies")
        return
    
    # Check environment configuration
    env_configured = check_environment_file()
    
    if not env_configured:
        print("\n⚠️ Environment not fully configured")
        print("   The application will run in demo mode with limited functionality")
        
        continue_anyway = input("Continue anyway? (y/n): ")
        if continue_anyway.lower() != 'y':
            print("   Please configure your .env file and run this script again")
            return
    
    # Run tests
    print("\n" + "=" * 50)
    run_tests()
    
    # Launch application
    print("\n" + "=" * 50)
    print("🎉 Setup complete! Launching the application...")
    print("\nThe Medical AI Agent will open in your web browser at:")
    print("   http://localhost:8501")
    print("\nPress Ctrl+C to stop the application")
    print("=" * 50)
    
    launch_application()

if __name__ == "__main__":
    main()
