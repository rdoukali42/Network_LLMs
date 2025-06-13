# AI Support Ticket System - Streamlit Frontend

A modern Streamlit-based support ticket interface that integrates with the AI workflow system to provide intelligent, automated responses to user support requests.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Streamlit
- Main AI workflow system dependencies
- Valid `GOOGLE_API_KEY` in `.env` file

### Installation & Launch
```bash
cd front
streamlit run app.py
```

**Default Login Credentials:**
- Username: `admin` | Password: `admin123`
- Username: `user` | Password: `user123`  
- Username: `demo` | Password: `demo`

**Access:** Open http://localhost:8501 in your browser

## 🎫 Features

### Support Ticket System
- **Create Tickets**: Submit detailed support requests with categorization and prioritization
- **AI Processing**: Automatic analysis and response generation using the main AI workflow
- **Status Tracking**: Monitor ticket progress from submission to AI response
- **User Isolation**: Each user sees only their own tickets
- **Analytics Dashboard**: Overview of ticket statistics and trends

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

### Support Ticket System
Once logged in, you can:

1. **Create Tickets**: Submit support requests with categorization and priority levels
2. **Track Status**: Monitor your tickets and view AI-generated responses  
3. **View Analytics**: See overview of your ticket history and statistics

#### Ticket Categories:
- Technical Issue
- Feature Request
- Bug Report
- General Question
- Account Issue

#### Priority Levels:
- Low, Medium, High, Critical
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
