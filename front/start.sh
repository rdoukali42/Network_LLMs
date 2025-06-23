#!/bin/bash
# Start the Streamlit application

# Navigate to the front directory
cd "$(dirname "$0")"

# Start Streamlit
streamlit run app.py --server.port 8501
