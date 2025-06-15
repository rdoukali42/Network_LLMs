# AI Project with Langchain and LangGraph

This project implements a multi-agent AI system using Langchain, LangGraph, LangFuse, and other modern LLM infrastructure tools.

## Project Structure

```
├── src/                    # Main source code
│   ├── agents/            # AI agent implementations
│   ├── tools/             # Custom tools for agents
│   ├── chains/            # Langchain chains
│   ├── graphs/            # LangGraph workflows
│   ├── retrievers/        # Custom retriever implementations
│   ├── vectorstore/       # Vector database management
│   ├── evaluation/        # LLM-based evaluation system
│   ├── config/            # Configuration management
│   └── utils/             # Utility functions
├── data/                  # Data storage
│   ├── raw/              # Raw input data
│   ├── processed/        # Processed data
│   └── embeddings/       # Vector embeddings
├── tests/                 # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── evaluation/       # Evaluation tests
├── configs/               # Configuration files
│   ├── development.yaml  # Development settings
│   ├── production.yaml   # Production settings
│   └── experiments/      # Experimental configurations
└── notebooks/             # Jupyter notebooks for experimentation
```

## Features

- **Multi-Agent System**: Research and Analysis agents working together
- **Vector Store Integration**: ChromaDB for semantic search
- **Custom Retrievers**: Hybrid and contextual retrieval strategies
- **LangGraph Workflows**: Complex multi-step processing
- **LLM-based Evaluation**: Automated quality assessment
- **Experiment Management**: A/B testing different configurations
- **LangFuse Integration**: Comprehensive logging and observability

## Setup

1. **Clone and Setup Environment**:
   ```bash
   cd /path/to/project
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Required API Keys**:
   - Google API key (for Gemini Flash 1.5)
   - OpenAI API key (optional, for comparison)
   - Anthropic API key (optional)
   - LangFuse public and secret keys

## Usage

### Basic Usage

```python
from src.main import AISystem

# Initialize the system
system = AISystem()

# Process a query
result = system.process_query("What is artificial intelligence?")
print(result)
```

### Running Experiments

```python
# Run an experiment with specific configuration
test_queries = [
    "What is machine learning?",
    "How does AI work?",
    "What are neural networks?"
]

experiment_results = system.run_experiment("experiment_1", test_queries)
```

### Configuration Management

The system supports multiple configurations:

- `development.yaml`: For development work
- `production.yaml`: For production deployment
- `experiments/`: For A/B testing different parameters

## Components

### Agents
- **MaestroAgent**: Specializes in query preprocessing and response synthesis
- **DataGuardianAgent**: Focuses on local document search and data verification

### Tools
- **DocumentAnalysisTool**: Analyze documents for insights
- **CalculatorTool**: Perform mathematical calculations

### Evaluation
- **LLMEvaluator**: Uses GPT-4 to evaluate response quality
- **Metrics**: Relevance, accuracy, completeness, efficiency
- **A/B Testing**: Compare different configurations

## Testing

Run the test suite:

```bash
# Unit tests
python -m pytest tests/unit/ -v

# Integration tests
python -m pytest tests/integration/ -v

# Evaluation tests
python -m pytest tests/evaluation/ -v

# All tests
python -m pytest tests/ -v
```

## Development

### Adding New Agents

1. Create a new agent class inheriting from `BaseAgent`
2. Implement the `run()` and `get_system_prompt()` methods
3. Add the agent to the workflow in `main.py`

### Adding New Tools

1. Create a tool class inheriting from `BaseTool`
2. Implement the `_run()` method
3. Add the tool to agents in the initialization

### Configuration

Modify `configs/development.yaml` or create new experiment configurations in `configs/experiments/`.

## Roadmap

- [ ] Add more specialized agents
- [ ] Implement advanced retrieval strategies
- [ ] Add support for different LLM providers
- [ ] Create web interface
- [ ] Add real-time evaluation dashboard

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

This project is for educational purposes only.
