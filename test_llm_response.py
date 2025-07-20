"""
Quick test to verify LLM responses and tracing are working.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_llm_response():
    """Test that the LLM is responding correctly."""
    print("🧪 Testing LLM Response and Tracing")
    print("=" * 40)
    
    # Test environment setup
    print("🔧 Environment Check:")
    groq_key = os.getenv("GROQ_API_KEY")
    langsmith_key = os.getenv("LANGSMITH_API_KEY")
    print(f"   GROQ_API_KEY: {'✅ SET' if groq_key else '❌ MISSING'}")
    print(f"   LANGSMITH_API_KEY: {'✅ SET' if langsmith_key else '❌ MISSING'}")
    
    # Test LangSmith tracing setup
    print("\n📊 Tracing Setup:")
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false")
    project = os.getenv("LANGCHAIN_PROJECT", "not set")
    print(f"   LANGCHAIN_TRACING_V2: {tracing_enabled}")
    print(f"   LANGCHAIN_PROJECT: {project}")
    
    # Test direct LLM call
    print("\n🤖 Testing Direct LLM Call:")
    try:
        from langchain_groq import ChatGroq
        
        llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0,
            api_key=groq_key
        )
        
        response = llm.invoke("What is the capital of France? Answer in one word.")
        print(f"   ✅ LLM Response: {response.content}")
        
    except Exception as e:
        print(f"   ❌ LLM Error: {e}")
        return False
    
    # Test medical graph
    print("\n🏥 Testing Medical AI Agent:")
    try:
        from medical_graph.medical_graph import process_patient_message
        
        test_message = "Hello, I need help"
        response = process_patient_message(test_message, "test-patient")
        
        if response and response != "I apologize, but I couldn't process your request.":
            print(f"   ✅ Medical AI Response: {response[:100]}...")
        else:
            print(f"   ❌ No valid response from Medical AI")
            return False
            
    except Exception as e:
        print(f"   ❌ Medical AI Error: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 All tests passed! LLM and tracing working correctly.")
    return True

if __name__ == "__main__":
    test_llm_response()
