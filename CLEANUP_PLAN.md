# 📋 Project Cleanup Plan

## 🎯 Goal
Clean up the AI Multi-Agent Workflow System by removing unnecessary files, test code, debug scripts, and calculator tools while preserving core functionality.

## 🔍 Analysis Summary
After analyzing the entire codebase, I've identified the core workflow system with these essential components:

### ✅ **KEEP - Core System Files**

#### **Main Application**
- `src/main.py` - Main AI System orchestrator
- `src/config/config_loader.py` - Configuration management
- `configs/development.yaml` - Core configuration
- `configs/production.yaml` - Production configuration
- `.env` - Environment variables
- `requirements.txt` - Dependencies

#### **Core Agents (ALL NEEDED)**
- `src/agents/base_agent.py` - Base agent class
- `src/agents/maestro_agent.py` - Query processing & synthesis
- `src/agents/data_guardian_agent.py` - Document search & analysis
- `src/agents/hr_agent.py` - Employee management & assignment
- `src/agents/vocal_assistant.py` - Voice call handling & redirect detection

#### **Essential Tools**
- `src/tools/employee_search_tool.py` - Employee search functionality (USED)
- `src/tools/availability_tool.py` - Employee availability checking (USED)
- `src/tools/__init__.py` - Tool package initialization

#### **Core Workflow**
- `src/graphs/workflow.py` - Main multi-agent workflow with LangGraph
- `src/graphs/__init__.py`

#### **Data & Storage**
- `src/vectorstore/vector_manager.py` - Document vector storage
- `data/` - Data directory (documents, databases, backups)
- `data/databases/employees.db` - Employee database
- `data/chroma_db/` - Vector database

#### **Frontend Application (COMPLETE FRONTEND)**
- `front/app.py` - Main Streamlit application
- `front/auth.py` - Authentication system
- `front/database.py` - Database interface
- `front/registration.py` - User registration
- `front/streamlit_config.py` - Streamlit configuration
- `front/tickets.py` - Ticket management interface
- `front/tickets.json` - Ticket storage
- `front/vocal_components.py` - Voice interface components
- `front/vocale.py` - Voice assistant interface
- `front/workflow_client.py` - Workflow integration
- `front/tickets/` - Complete ticket management system
- `front/requirements_streamlit.txt` - Frontend dependencies
- `front/.streamlit/` - Streamlit configuration

#### **Support Files**
- `src/utils/helpers.py` - Utility functions
- `src/utils/api_tracker.py` - API usage tracking
- `src/models/common_models.py` - Pydantic models
- `src/models/hr_models.py` - HR-specific models
- `src/retrievers/custom_retrievers.py` - Document retrieval
- `src/chains/basic_chains.py` - LangChain implementations
- `README.md` - Project documentation

---

## ❌ **REMOVE - Unnecessary Files**

### **Calculator Tools (AS REQUESTED)**
- `src/tools/custom_tools.py` - Contains CalculatorTool and DocumentAnalysisTool
- **Action:** Remove CalculatorTool, keep DocumentAnalysisTool if used elsewhere

### **Debug Scripts (ALL TEMPORARY)**
- `debug_conversation_analysis.py` - Debug vocal assistant
- `debug_end_call_process.py` - Debug end call process
- `debug_vocal_parsing.py` - Debug vocal parsing
- `deep_redirect_test.py` - Deep redirect testing
- `diagnose_hr_issues.py` - HR diagnostics
- `streamlit_reload_fix.py` - Streamlit reload utility

### **Test Files (ALL SIMULATION/DEBUG)**
- `test_company_scope.py` - Company scope testing
- `test_complete_end_call_workflow.py` - End call workflow testing
- `test_complete_workflow.py` - Complete workflow testing
- `test_completed_call_synthesis.py` - Call synthesis testing
- `test_dataguardian_format.py` - DataGuardian format testing
- `test_debug_tracing.py` - Debug tracing
- `test_end_call_maestro_fix.py` - End call maestro fix testing
- `test_end_call_redirect.py` - End call redirect testing
- `test_final_redirect_system.py` - Final redirect system testing
- `test_frontend_end_call.py` - Frontend end call testing
- `test_integration.py` - Integration testing
- `test_new_redirect_workflow.py` - New redirect workflow testing
- `test_patrick_assignment.py` - Patrick assignment testing
- `test_patrick_redirect.py` - Patrick redirect testing
- `test_real_end_call_scenario.py` - Real end call scenario testing
- `test_real_end_to_end_redirect.py` - Real end-to-end redirect testing
- `test_real_redirect_scenarios.py` - Real redirect scenarios testing
- `test_real_ticket_assignment.py` - Real ticket assignment testing
- `test_redirect_conversation.py` - Redirect conversation testing
- `test_redirect_functionality.py` - Redirect functionality testing
- `test_redirect_workflow.py` - Redirect workflow testing
- `test_search_debug.py` - Search debug testing
- `test_simple_analysis.py` - Simple analysis testing
- `test_vocal_debug.py` - Vocal debug testing
- `test_vocal_response_fix.py` - Vocal response fix testing

### **Enhancement/Experimental Scripts**
- `enhance_ticket_schema.py` - Ticket schema enhancement

### **Documentation Directories (EVALUATE)**
- `docs/` - Check if needed for project understanding
- `notebooks/comprehensive_system_test.ipynb` - Jupyter notebook testing
- `tests/` - Formal test structure (may keep for future)

### **Development Files**
- `todo.md` - Development notes
- `claude/todo.md` - Claude-specific notes
- `END_CALL_FIX_SUMMARY.md` - Fix documentation

### **Scripts (EVALUATE)**
- `scripts/run_experiments.py` - Experiment runner
- `scripts/setup_project.py` - Project setup

### **Evaluation System (QUESTIONABLE)**
- `src/evaluation/llm_evaluator.py` - LLM evaluation system (may be needed for quality)

### **Backup Files**
- `front/tickets_backup.json` - Backup ticket data

---

## 🔧 **CODE MODIFICATIONS NEEDED**

### **1. Remove Calculator Tool References**
**Files to modify:**
- `src/main.py` - Remove CalculatorTool import and usage
- `src/agents/maestro_agent.py` - Remove calculator tool references from prompts

### **2. Clean up Tool Imports**
**Files to modify:**
- `src/tools/__init__.py` - Update imports to exclude removed tools
- Any agent files importing custom_tools

### **3. Update Documentation**
**Files to modify:**
- `README.md` - Update to reflect cleaned structure
- Remove references to removed files

---

## 📊 **Cleanup Impact Analysis**

### **Files to Keep: ~45 core files**
- 5 agents (all essential for workflow)
- 2 core tools (employee search, availability)
- 1 main workflow file
- Complete frontend system
- Configuration and data files
- Support utilities

### **Files to Remove: ~35+ files**
- ~25 test files (all debug/simulation)
- ~6 debug scripts
- ~3 experimental/enhancement scripts
- 1+ documentation files (if not needed)

### **Code Changes: Minimal**
- Remove calculator tool from 2-3 files
- Update import statements
- Clean up references

---

## ✅ **Post-Cleanup Verification**

### **Core Functionality Preserved:**
1. ✅ Multi-agent workflow (Maestro, DataGuardian, HR, VocalAssistant)
2. ✅ Employee search and assignment
3. ✅ Document retrieval and analysis
4. ✅ Voice call handling and redirect detection
5. ✅ Ticket management system
6. ✅ Streamlit frontend interface
7. ✅ Configuration management
8. ✅ Vector storage and retrieval

### **Removed Functionality:**
1. ❌ Calculator tool (as requested)
2. ❌ Debug and simulation scripts
3. ❌ Test files for development
4. ❌ Experimental features

---

## 🚀 **Execution Steps**

1. **Backup** - Create backup of current state
2. **Remove Files** - Delete all identified unnecessary files
3. **Modify Code** - Remove calculator tool references
4. **Update Imports** - Clean up import statements
5. **Test Core System** - Verify main workflow still works
6. **Test Frontend** - Verify Streamlit app still works
7. **Update Documentation** - Update README and docs

**Estimated time:** 2-3 hours
**Risk level:** Low (keeping all core functionality)
**Impact:** Significantly cleaner, more maintainable codebase
