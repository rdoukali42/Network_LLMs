# AI Multi-Agent Workflow System

A comprehensive AI system implementing multi-agent workflows using LangChain, LangGraph, and Gemini Flash 1.5.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google API Key (for Gemini Flash 1.5)

### Installation
```bash
# Clone and setup
git clone <repository>
cd Network

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Run the Streamlit App
```bash
cd front/
./start.sh
```
Access at: http://localhost:8501

**Login credentials:**
- admin / admin123
- user / user123  
- demo / demo

## 🏗️ Project Structure

```
├── src/                    # Core AI system
│   ├── agents/            # Multi-agent implementations
│   ├── tools/             # Custom tools (Employee Search, Availability)
│   ├── chains/            # LangChain implementations
│   ├── graphs/            # LangGraph workflows
│   ├── models/            # Pydantic data models
│   ├── utils/             # Utility functions
│   └── vectorstore/       # Document vector storage
├── front/                 # Streamlit web interface
│   └── tickets/          # Ticket management system
├── data/                  # Data storage
│   ├── databases/        # Employee and ticket databases
│   ├── chroma_db/        # Vector database
│   └── raw/              # Raw documents
└── configs/              # Configuration files
```

## 🤖 System Components

### **Core Agents**
- **MaestroAgent**: Query preprocessing and response synthesis
- **DataGuardianAgent**: Local document search and verification
- **HRAgent**: Employee assignment and management
- **VocalAssistant**: Voice call handling and redirect detection

### **Available Tools**
- **EmployeeSearchTool**: Find and match employees by criteria
- **AvailabilityTool**: Check employee availability status
- **DocumentAnalysisTool**: Document processing and insights

### **Key Features**
- ✅ **Multi-agent workflows** with LangGraph
- ✅ **Employee assignment system** with redirect capabilities
- ✅ **Voice call interface** with conversation analysis
- ✅ **Ticket management system** with real-time processing
- ✅ **Document retrieval** with vector search
- ✅ **Streamlit web interface** with authentication
- ✅ **Modular architecture** for easy extension

## 📖 Documentation

### System Documentation
- **[System Complete Guide](docs/system/SYSTEM_COMPLETE.md)** - Complete system overview
- **[Evaluator Fixes](docs/system/EVALUATOR_FIXES_SUMMARY.md)** - LLM evaluator improvements

### Project Documentation  
- **[Project History](docs/project/README.md)** - Detailed project documentation
- **[Completion Report](docs/project/COMPLETION_REPORT.md)** - Development completion status
- **[LangFuse Integration](docs/project/LANGFUSE_INTEGRATION_GUIDE.md)** - Observability setup

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/unit/ -v           # Unit tests
python -m pytest tests/integration/ -v    # Integration tests
python -m pytest tests/system/ -v         # System tests
python -m pytest tests/evaluation/ -v     # Evaluation tests
```

### System Tests
- `tests/system/test_complete_workflow_tools.py` - End-to-end workflow testing
- `tests/system/verify_websearch_removal.py` - System verification
- `tests/system/test_evaluator_fixes.py` - Evaluator testing

## 🔧 Configuration

The system supports multiple configurations:

- **Development**: `configs/development.yaml`
- **Production**: `configs/production.yaml` 
- **Experiments**: `configs/experiments/`

## 🎯 Usage Examples

### Basic System Usage
```python
from src.main import AISystem

# Initialize system
system = AISystem("development")

# Process queries
result = system.process_query("What is machine learning?")
print(result['synthesis'])
```

### Web Interface
The Streamlit app provides a complete web interface with:
- User authentication
- Real-time chat
- Multi-agent workflow integration
- Session management

## 🔮 What's Next

- [ ] Enhanced tool integrations
- [ ] Advanced retrieval strategies
- [ ] Real-time evaluation dashboard
- [ ] Multi-modal capabilities

## 📝 License

This project is for educational and research purposes.

---

**Built with:** LangChain • LangGraph • Streamlit • Gemini Flash 1.5 • LangFuse
