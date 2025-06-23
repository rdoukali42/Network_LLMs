"""
Add this to force reload the workflow module in Streamlit.
Put this at the top of your Streamlit app file.
"""

import importlib
import sys

# Force reload the workflow module to get the latest process_end_call method
if 'graphs.workflow' in sys.modules:
    importlib.reload(sys.modules['graphs.workflow'])
if 'src.graphs.workflow' in sys.modules:
    importlib.reload(sys.modules['src.graphs.workflow'])

print("🔄 STREAMLIT: Forced reload of workflow module to get latest methods")
