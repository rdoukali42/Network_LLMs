# Test Suite Index

Comprehensive test coverage for the AI Multi-Agent Workflow System.

## 🧪 Test Categories

### **Unit Tests** (`/tests/unit/`)
- `test_basic_components.py` - Core component testing
- Individual component validation
- Isolated functionality testing

### **Integration Tests** (`/tests/integration/`)
- Cross-component integration testing
- API integration validation
- System-level integration checks

### **System Tests** (`/tests/system/`)
- **[test_complete_workflow_tools.py](system/test_complete_workflow_tools.py)** - End-to-end workflow testing
- **[test_agent_tools.py](system/test_agent_tools.py)** - Agent tool integration testing
- **[test_evaluator_fixes.py](system/test_evaluator_fixes.py)** - LLM evaluator validation
- **[test_live_evaluation.py](system/test_live_evaluation.py)** - Live API evaluation testing
- **[verify_websearch_removal.py](system/verify_websearch_removal.py)** - System verification after changes

### **Evaluation Tests** (`/tests/evaluation/`)
- **[test_llm_evaluation.py](evaluation/test_llm_evaluation.py)** - LLM evaluation system tests
- **[test_llm_evaluation_fixed.py](evaluation/test_llm_evaluation_fixed.py)** - Fixed evaluation tests
- **[test_llm_evaluation_new.py](evaluation/test_llm_evaluation_new.py)** - New evaluation approaches

## 🚀 Running Tests

### Quick Test Commands

```bash
# Run all tests
python -m pytest tests/ -v

# Run by category
python -m pytest tests/unit/ -v           # Unit tests only
python -m pytest tests/integration/ -v    # Integration tests only
python -m pytest tests/system/ -v         # System tests only
python -m pytest tests/evaluation/ -v     # Evaluation tests only

# Run specific test files
python -m pytest tests/system/test_complete_workflow_tools.py -v
python -m pytest tests/system/verify_websearch_removal.py -v
```

### Individual Test Execution

```bash
# System verification
cd /Users/level3/Desktop/Network
python tests/system/verify_websearch_removal.py

# Complete workflow testing
python tests/system/test_complete_workflow_tools.py

# Agent tool testing
python tests/system/test_agent_tools.py

# Evaluator testing
python tests/system/test_evaluator_fixes.py
```

## 📊 Test Coverage

### **Core System Components**
- ✅ **Agents**: ResearchAgent, AnalysisAgent
- ✅ **Tools**: CalculatorTool, DocumentAnalysisTool
- ✅ **Workflows**: Multi-agent workflow execution
- ✅ **Evaluation**: LLM evaluation system
- ✅ **Configuration**: System configuration loading

### **Integration Points**
- ✅ **Tool Integration**: Agent-tool communication
- ✅ **Workflow Integration**: End-to-end processing
- ✅ **API Integration**: Gemini Flash 1.5 API calls
- ✅ **Frontend Integration**: Streamlit app connectivity

### **System Validation**
- ✅ **Component Removal**: WebSearchTool removal verification
- ✅ **System Health**: Overall system functionality
- ✅ **Performance**: Response time and accuracy
- ✅ **Error Handling**: Graceful failure management

## 🔧 Test Configuration

### **Test Environment**
- **Python Version**: 3.8+
- **Test Framework**: pytest
- **API Testing**: Real API integration tests
- **Mock Testing**: Component isolation tests

### **Environment Variables**
```bash
# Required for live API tests
GOOGLE_API_KEY=your_google_api_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

## 📝 Test Development Guidelines

### **Adding New Tests**

1. **Unit Tests**: Place in `/tests/unit/` for individual components
2. **Integration Tests**: Place in `/tests/integration/` for component interactions  
3. **System Tests**: Place in `/tests/system/` for end-to-end testing
4. **Evaluation Tests**: Place in `/tests/evaluation/` for LLM evaluation testing

### **Test Naming Conventions**
- **Files**: `test_[component/feature]_[description].py`
- **Functions**: `test_[specific_functionality]()`
- **Classes**: `Test[ComponentName]`

### **Test Documentation**
- Include docstrings for all test functions
- Document test setup and expected outcomes
- Add comments for complex test logic

## 🎯 Continuous Integration

Tests are designed to be run in CI/CD pipelines with:
- **Automated test execution** on code changes
- **Test result reporting** and coverage analysis
- **Integration validation** before deployment

---

*Total Tests: 15+ test files covering all system components*
