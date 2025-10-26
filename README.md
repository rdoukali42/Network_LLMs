# 🎫 AI-Powered Support Ticket System

An intelligent multi-agent support system that combines AI-powered document retrieval with human expertise escalation. Built with LangChain, LangGraph, and Google's Gemini AI, featuring voice-enabled expert consultation and real-time ticket management.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-Latest-green.svg)](https://github.com/langchain-ai/langchain)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.50+-red.svg)](https://streamlit.io/)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Development](#-development)

---

## 🎯 Overview

This system revolutionizes IT support by intelligently routing queries through a multi-agent AI workflow. When documentation exists, AI provides instant solutions. When human expertise is needed, the system seamlessly connects users with the right experts via voice calls and automatically generates professional solutions.

### **Problem Solved**

Traditional support systems suffer from:
- **Information overload**: Hard to find relevant solutions in vast knowledge bases
- **Expert bottlenecks**: Skilled staff overwhelmed with repetitive queries
- **Slow response times**: Users wait hours for specialized help
- **Knowledge silos**: Expertise trapped with individual employees

### **Our Solution**

A hybrid AI-human system that:
- ✅ **Instantly resolves** 75%+ of queries using RAG (Retrieval Augmented Generation)
- ✅ **Intelligently escalates** complex issues to the right experts
- ✅ **Facilitates voice calls** between users and experts when needed
- ✅ **Auto-generates solutions** from expert conversations
- ✅ **Maintains context** across entire ticket lifecycle

---

## ✨ Key Features

### **Intelligent Ticket Processing**
- 🤖 **Multi-Agent AI Workflow**: Orchestrated by MaestroAgent for optimal routing
- 📚 **Semantic Document Search**: RAG-based retrieval from company knowledge base
- 🎯 **Smart Expert Matching**: HR Agent finds the best employee for each issue
- 🔄 **Real-time Status Tracking**: Live updates on ticket progress

### **Voice-Enabled Collaboration**
- 🎙️ **Audio Transcription**: Speech-to-text for user queries
- 📞 **Voice Call Interface**: Direct expert-user communication
- 🔊 **Text-to-Speech**: AI-generated voice responses
- 💬 **Conversation Recording**: Full call history for quality assurance

### **Professional UI/UX**
- 🎨 **Modern Streamlit Interface**: Clean, responsive web application
- 👥 **User Authentication**: Secure employee registration and login
- 📊 **Dashboard Analytics**: Track ticket metrics and agent performance
- 🔔 **Real-time Notifications**: Instant updates on ticket changes

### **Developer-Friendly**
- 🏗️ **Modular Architecture**: Clean separation of concerns
- 📖 **Comprehensive Documentation**: Inline docstrings and API docs
- 🧪 **Test Suite**: Unit, integration, and system tests
- 🔧 **Easy Configuration**: YAML-based settings management

---

## 🏗️ System Architecture

### **Multi-Agent Workflow**

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                           │
└────────────────────────┬────────────────────────────────────┘
                         ↓
                  ┌──────────────┐
                  │ MaestroAgent │  (Query Analysis & Orchestration)
                  └──────┬───────┘
                         ↓
              ┌──────────────────────┐
              │ DataGuardianAgent    │  (Document Retrieval)
              └──────┬───────────────┘
                     ↓
            ┌────────────────┐
            │ Documents Found?│
            └────┬────────┬───┘
                YES      NO
                 ↓        ↓
         ┌───────────┐  ┌──────────┐
         │ Generate  │  │ HR Agent │  (Expert Matching)
         │ Response  │  └────┬─────┘
         └─────┬─────┘       ↓
               ↓      ┌──────────────────┐
         ┌─────────┐  │ VocalAssistant   │  (Voice Call)
         │ Return  │  └────┬─────────────┘
         │ to User │       ↓
         └─────────┘  ┌──────────────────┐
                      │ Solution Generated│
                      └────┬──────────────┘
                           ↓
                      Return to User
```

### **Core Components**

#### **Agents**
- **MaestroAgent**: System orchestrator and decision-maker
- **DataGuardianAgent**: RAG-based document retrieval specialist
- **HR_Agent**: Employee skill matching and assignment
- **VocalAssistant**: Voice call management and transcription

#### **Tools**
- **AvailabilityTool**: Real-time employee status checking
- **CustomTools**: Calculator, document analysis, and more

#### **Infrastructure**
- **Vector Store**: ChromaDB for semantic search
- **Database**: SQLite for employee and ticket data
- **LLM**: Google Gemini Flash 1.5 for AI processing
- **Observability**: LangFuse for monitoring and debugging

---

## 🛠️ Technology Stack

### **Core AI/ML**
- **LangChain** (0.1.0+): AI application framework
- **LangGraph** (0.1.0+): Multi-agent orchestration
- **Google Gemini**: Primary LLM (Flash 1.5)
- **ChromaDB** (0.4.0+): Vector database for embeddings
- **Sentence Transformers** (2.2.0+): Text embeddings

### **Backend**
- **Python** (3.12+): Primary language
- **SQLite**: Relational database
- **Pydantic** (2.0+): Data validation
- **FastAPI** (0.100+): API framework

### **Frontend**
- **Streamlit** (1.50+): Web interface
- **Audio Processing**: Speech recognition and synthesis

### **DevOps & Monitoring**
- **LangFuse** (2.0+): LLM observability
- **Pytest**: Testing framework
- **Black**: Code formatting
- **Pre-commit**: Git hooks

---

## 📁 Project Structure

```
ticket_system/
├── src/                          # Core application code
│   ├── agents/                   # Multi-agent implementations
│   │   ├── base_agent.py        # Abstract base class
│   │   ├── maestro_agent.py     # Orchestrator agent
│   │   ├── data_guardian_agent.py # Document retrieval
│   │   ├── hr_agent.py          # Expert matching
│   │   └── vocal_assistant.py   # Voice interface
│   ├── tools/                    # Custom tools
│   │   ├── availability_tool.py # Employee status
│   │   └── custom_tools.py      # Utility tools
│   ├── graphs/                   # LangGraph workflows
│   ├── retrievers/               # RAG retrieval logic
│   ├── vectorstore/              # Vector DB management
│   ├── evaluation/               # Quality assessment
│   ├── config/                   # Configuration management
│   └── utils/                    # Helper functions
│
├── front/                        # Streamlit web interface
│   ├── app.py                   # Main entry point
│   ├── auth.py                  # Authentication
│   ├── database.py              # Database manager
│   ├── registration.py          # User registration
│   ├── workflow_client.py       # Backend integration
│   └── tickets/                 # Ticket management modules
│       ├── ticket_manager.py    # Core ticket logic
│       ├── ticket_forms.py      # UI forms
│       ├── ticket_processing.py # AI processing
│       ├── call_interface.py    # Voice call UI
│       ├── availability.py      # Status management
│       └── smart_refresh.py     # Auto-refresh logic
│
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── system/                  # End-to-end tests
│   └── evaluation/              # AI evaluation tests
│
├── configs/                      # Configuration files
│   ├── development.yaml         # Dev environment
│   └── production.yaml          # Prod environment
│
├── data/                         # Data directory
│   ├── raw/                     # Company documents
│   ├── databases/               # SQLite databases
│   └── backups/                 # Database backups
│
├── docs/                         # Documentation
│   └── architecture/            # System diagrams
│
├── notebooks/                    # Jupyter notebooks
├── scripts/                      # Utility scripts
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

---

## 🚀 Installation

### **Prerequisites**

- Python 3.12 or higher
- pip package manager
- Virtual environment (recommended)
- Google API Key for Gemini AI

### **Step 1: Clone Repository**

```bash
git clone https://github.com/rdoukali42/Network_LLMs.git
cd Network_LLMs
```

### **Step 2: Create Virtual Environment**

```bash
python -m venv venv

# Activate on Linux/macOS
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### **Step 3: Install Dependencies**

```bash
# Install all dependencies
pip install -r requirements.txt
```

### **Step 4: Set Up Environment Variables**

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your API keys
```

Required environment variables:
```bash
# Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here

# LangFuse (Optional - for monitoring)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com

# Application Settings
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### **Step 5: Initialize Data Directories**

```bash
# Create necessary directories
mkdir -p data/databases data/backups data/raw

# Add your company documents to data/raw/
# Example: company_scope.md, company_code_of_conduct.md
```

---

## ⚙️ Configuration

### **YAML Configuration**

Edit `configs/development.yaml` or `configs/production.yaml`:

```yaml
# Model Configuration
model:
  provider: "google"
  name: "gemini-1.5-flash"
  temperature: 0.7
  max_tokens: 4096

# Vector Store
vectorstore:
  type: "chroma"
  persist_directory: "data/chroma_db"
  collection_name: "company_docs"

# Agents
agents:
  maestro:
    enabled: true
    max_iterations: 5
  data_guardian:
    enabled: true
    top_k: 5
  hr_agent:
    enabled: true
  vocal_assistant:
    enabled: true

# Logging
logging:
  level: "INFO"
  format: "detailed"
```

---

## 💻 Usage

### **Running the Web Application**

```bash
# Make sure you're in the project root with venv activated
source venv/bin/activate

# Run Streamlit app
streamlit run front/app.py
```

Access the application at: **http://localhost:8501**

### **Default Login Credentials**

For testing purposes:
- Username: `admin` / Password: `admin123`
- Username: `demo` / Password: `demo`

**Note**: Register new employees through the "Register as Employee" option.

### **Using the System**

1. **Login/Register**: Authenticate or create an employee account
2. **Create Ticket**: Submit a support query
3. **AI Processing**: System analyzes and routes your ticket
4. **Get Solution**: Receive instant AI response or expert consultation
5. **Voice Call** (if escalated): Connect with expert via voice
6. **Track Status**: Monitor ticket progress in real-time

### **Programmatic Usage**

```python
from src.main import TicketWorkflow
from src.config import load_config

# Initialize system
config = load_config("development")
workflow = TicketWorkflow(config)

# Process a ticket
result = workflow.process_ticket(
    user_query="How do I reset my password?",
    user_id="user123",
    priority="medium"
)

print(result['status'])        # "solved" or "escalated"
print(result['response'])      # AI-generated solution
print(result['assigned_to'])   # Employee if escalated
```

---

## 📚 API Documentation

### **Ticket Manager**

```python
from front.tickets.ticket_manager import TicketManager

manager = TicketManager()

# Create ticket
ticket_id = manager.create_ticket(
    subject="Database connection issue",
    description="Cannot connect to production database",
    priority="high",
    created_by="john.doe"
)

# Get ticket status
status = manager.get_ticket_status(ticket_id)

# Update ticket
manager.update_ticket(ticket_id, status="resolved")
```

### **Database Manager**

```python
from front.database import db_manager

# Register employee
db_manager.register_employee(
    username="jane.smith",
    full_name="Jane Smith",
    role="Senior DevOps Engineer",
    expertise="Kubernetes, Docker, AWS"
)

# Check availability
status = db_manager.get_employee_availability("jane.smith")

# Update availability
db_manager.update_availability(
    username="jane.smith",
    status="Available",
    until_datetime="2025-10-26 18:00:00"
)
```

---

## 🧪 Testing

### **Run All Tests**

```bash
# Run complete test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov=front --cov-report=html
```

### **Run Specific Test Categories**

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# System tests (end-to-end)
pytest tests/system/ -v

# Evaluation tests
pytest tests/evaluation/ -v
```

### **Test Structure**

- `tests/unit/`: Component-level tests
- `tests/integration/`: Multi-component interaction tests
- `tests/system/`: Full workflow tests
- `tests/evaluation/`: LLM output quality tests

---

## 🔧 Development

### **Code Style**

This project follows PEP 8 and uses automated formatting:

```bash
# Format code
black src/ front/ tests/

# Lint code
flake8 src/ front/ tests/

# Type checking (optional)
mypy src/
```

### **Pre-commit Hooks**

Install pre-commit hooks for automatic checks:

```bash
pre-commit install
pre-commit run --all-files
```

### **Adding New Agents**

1. Create agent class inheriting from `BaseAgent`:

```python
from src.agents.base_agent import BaseAgent

class MyCustomAgent(BaseAgent):
    def __init__(self, config):
        super().__init__(config)
        self.agent_name = "MyCustomAgent"
    
    def process(self, input_data):
        # Implementation
        pass
```

2. Register in `src/agents/__init__.py`
3. Add configuration in YAML files
4. Write tests in `tests/unit/test_my_custom_agent.py`

### **Adding New Tools**

```python
from langchain.tools import Tool

def my_custom_function(input_str: str) -> str:
    """Tool description for LLM."""
    # Implementation
    return result

my_tool = Tool(
    name="MyCustomTool",
    func=my_custom_function,
    description="What this tool does"
)
```

---

## 📊 Database Schema

### **Employees Table**

```sql
CREATE TABLE employees_data_table (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role_in_company VARCHAR(100) NOT NULL,
    job_description TEXT NOT NULL,
    expertise TEXT NOT NULL,
    responsibilities TEXT NOT NULL,
    availability_status TEXT DEFAULT 'Offline',
    status_until TIMESTAMP NULL,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### **Call Notifications Table**

```sql
CREATE TABLE call_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_employee VARCHAR(50) NOT NULL,
    ticket_id VARCHAR(50) NOT NULL,
    ticket_subject TEXT NOT NULL,
    caller_name TEXT NOT NULL,
    call_info JSON NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

**Quick steps:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **LangChain** team for the excellent framework
- **Google** for Gemini AI models
- **Streamlit** for the beautiful UI framework
- Open source community for various tools and libraries
