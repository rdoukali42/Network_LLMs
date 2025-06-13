# AI Chat System - Streamlit Frontend

A simple Streamlit-based chat interface for the AI workflow system.

## Files Structure

```
front/
├── app.py                    # Main Streamlit application entry point
├── auth.py                   # Authentication component
├── chat.py                   # Chat interface component  
├── workflow_client.py        # AI workflow client
├── streamlit_config.py       # App configuration
├── requirements_streamlit.txt # Streamlit dependencies
└── README.md                 # This file
```

## Setup

1. **Install Streamlit (if not already installed):**
   ```bash
   pip install streamlit>=1.28.0
   ```

2. **Ensure your environment is set up:**
   - Make sure your `.env` file contains `GOOGLE_API_KEY`
   - Ensure all main project dependencies are installed

## Quick Start

### Option 1: Use the start script
```bash
cd front
./start.sh
```

### Option 2: Manual start
```bash
cd front
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Login
- **Username**: `admin`, `user`, or `demo`
- **Password**: `admin123`, `user123`, or `demo` respectively

### Chat Interface
- Type your questions in the chat input
- The AI will process your query using the full workflow system
- Chat history is maintained during your session
- Use "Clear Chat History" to reset the conversation
- Click "Logout" to return to login screen

## Features

- ✅ User authentication with login/logout
- ✅ Real-time chat interface
- ✅ Integration with AI workflow system
- ✅ Chat history preservation
- ✅ Error handling and user feedback
- ✅ Modular component structure

## Security Note

The current authentication uses hardcoded credentials for demo purposes. In production, replace the `authenticate_user()` function in `auth.py` with proper authentication (database, OAuth, etc.).

## Troubleshooting

- **AI responses showing errors**: Check that `GOOGLE_API_KEY` is set in your `.env` file
- **Import errors**: Ensure you're running from the correct directory and all dependencies are installed
- **Connection issues**: Verify your internet connection and API key validity
