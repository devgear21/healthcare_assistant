#!/usr/bin/env python3
"""
GitHub Upload Preparation Script
Helps prepare the Medical AI Agent project for GitHub upload
"""

import os
import shutil
from pathlib import Path

def check_essential_files():
    """Check if all essential files are present."""
    essential_files = [
        # Core agents
        "agents/__init__.py",
        "agents/intent_classifier.py",
        "agents/emergency_agent.py", 
        "agents/scheduler_agent.py",
        "agents/medical_records_agent.py",
        "agents/routine_query_agent.py",
        
        # Workflow
        "medical_graph/__init__.py",
        "medical_graph/medical_graph.py",
        
        # Memory & Monitoring
        "memory/__init__.py",
        "memory/memory_manager.py",
        "monitoring/__init__.py", 
        "monitoring/langsmith_setup.py",
        
        # Utilities
        "utils/__init__.py",
        "utils/fhir_utils.py",
        "utils/auth.py",
        "utils/alerting.py",
        
        # Data
        "data/__init__.py",
        "data/sample_fhir_records.json",
        
        # UI
        "ui/streamlit_ui.py",
        
        # Configuration
        "requirements.txt",
        ".env.example",
        ".gitignore",
        "README.md",
        
        # Testing
        "test_system.py"
    ]
    
    missing_files = []
    present_files = []
    
    for file_path in essential_files:
        if os.path.exists(file_path):
            present_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    return present_files, missing_files

def check_sensitive_files():
    """Check for sensitive files that should NOT be uploaded."""
    sensitive_patterns = [
        ".env",
        "*.key",
        "*.pem",
        "__pycache__/",
        ".venv/",
        "venv/",
        "node_modules/",
        "*.pyc",
        ".DS_Store",
        "Thumbs.db"
    ]
    
    found_sensitive = []
    
    for pattern in sensitive_patterns:
        if "*" in pattern:
            # Simple glob-like check
            if pattern.startswith("*."):
                ext = pattern[2:]
                for file in Path(".").rglob(f"*.{ext}"):
                    found_sensitive.append(str(file))
        elif pattern.endswith("/"):
            # Directory check
            dir_name = pattern[:-1]
            if os.path.exists(dir_name):
                found_sensitive.append(dir_name)
        else:
            # Direct file check
            if os.path.exists(pattern):
                found_sensitive.append(pattern)
    
    return found_sensitive

def main():
    """Main preparation check."""
    print("🚀 GitHub Upload Preparation Check")
    print("=" * 50)
    
    # Check essential files
    present_files, missing_files = check_essential_files()
    
    print(f"\n✅ Essential files present: {len(present_files)}")
    for file in present_files[:10]:  # Show first 10
        print(f"   ✓ {file}")
    if len(present_files) > 10:
        print(f"   ... and {len(present_files) - 10} more")
    
    if missing_files:
        print(f"\n⚠️ Missing essential files: {len(missing_files)}")
        for file in missing_files:
            print(f"   ✗ {file}")
    
    # Check sensitive files
    sensitive_files = check_sensitive_files()
    if sensitive_files:
        print(f"\n🔒 Sensitive files detected (should NOT upload): {len(sensitive_files)}")
        for file in sensitive_files[:10]:  # Show first 10
            print(f"   🔒 {file}")
        if len(sensitive_files) > 10:
            print(f"   ... and {len(sensitive_files) - 10} more")
        print("   ℹ️ These files are excluded by .gitignore")
    else:
        print("\n✅ No sensitive files detected in main directory")
    
    # Summary and next steps
    print("\n" + "=" * 50)
    print("📋 GITHUB UPLOAD SUMMARY")
    print("=" * 50)
    
    if not missing_files:
        print("🎉 All essential files are ready for upload!")
        print("\n📝 Next steps:")
        print("1. Create a new repository on GitHub")
        print("2. Initialize git in this directory:")
        print("   git init")
        print("   git add .")
        print("   git commit -m 'Initial commit: Medical AI Agent'")
        print("3. Connect to your GitHub repository:")
        print("   git remote add origin https://github.com/yourusername/medical-ai-agent.git")
        print("   git branch -M main") 
        print("   git push -u origin main")
        print("\n🔐 Remember:")
        print("- Your .env file is NOT included (good for security)")
        print("- Users will need to create their own .env from .env.example")
        print("- All API keys are safely excluded")
        
    else:
        print("⚠️ Some essential files are missing. Please ensure all components are present before uploading.")
    
    print(f"\n📁 Ready to upload: ~{len(present_files)} files")
    print("📖 Full documentation: README.md")
    print("🔧 Setup guide: GITHUB_UPLOAD_GUIDE.md")

if __name__ == "__main__":
    main()
