#!/usr/bin/env python3
"""
Cross-platform startup script for Rush AI
Works on Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['flask', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} missing")
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
        print("✅ All dependencies installed")

def setup_database():
    """Initialize database if needed"""
    try:
        from database import knowledge_db
        stats = knowledge_db.get_statistics()
        print(f"✅ Database ready: {stats['total_knowledge']} knowledge items")
    except Exception as e:
        print(f"❌ Database error: {e}")
        sys.exit(1)

def start_app():
    """Start the Flask application"""
    print("\n🚀 Starting Rush AI...")
    print(f"📍 Platform: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    # Import and run the app
    try:
        from app import app
        
        # Get port from environment or use default
        port = int(os.environ.get('PORT', 5000))
        
        print(f"🌐 Server will start at: http://127.0.0.1:{port}")
        print("🎬 Rush AI Movie Recommendation System")
        print("=" * 50)
        
        # Start the Flask app
        app.run(
            host='127.0.0.1',
            port=port,
            debug=False,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down Rush AI...")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        sys.exit(1)

def main():
    """Main startup function"""
    print("🤖 Rush AI - Cross-Platform Startup")
    print("=" * 40)
    
    # Run checks
    check_python_version()
    check_dependencies()
    setup_database()
    
    # Start the application
    start_app()

if __name__ == "__main__":
    main()
