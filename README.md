# 🎫 AI-Powered Support Ticket System# AI Multi-Agent Workflow System



An intelligent multi-agent support system that combines AI-powered document retrieval with human expertise escalation. Built with LangChain, LangGraph, and Google's Gemini AI, featuring voice-enabled expert consultation and real-time ticket management.A comprehensive AI system implementing multi-agent workflows using LangChain, LangGraph, and Gemini Flash 1.5.



[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)## 🚀 Quick Start

[![LangChain](https://img.shields.io/badge/LangChain-Latest-green.svg)](https://github.com/langchain-ai/langchain)

[![Streamlit](https://img.shields.io/badge/Streamlit-1.50+-red.svg)](https://streamlit.io/)### Prerequisites

- Python 3.8+

---- Google API Key (for Gemini Flash 1.5)



## 📋 Table of Contents### Installation

```bash

- [Overview](#-overview)# Clone and setup

- [Key Features](#-key-features)git clone <repository>

- [System Architecture](#-system-architecture)cd Network

- [Technology Stack](#-technology-stack)

- [Project Structure](#-project-structure)# Create virtual environment

- [Installation](#-installation)python -m venv venv

- [Configuration](#-configuration)source venv/bin/activate  # On macOS/Linux

- [Usage](#-usage)

- [API Documentation](#-api-documentation)# Install dependencies

- [Testing](#-testing)pip install -r requirements.txt

- [Development](#-development)

# Configure environment

---cp .env.example .env

# Edit .env with your API keys

## 🎯 Overview```



This system revolutionizes IT support by intelligently routing queries through a multi-agent AI workflow. When documentation exists, AI provides instant solutions. When human expertise is needed, the system seamlessly connects users with the right experts via voice calls and automatically generates professional solutions.### Run the Streamlit App

```bash

### **Problem Solved**cd front/

./start.sh

Traditional support systems suffer from:```

- **Information overload**: Hard to find relevant solutions in vast knowledge basesAccess at: http://localhost:8501

- **Expert bottlenecks**: Skilled staff overwhelmed with repetitive queries

- **Slow response times**: Users wait hours for specialized help**Login credentials:**

- **Knowledge silos**: Expertise trapped with individual employees- admin / admin123

- user / user123  

### **Our Solution**- demo / demo



A hybrid AI-human system that:## 🏗️ Project Structure

- ✅ **Instantly resolves** 75%+ of queries using RAG (Retrieval Augmented Generation)

- ✅ **Intelligently escalates** complex issues to the right experts```

- ✅ **Facilitates voice calls** between users and experts when needed├── src/                    # Core AI system

- ✅ **Auto-generates solutions** from expert conversations│   ├── agents/            # Multi-agent implementations

- ✅ **Maintains context** across entire ticket lifecycle│   ├── tools/             # Custom tools (Calculator, DocumentAnalysis)

│   ├── chains/            # LangChain implementations

---│   ├── graphs/            # LangGraph workflows

│   └── evaluation/        # LLM evaluation system

## ✨ Key Features├── front/                 # Streamlit web interface

├── tests/                 # Comprehensive test suite

### **Intelligent Ticket Processing**│   ├── unit/             # Unit tests

- 🤖 **Multi-Agent AI Workflow**: Orchestrated by MaestroAgent for optimal routing│   ├── integration/      # Integration tests

- 📚 **Semantic Document Search**: RAG-based retrieval from company knowledge base│   ├── system/           # System-level tests

- 🎯 **Smart Expert Matching**: HR Agent finds the best employee for each issue│   └── evaluation/       # Evaluation tests

- 🔄 **Real-time Status Tracking**: Live updates on ticket progress├── docs/                  # Documentation

│   ├── system/           # System documentation

### **Voice-Enabled Collaboration**│   └── project/          # Project history & guides

- 🎙️ **Audio Transcription**: Speech-to-text for user queries├── examples/             # Demo applications

- 📞 **Voice Call Interface**: Direct expert-user communication├── debug/                # Debug utilities

- 🔊 **Text-to-Speech**: AI-generated voice responses└── configs/              # Configuration files

- 💬 **Conversation Recording**: Full call history for quality assurance```



### **Professional UI/UX**## 🤖 System Components

- 🎨 **Modern Streamlit Interface**: Clean, responsive web application

- 👥 **User Authentication**: Secure employee registration and login### **Core Agents**

- 📊 **Dashboard Analytics**: Track ticket metrics and agent performance- **MaestroAgent**: Query preprocessing and response synthesis

- 🔔 **Real-time Notifications**: Instant updates on ticket changes- **DataGuardianAgent**: Local document search and verification



### **Developer-Friendly**### **Available Tools**

- 🏗️ **Modular Architecture**: Clean separation of concerns- **CalculatorTool**: Mathematical calculations

- 📖 **Comprehensive Documentation**: Inline docstrings and API docs- **DocumentAnalysisTool**: Document processing and insights

- 🧪 **Test Suite**: Unit, integration, and system tests

- 🔧 **Easy Configuration**: YAML-based settings management### **Key Features**

- ✅ **Multi-agent workflows** with LangGraph

---- ✅ **Real-time chat interface** with Streamlit

- ✅ **Tool integration** for enhanced capabilities

## 🏗️ System Architecture- ✅ **LLM evaluation system** with Gemini Flash 1.5

- ✅ **Modular architecture** for easy extension

### **Multi-Agent Workflow**- ✅ **Comprehensive testing** suite



```## 📖 Documentation

┌─────────────────────────────────────────────────────────────┐

│                        User Query                           │### System Documentation

└────────────────────────┬────────────────────────────────────┘- **[System Complete Guide](docs/system/SYSTEM_COMPLETE.md)** - Complete system overview

                         ↓- **[Evaluator Fixes](docs/system/EVALUATOR_FIXES_SUMMARY.md)** - LLM evaluator improvements

                  ┌──────────────┐

                  │ MaestroAgent │  (Query Analysis & Orchestration)### Project Documentation  

                  └──────┬───────┘- **[Project History](docs/project/README.md)** - Detailed project documentation

                         ↓- **[Completion Report](docs/project/COMPLETION_REPORT.md)** - Development completion status

              ┌──────────────────────┐- **[LangFuse Integration](docs/project/LANGFUSE_INTEGRATION_GUIDE.md)** - Observability setup

              │ DataGuardianAgent    │  (Document Retrieval)

              └──────┬───────────────┘## 🧪 Testing

                     ↓

            ┌────────────────┐```bash

            │ Documents Found?│# Run all tests

            └────┬────────┬───┘python -m pytest tests/ -v

                YES      NO

                 ↓        ↓# Run specific test categories

         ┌───────────┐  ┌──────────┐python -m pytest tests/unit/ -v           # Unit tests

         │ Generate  │  │ HR Agent │  (Expert Matching)python -m pytest tests/integration/ -v    # Integration tests

         │ Response  │  └────┬─────┘python -m pytest tests/system/ -v         # System tests

         └─────┬─────┘       ↓python -m pytest tests/evaluation/ -v     # Evaluation tests

               ↓      ┌──────────────────┐```

         ┌─────────┐  │ VocalAssistant   │  (Voice Call)

         │ Return  │  └────┬─────────────┘### System Tests

         │ to User │       ↓- `tests/system/test_complete_workflow_tools.py` - End-to-end workflow testing

         └─────────┘  ┌──────────────────┐- `tests/system/verify_websearch_removal.py` - System verification

                      │ Solution Generated│- `tests/system/test_evaluator_fixes.py` - Evaluator testing

                      └────┬──────────────┘

                           ↓## 🔧 Configuration

                      Return to User

```The system supports multiple configurations:



### **Core Components**- **Development**: `configs/development.yaml`

- **Production**: `configs/production.yaml` 

#### **Agents**- **Experiments**: `configs/experiments/`

- **MaestroAgent**: System orchestrator and decision-maker

- **DataGuardianAgent**: RAG-based document retrieval specialist## 🎯 Usage Examples

- **HR_Agent**: Employee skill matching and assignment

- **VocalAssistant**: Voice call management and transcription### Basic System Usage

```python

#### **Tools**from src.main import AISystem

- **AvailabilityTool**: Real-time employee status checking

- **CustomTools**: Calculator, document analysis, and more# Initialize system

system = AISystem("development")

#### **Infrastructure**

- **Vector Store**: ChromaDB for semantic search# Process queries

- **Database**: SQLite for employee and ticket dataresult = system.process_query("What is machine learning?")

- **LLM**: Google Gemini Flash 1.5 for AI processingprint(result['synthesis'])

- **Observability**: LangFuse for monitoring and debugging```



---### Web Interface

The Streamlit app provides a complete web interface with:

## 🛠️ Technology Stack- User authentication

- Real-time chat

### **Core AI/ML**- Multi-agent workflow integration

- **LangChain** (0.1.0+): AI application framework- Session management

- **LangGraph** (0.1.0+): Multi-agent orchestration

- **Google Gemini**: Primary LLM (Flash 1.5)## 🔮 What's Next

- **ChromaDB** (0.4.0+): Vector database for embeddings

- **Sentence Transformers** (2.2.0+): Text embeddings- [ ] Enhanced tool integrations

- [ ] Advanced retrieval strategies

### **Backend**- [ ] Real-time evaluation dashboard

- **Python** (3.12+): Primary language- [ ] Multi-modal capabilities

- **SQLite**: Relational database

- **Pydantic** (2.0+): Data validation## 📝 License

- **FastAPI** (0.100+): API framework

This project is for educational and research purposes.

### **Frontend**

- **Streamlit** (1.50+): Web interface---

- **Audio Processing**: Speech recognition and synthesis

**Built with:** LangChain • LangGraph • Streamlit • Gemini Flash 1.5 • LangFuse

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
│   ├── architecture/            # System diagrams
│   └── project/                 # Project guides
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
git clone https://github.com/yourusername/ticket_system.git
cd ticket_system
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

# Install Streamlit (for web interface)
pip install -r front/requirements_streamlit.txt
```

### **Step 4: Set Up Environment Variables**

Create a `.env` file in the project root:

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

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **Contribution Guidelines**

- Write clean, documented code
- Add tests for new features
- Update README if needed
- Follow existing code style
- Keep commits atomic and well-described

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Acknowledgments

- **LangChain** team for the excellent framework
- **Google** for Gemini AI models
- **Streamlit** for the beautiful UI framework
- Open source community for various tools and libraries

---

**Built with ❤️ using LangChain, LangGraph, and Gemini AI**

*Last Updated: October 2025*
