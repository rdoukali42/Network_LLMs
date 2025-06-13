#!/usr/bin/env python3
"""
Setup script for the AI project.
Initializes the project with sample data and configurations.
"""

import os
import sys
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from src.utils.helpers import load_sample_data, ensure_directory_exists
from src.config.config_loader import config_loader


def setup_project():
    """Setup the project with initial data and configurations."""
    print("🚀 Setting up AI Project...")
    
    # Ensure all directories exist
    directories = [
        "data/raw",
        "data/processed", 
        "data/embeddings",
        "data/chroma_db",
        "data/experiments",
        "logs"
    ]
    
    for directory in directories:
        ensure_directory_exists(directory)
        print(f"✅ Created directory: {directory}")
    
    # Create sample data files
    sample_docs = load_sample_data()
    
    for i, doc in enumerate(sample_docs, 1):
        file_path = f"data/raw/sample_doc_{i}.txt"
        with open(file_path, 'w') as f:
            f.write(doc.strip())
        print(f"✅ Created sample document: {file_path}")
    
    # Test configuration loading
    try:
        config = config_loader.load_config("development")
        print("✅ Configuration system working")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
    
    # Create environment file if it doesn't exist
    env_file = ".env"
    if not os.path.exists(env_file):
        # Copy from example
        with open(".env.example", 'r') as src:
            content = src.read()
        
        with open(env_file, 'w') as dst:
            dst.write(content)
        
        print(f"✅ Created {env_file} from template")
        print("⚠️  Please edit .env with your actual API keys")
    
    print("\n🎉 Project setup complete!")
    print("\nNext steps:")
    print("1. Edit .env with your API keys")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run tests: python -m pytest tests/")
    print("4. Start experimenting with notebooks/")


if __name__ == "__main__":
    setup_project()
