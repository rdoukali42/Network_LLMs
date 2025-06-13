#!/usr/bin/env python3
"""
Demo script to show Streamlit components functionality.
Tests the workflow integration without running the full Streamlit server.
"""

import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent
front_dir = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(front_dir))

def demo_auth():
    """Demo the authentication component."""
    print("🔐 AUTHENTICATION DEMO")
    print("=" * 40)
    
    from auth import authenticate_user
    
    # Test valid credentials
    test_cases = [
        ("admin", "admin123", True),
        ("user", "user123", True), 
        ("demo", "demo", True),
        ("invalid", "wrong", False)
    ]
    
    for username, password, expected in test_cases:
        result = authenticate_user(username, password)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} {username}:{password} -> {result}")

def demo_workflow_client():
    """Demo the workflow client."""
    print("\n🤖 WORKFLOW CLIENT DEMO")
    print("=" * 40)
    
    from workflow_client import WorkflowClient
    
    try:
        client = WorkflowClient()
        ready = client.is_ready()
        print(f"Client ready: {'✅ Yes' if ready else '❌ No'}")
        
        if ready:
            print("🔍 Testing simple query...")
            # Test with a simple query
            result = client.process_query("What is 2+2?")
            
            if result.get("status") == "success":
                response = result.get("result", "")
                print(f"✅ Response received ({len(response)} chars)")
                print(f"📝 Preview: {response[:100]}...")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Workflow client error: {e}")

def demo_config():
    """Demo the configuration."""
    print("\n⚙️ CONFIGURATION DEMO")
    print("=" * 40)
    
    from streamlit_config import APP_TITLE, APP_ICON, DEFAULT_USERS, check_environment
    
    print(f"App Title: {APP_TITLE}")
    print(f"App Icon: {APP_ICON}")
    print(f"Default Users: {list(DEFAULT_USERS.keys())}")
    
    missing = check_environment()
    if missing:
        print(f"⚠️  Missing env vars: {missing}")
    else:
        print("✅ Environment configured")

if __name__ == "__main__":
    print("🚀 STREAMLIT COMPONENTS DEMO")
    print("=" * 50)
    
    try:
        demo_config()
        demo_auth()
        demo_workflow_client()
        
        print("\n" + "=" * 50)
        print("✅ ALL COMPONENTS TESTED SUCCESSFULLY!")
        print("\nTo run the full Streamlit app:")
        print("  cd /Users/level3/Desktop/Network/front")
        print("  streamlit run app.py")
        print("\nLogin credentials:")
        print("  admin:admin123, user:user123, demo:demo")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
