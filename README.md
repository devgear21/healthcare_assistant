#  Intelligent Medical AI Agent

## Overview
A comprehensive healthcare AI assistant built with LangGraph and LangSmith, featuring specialized agents for medical consultations, appointment scheduling, emergency detection, and patient record management.

##  Features
- **Intelligent Intent Classification**: Automatically routes patient queries to specialized agents
- **Emergency Detection**: Real-time identification and escalation of urgent medical situations
- **Appointment Management**: Automated scheduling, rescheduling, and appointment reminders
- **Medical Records**: FHIR-compatible patient data management and retrieval
- **Conversational Memory**: Maintains context across interactions for personalized care
- **Advanced Monitoring**: LangSmith integration for performance tracking and optimization


##  Demo Video
[![Watch the video](https://img.youtube.com/vi/7JUhg-PUG48/hqdefault.jpg)](https://www.youtube.com/watch?v=7JUhg-PUG48)



##  Architecture
Built with **LangGraph** for workflow orchestration and **Groq Llama 3.1** models for AI capabilities:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Patient Input  │───▶│ Intent Classifier│───▶│ Specialized     │
└─────────────────┘    └─────────────────┘    │ Agent Router    │
                                              └─────────────────┘
                                                       │
                       ┌───────────────────────────────┼───────────────────────────────┐
                       ▼                               ▼                               ▼
              ┌─────────────────┐            ┌─────────────────┐            ┌─────────────────┐
              │ Emergency Agent │            │ Scheduler Agent │            │ Medical Records │
              └─────────────────┘            └─────────────────┘            │     Agent       │
                       │                               │                    └─────────────────┘
                       ▼                               ▼                               │
              ┌─────────────────┐            ┌─────────────────┐                     ▼
              │ Routine Query   │            │ Conversation    │            ┌─────────────────┐
              │     Agent       │            │     Memory      │            │ FHIR Data Store │
              └─────────────────┘            └─────────────────┘            └─────────────────┘
```

##  Project Structure
```
MedSupport/
├── agents/                      # AI Agent implementations
│   ├── intent_classifier.py     # Routes messages to appropriate agents
│   ├── emergency_agent.py       # Handles urgent medical situations
│   ├── scheduler_agent.py       # Manages appointments and scheduling
│   ├── medical_records_agent.py # Patient record management
│   └── routine_query_agent.py   # General medical queries and FAQs
├── medical_graph/               # LangGraph workflow orchestration
│   └── medical_graph.py         # Main workflow definition and state management
├── memory/                      # Conversation context management
│   └── memory_manager.py        # Patient interaction history and context
├── monitoring/                  # Performance tracking and analytics
│   └── langsmith_setup.py       # LangSmith integration for monitoring
├── ui/                          # User interface implementations
│   ├── streamlit_ui.py          # Main Streamlit web interface
│   ├── simple_test_ui.py        # Simplified UI for testing
│   └── debug_ui.py              # Debug interface for development
├── utils/                       # Utility functions and helpers
│   └── fhir_utils.py           # FHIR-compatible data management
├── data/                        # Sample data and test records
│   └── sample_fhir_records.json # Test patient data and medical records
├── tests/                       # Testing and validation
│   └── test_llm_response.py     # Backend functionality tests
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── requirements.txt             # Python dependencies
└── README.md                    # Project documentation
```


##  API Keys Required

- **Groq API Key**: For Llama 3.1 language model access
  - Get your free API key at [Groq Console](https://console.groq.com/)
- **LangChain/LangSmith API Key**: For monitoring and tracing
  - Sign up at [LangSmith](https://smith.langchain.com/)



##  Monitoring & Analytics

The system includes comprehensive monitoring through **LangSmith**:
- **Real-time Tracing**: Monitor all agent interactions and decisions
- **Performance Metrics**: Track response times and success rates
- **Conversation Analytics**: Analyze patient interaction patterns
- **Error Tracking**: Identify and debug system issues

##  Medical Compliance

- **FHIR Compatible**: Uses industry-standard healthcare data formats
- **Privacy Focused**: No sensitive patient data stored in code
- **Secure Authentication**: Patient verification system included
- **Audit Trail**: Complete interaction logging for compliance

##  Technology Stack

- **LangGraph**: Workflow orchestration and agent coordination
- **Groq Llama 3.1**: Advanced language model for AI capabilities
- **LangSmith**: Monitoring, tracing, and analytics platform
- **Streamlit**: Modern web interface framework
- **Python**: Core development language
- **FHIR**: Healthcare data standards compliance

##  Performance

- **Response Time**: < 2 seconds for routine queries
- **Accuracy**: 95%+ intent classification accuracy
- **Uptime**: Designed for 24/7 healthcare availability
- **Scalability**: Modular architecture supports easy expansion
