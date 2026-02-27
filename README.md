# AI-Powered Support Ticket System

> **Arkadia LEVEL3 Program**
> This project was developed as part of the **Arkadia LEVEL3 AI Track**.
> Not intended for production use as-is.

A multi-agent AI support system built with LangChain, LangGraph, and Google Gemini. Resolves queries via RAG when documentation exists, and escalates to the right human expert with a voice call interface when it does not. A Streamlit frontend handles auth, ticket lifecycle, and real-time status tracking.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Query                           │
└────────────────────────┬────────────────────────────────────┘
                         ↓
                  ┌──────────────┐
                  │ MaestroAgent │  (Orchestration)
                  └──────┬───────┘
                         ↓
              ┌──────────────────────┐
              │ DataGuardianAgent    │  (RAG / Document Retrieval)
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
         ┌─────────┐  │ VocalAssistant   │  (Voice Call + Transcription)
         │ Return  │  └────┬─────────────┘
         │ to User │       ↓
         └─────────┘  ┌──────────────────┐
                      │ Solution Generated│
                      └────┬──────────────┘
                           ↓
                      Return to User
```

## Project Structure

```
ticket_system/
├── src/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── maestro_agent.py
│   │   ├── data_guardian_agent.py
│   │   ├── hr_agent.py
│   │   └── vocal_assistant.py
│   ├── tools/
│   │   ├── availability_tool.py
│   │   └── custom_tools.py
│   ├── graphs/                   # LangGraph workflows
│   ├── retrievers/               # RAG retrieval logic
│   ├── vectorstore/              # ChromaDB management
│   ├── evaluation/
│   ├── config/
│   └── utils/
├── front/
│   ├── app.py                   # Streamlit entry point
│   ├── auth.py
│   ├── database.py
│   └── tickets/
│       ├── ticket_manager.py
│       ├── ticket_forms.py
│       ├── ticket_processing.py
│       ├── call_interface.py
│       └── availability.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── system/
├── configs/
│   ├── development.yaml
│   └── production.yaml
├── data/
│   ├── raw/                     # Company documents (for RAG)
│   └── databases/               # SQLite
└── requirements.txt
```

## How to Run

```bash
# Clone and set up environment
git clone https://github.com/rdoukali42/Network_LLMs.git
cd Network_LLMs
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Set up environment variables:

```bash
cp .env.example .env
# Add your GOOGLE_API_KEY and optionally LANGFUSE keys
```

```bash
# Initialize data directories
mkdir -p data/databases data/backups data/raw

# Start the app
streamlit run front/app.py
```

App runs at `http://localhost:8501`. Default test credentials: `admin / admin123`.

### Configuration

Edit `configs/development.yaml` to tune model, vector store, and agent settings:

```yaml
model:
  provider: "google"
  name: "gemini-1.5-flash"
  temperature: 0.7

vectorstore:
  type: "chroma"
  persist_directory: "data/chroma_db"

agents:
  maestro:
    enabled: true
    max_iterations: 5
  data_guardian:
    enabled: true
    top_k: 5
```

---

**Reda Doukali**
[github.com/rdoukali42](https://github.com/rdoukali42) | [linkedin.com/in/reda-doukali](https://linkedin.com/in/reda-doukali)
