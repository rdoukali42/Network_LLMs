# Optimized AI Support Ticket System

This project is a refactored and optimized version of the original AI Support Ticket System.
The goal of this version is to provide the core application workflow with minimal code,
improved modularity, and enhanced configurability.

## Overview

The system provides a Streamlit-based frontend for users to:
- Register and authenticate.
- Create support tickets.
- View their tickets and responses.
- (If an employee) View and manage tickets assigned to them.
- (If an employee) Engage in voice calls for ticket resolution (simulated by AI playing the other party).

The backend consists of an AI system that:
- Processes new tickets using a multi-agent workflow (Maestro, DataGuardian, HRAgent, VocalAssistantAgent).
- Utilizes a vector store for document retrieval to answer queries.
- Assigns tickets to appropriate employees if direct answers are not found.
- Facilitates voice call handoff information.

## Structure

The project is organized into the following main directories:

-   `app/`: Contains the Streamlit frontend application code.
    -   `main_app.py`: The main entry point for the Streamlit application.
    -   Other files define UI components for auth, tickets, registration, etc.
-   `core/`: Houses the backend AI logic.
    -   `system.py`: Defines the main `AISystem` orchestrator.
    -   `agents/`: Contains definitions for individual AI agents.
    -   `tools/`: Contains tools used by the agents.
    -   `graph/`: Defines the LangGraph multi-agent workflow.
    -   `services/`: Contains services like `VoiceService` for STT/TTS.
    -   `models/`: Pydantic models for data structures.
-   `data_management/`: Handles data persistence.
    -   `database.py`: Manages the SQLite database for employee and call notification data.
    -   `ticket_store.py`: Manages tickets stored in a JSON file.
-   `config/`: Contains configuration files.
    -   `app_config.py`: Frontend UI configurations.
    -   `core_config.py`: Backend system and API key configuration loader.
    -   `*.yaml`: YAML configuration files for different environments.
-   `vectorstore/`: Manages the vector database for document similarity search.
-   `utils/`: Shared utility functions.
-   `data/`: Stores persistent data like the SQLite database, raw documents for the vector store, and ticket backups.
-   `static/`: Static assets for the frontend (e.g., images, audio files).

## Setup

1.  **Clone the repository.**
2.  **Create a Python virtual environment** (recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure API Keys and Environment:**
    *   Copy the `.env.example` file to a new file named `.env` in the `optimized_project` root directory:
        ```bash
        cp .env.example .env
        ```
    *   Edit the `.env` file and add your actual API keys (e.g., `GEMINI_API_KEY`).
    *   Review YAML configuration files in `optimized_project/config/` (e.g., `development.yaml`) for any other settings. The `core_config.py` will load API keys from the `.env` file or environment variables first.
5.  **Prepare Data (Optional but Recommended for Full Functionality):**
    *   Place any raw text or markdown documents you want the AI to be able to search into the `optimized_project/data/raw/` directory. The `AISystem` will load these into the vector store on its first run. A `company_scope.md` is particularly useful for the DataGuardianAgent.
    *   The SQLite database (`employees.db`) and `tickets.json` file will be created automatically in `optimized_project/data/databases/` and `optimized_project/data_management/` respectively if they don't exist.

## Running the Application

Navigate to the `optimized_project` root directory in your terminal and run:

```bash
streamlit run app/main_app.py
```

The application should then be accessible in your web browser (usually at `http://localhost:8501`).

## Key Changes from Original Project

-   **Modularity:** Code has been reorganized into distinct layers (app, core, data_management, config, etc.) to improve separation of concerns and maintainability.
-   **Minimalism:** Focus on the core workflow. Unused files (like `front/vocale.py`) and non-essential functions/fallbacks (like the `MultiAgentWorkflow.run()` error fallback) have been removed.
-   **Configuration:** Centralized configuration for both frontend and backend. API keys are managed via `.env` and `core_config.py`, removing hardcoded keys.
-   **Pathing:** Paths are generally relative to the `optimized_project` root or dynamically determined.
-   **CalculatorTool Removed:** As per request, this tool is no longer part of the system.

This refactored version aims to be a cleaner and more adaptable foundation.
Further enhancements in terms of error handling, testing, and specific feature refinements can be built upon this structure.
