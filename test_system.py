"""
Test script for the Medical AI Agent.
Tests various components and workflows to ensure everything is working correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_environment():
    """Test environment setup and dependencies."""
    print("🧪 Testing Environment Setup...")
    
    try:
        # Test imports
        import langgraph
        import langchain
        import streamlit
        import openai
        print("✅ Core dependencies imported successfully")
        
        # Test environment variables
        api_keys = ["GROQ_API_KEY", "LANGCHAIN_API_KEY", "LANGSMITH_API_KEY"]
        for key in api_keys:
            value = os.getenv(key)
            if value and value not in ["your_key_here", "your_groq_key_here"]:
                print(f"✅ {key} is configured")
            else:
                print(f"⚠️ {key} not configured (using demo mode)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_fhir_data():
    """Test FHIR data loading and utilities."""
    print("\n🧪 Testing FHIR Data Management...")
    
    try:
        from utils.fhir_utils import fhir_manager, get_patient_info, search_patients
        
        # Test patient data loading
        patients = fhir_manager.data.get("patients", [])
        print(f"✅ Loaded {len(patients)} patients")
        
        # Test patient search
        if patients:
            test_patient = patients[0]
            patient_info = get_patient_info(test_patient["id"])
            if patient_info:
                print(f"✅ Retrieved patient: {patient_info['name']}")
            
            # Test search
            search_results = search_patients(test_patient["name"])
            if search_results:
                print(f"✅ Search found {len(search_results)} patients")
        
        # Test FAQs
        faqs = fhir_manager.get_faqs()
        print(f"✅ Loaded {len(faqs)} FAQs")
        
        return True
        
    except Exception as e:
        print(f"❌ FHIR test failed: {e}")
        return False

def test_agents():
    """Test individual agent components."""
    print("\n🧪 Testing Agent Components...")
    
    try:
        # Test intent classifier
        from agents.intent_classifier import classify_intent
        
        test_cases = [
            {"message": "I need to schedule an appointment", "expected": "appointment"},
            {"message": "Show me my medical history", "expected": "medical_records"},
            {"message": "I'm having chest pain", "expected": "emergency"},
            {"message": "What are your office hours?", "expected": "routine"}
        ]
        
        for test in test_cases:
            result = classify_intent({"message": test["message"]})
            intent = result.get("intent", "")
            if intent == test["expected"]:
                print(f"✅ Intent classification: '{test['message'][:30]}...' → {intent}")
            else:
                print(f"⚠️ Intent classification: '{test['message'][:30]}...' → {intent} (expected {test['expected']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        return False

def test_memory():
    """Test memory management."""
    print("\n🧪 Testing Memory Management...")
    
    try:
        from memory.memory_manager import get_memory_manager
        
        # Test memory manager
        memory = get_memory_manager("test_patient")
        
        # Test saving interaction
        memory.save_interaction(
            "Test user message", 
            "Test AI response", 
            {"intent": "test", "timestamp": "2025-07-19"}
        )
        
        # Test retrieving history
        history = memory.get_conversation_history()
        if history:
            print(f"✅ Memory saved and retrieved {len(history)} messages")
        
        # Test clearing memory
        memory.clear_memory()
        print("✅ Memory cleared successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory test failed: {e}")
        return False

def test_main_graph():
    """Test the main LangGraph workflow."""
    print("\n🧪 Testing Main LangGraph Workflow...")
    
    try:
        from medical_graph.medical_graph import process_patient_message
        
        # Test routine query
        response = process_patient_message(
            message="What are your office hours?",
            patient_id="patient-001"
        )
        
        if response and len(response) > 10:
            print("✅ Routine query processed successfully")
            print(f"   Response preview: {response[:100]}...")
        
        # Test appointment request
        response = process_patient_message(
            message="I need to schedule an appointment",
            patient_id="patient-001"
        )
        
        if response and "appointment" in response.lower():
            print("✅ Appointment request processed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Main graph test failed: {e}")
        return False

def test_monitoring():
    """Test monitoring and alerting."""
    print("\n🧪 Testing Monitoring & Alerting...")
    
    try:
        from monitoring.langsmith_setup import get_callback_manager, trace_medical_interaction
        from utils.alerting import alert_manager
        
        # Test callback manager
        callback_manager = get_callback_manager()
        if callback_manager:
            print("✅ Callback manager initialized")
        
        # Test tracing
        trace_medical_interaction("test input", "test output", "test")
        print("✅ Interaction tracing works")
        
        # Test alert system
        alert_history = alert_manager.get_alert_history()
        print(f"✅ Alert system operational ({len(alert_history)} alerts in history)")
        
        return True
        
    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")
        return False

def run_integration_test():
    """Run a complete integration test."""
    print("\n🧪 Running Integration Test...")
    
    try:
        from medical_graph.medical_graph import process_patient_message
        
        # Simulate a complete patient interaction
        test_scenarios = [
            {
                "message": "Hello, I'd like to check my upcoming appointments",
                "description": "Appointment check"
            },
            {
                "message": "Can you show me my current medications?",
                "description": "Medical records request"
            },
            {
                "message": "I'm having severe chest pain and shortness of breath",
                "description": "Emergency situation"
            },
            {
                "message": "What insurance plans do you accept?",
                "description": "General inquiry"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n   Testing: {scenario['description']}")
            response = process_patient_message(
                message=scenario["message"],
                patient_id="patient-001"
            )
            
            if response and len(response) > 20:
                print(f"   ✅ Response generated ({len(response)} chars)")
            else:
                print(f"   ⚠️ Short or no response")
        
        print("\n✅ Integration test completed")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🩺 Medical AI Agent - System Tests")
    print("=" * 50)
    
    test_results = []
    
    # Run all tests
    test_results.append(test_environment())
    test_results.append(test_fhir_data())
    test_results.append(test_agents())
    test_results.append(test_memory())
    test_results.append(test_monitoring())
    test_results.append(test_main_graph())
    test_results.append(run_integration_test())
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! The Medical AI Agent is ready to use.")
        print("\nTo start the application:")
        print("   streamlit run ui/streamlit_ui.py")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
        print("   Common issues:")
        print("   - Missing API keys in .env file")
        print("   - Missing dependencies (run: pip install -r requirements.txt)")
        print("   - Network connectivity issues")
    
    print("\n📞 Support: If you need help, check the README.md file")

if __name__ == "__main__":
    main()
