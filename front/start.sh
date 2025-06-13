#!/bin/bash
# Quick start script for the Streamlit app

echo "🚀 Starting AI Chat System"
echo "=========================="

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Please run this script from the front/ directory"
    exit 1
fi

# Activate virtual environment if it exists
if [ -f "../venv/bin/activate" ]; then
    echo "🔧 Activating virtual environment..."
    source ../venv/bin/activate
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip install "streamlit>=1.28.0"
fi

# Check environment
if [ ! -f "../.env" ]; then
    echo "⚠️  Warning: .env file not found. Make sure to set GOOGLE_API_KEY"
fi

echo "✅ Starting Streamlit app..."
echo "📝 Login credentials: admin:admin123, user:user123, demo:demo"
echo "🌐 App will open at: http://localhost:8501"
echo ""

python -m streamlit run app.py
