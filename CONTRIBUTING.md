# Contributing to AI-Powered Support Ticket System

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)

---

## 📜 Code of Conduct

### Our Standards

- **Be respectful** and inclusive
- **Be constructive** in feedback
- **Be professional** in all interactions
- **Focus on what's best** for the project and community

---

## 🚀 Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/ticket_system.git
cd ticket_system
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install black flake8 mypy pre-commit pytest-cov

# Set up pre-commit hooks
pre-commit install
```

### 3. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

---

## 🔄 Development Workflow

### 1. Make Your Changes

- Write clean, readable code
- Follow existing code style and patterns
- Add comments for complex logic
- Update docstrings as needed

### 2. Test Your Changes

```bash
# Run all tests
pytest tests/ -v

# Run specific test category
pytest tests/unit/ -v

# Run with coverage
pytest tests/ --cov=src --cov=front --cov-report=html
```

### 3. Format and Lint

```bash
# Format code with Black
black src/ front/ tests/

# Check with flake8
flake8 src/ front/ tests/ --max-line-length=100

# Type check (optional)
mypy src/
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: Add new feature description"
```

---

## 📝 Coding Standards

### Python Style Guide

- Follow **PEP 8** guidelines
- Use **Black** for code formatting (line length: 100)
- Use **type hints** where applicable
- Write **docstrings** for all public functions and classes

### Docstring Format

```python
def process_ticket(ticket_id: str, priority: str = "medium") -> dict:
    """
    Process a support ticket through the AI workflow.
    
    Args:
        ticket_id: Unique identifier for the ticket
        priority: Priority level (low, medium, high)
    
    Returns:
        Dictionary containing processing results with keys:
        - status: Processing status
        - response: Generated response
        - assigned_to: Assigned employee (if escalated)
    
    Raises:
        ValueError: If ticket_id is invalid
        TicketProcessingError: If processing fails
    
    Example:
        >>> result = process_ticket("TKT-001", priority="high")
        >>> print(result['status'])
        'solved'
    """
    # Implementation
    pass
```

### Code Organization

- **One class per file** for major components
- **Group related functions** in modules
- **Keep functions small** (< 50 lines ideally)
- **Use meaningful names** (descriptive, not abbreviated)

### Import Order

```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import streamlit as st
from langchain import LLMChain

# Local application imports
from src.agents.base_agent import BaseAgent
from src.utils.helpers import format_response
```

---

## 🧪 Testing Guidelines

### Test Structure

```python
import pytest
from src.agents.maestro_agent import MaestroAgent

class TestMaestroAgent:
    """Test suite for MaestroAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create a MaestroAgent instance for testing."""
        config = {"model": "gemini-1.5-flash"}
        return MaestroAgent(config)
    
    def test_process_query_success(self, agent):
        """Test successful query processing."""
        result = agent.process("How do I reset my password?")
        assert result is not None
        assert "response" in result
    
    def test_process_query_empty_input(self, agent):
        """Test handling of empty input."""
        with pytest.raises(ValueError):
            agent.process("")
```

### Test Coverage

- Aim for **80%+ code coverage**
- Write tests for:
  - Happy path scenarios
  - Edge cases
  - Error conditions
  - Input validation

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific file
pytest tests/unit/test_maestro_agent.py -v

# With coverage
pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 📝 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples

```bash
# Feature
git commit -m "feat(agents): Add new DataGuardianAgent for document retrieval"

# Bug fix
git commit -m "fix(ticket): Resolve ticket assignment race condition"

# Documentation
git commit -m "docs(readme): Update installation instructions"

# Refactor
git commit -m "refactor(database): Simplify employee query logic"
```

---

## 🔍 Pull Request Process

### 1. Before Submitting

✅ **Checklist:**
- [ ] Code follows project style guidelines
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] No merge conflicts
- [ ] Commits are well-formed and descriptive

### 2. PR Template

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Closes #123
```

### 3. Review Process

1. **Automated checks** must pass (tests, linting)
2. **Code review** by at least one maintainer
3. **Address feedback** promptly
4. **Squash commits** if requested
5. **Merge** after approval

### 4. After Merge

- Delete your branch (if no longer needed)
- Update your local repository
- Close related issues

---

## 🎯 Areas for Contribution

### High Priority

- **Testing**: Improve test coverage
- **Documentation**: API docs, tutorials, examples
- **Bug fixes**: Check the issues page
- **Performance**: Optimize slow operations

### Feature Ideas

- Additional AI agents
- New integration tools
- Enhanced UI/UX
- Multilingual support
- Advanced analytics dashboard

### Documentation Needs

- Video tutorials
- Use case examples
- API documentation
- Deployment guides

---

## 📞 Getting Help

### Questions?

- **GitHub Issues**: For bug reports and feature requests
- **Discussions**: For general questions and ideas
- **Email**: For private inquiries

### Resources

- [README.md](README.md) - Project overview
- [docs/architecture/](docs/architecture/) - System architecture
- [tests/](tests/) - Test examples

---

## 🏆 Recognition

Contributors will be:
- Added to CONTRIBUTORS.md
- Mentioned in release notes
- Acknowledged in the project README

Thank you for contributing! 🎉

---

**Happy Coding!** 💻
