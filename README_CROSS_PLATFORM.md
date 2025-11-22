# Rush AI - Cross-Platform Deployment Guide

## 🌍 Platform Support

Rush AI is designed to work seamlessly across all major platforms:

- ✅ **Windows 10/11**
- ✅ **macOS 10.14+**
- ✅ **Linux (Ubuntu, CentOS, Debian)**
- ✅ **Docker containers**

## 🚀 Quick Start (Any Platform)

### Method 1: Using the Startup Script (Recommended)

```bash
# Clone or download the project
cd Rush

# Run the cross-platform startup script
python run.py
```

The startup script will:
- Check Python version compatibility
- Install missing dependencies automatically
- Initialize the database
- Start the server at `http://127.0.0.1:5000`

### Method 2: Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python app.py
```

## 📋 System Requirements

### Minimum Requirements
- **Python**: 3.7 or higher
- **Memory**: 512MB RAM
- **Storage**: 100MB free space
- **Network**: Internet connection for movie data

### Recommended Requirements
- **Python**: 3.9 or higher
- **Memory**: 1GB RAM
- **Storage**: 1GB free space
- **Network**: Broadband connection

## 🛠️ Platform-Specific Instructions

### Windows

#### Option 1: Command Prompt
```cmd
cd Rush
python run.py
```

#### Option 2: PowerShell
```powershell
cd Rush
python run.py
```

#### Option 3: Using Python Launcher
```cmd
py run.py
```

### macOS

#### Option 1: Terminal
```bash
cd Rush
python3 run.py
```

#### Option 2: Using Homebrew Python
```bash
brew install python3
cd Rush
python3 run.py
```

### Linux

#### Ubuntu/Debian
```bash
# Install Python if needed
sudo apt update
sudo apt install python3 python3-pip

# Run the application
cd Rush
python3 run.py
```

#### CentOS/RHEL
```bash
# Install Python if needed
sudo yum install python3 python3-pip

# Run the application
cd Rush
python3 run.py
```

## 🐳 Docker Deployment

### Build Docker Image
```bash
docker build -t rush-ai .
```

### Run Container
```bash
docker run -p 5000:5000 rush-ai
```

### Docker Compose
```yaml
version: '3.8'
services:
  rush-ai:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./knowledge.db:/app/knowledge.db
```

## 🔧 Configuration

### Environment Variables
```bash
# Server port (default: 5000)
export PORT=5000

# Flask environment (development/production)
export FLASK_ENV=production

# API Keys (set in .env file)
TMDB_API_KEY=your_tmdb_key_here
```

### Database Location
The database (`knowledge.db`) is automatically created in the project directory and works across all platforms.

## 🌐 Network Configuration

### Local Development
- Access at: `http://127.0.0.1:5000`
- Network access: `http://YOUR_IP:5000`

### Production Deployment
- Use reverse proxy (nginx/Apache)
- Configure firewall rules
- Set up SSL certificates

## 📱 Mobile Access

Once running, Rush AI is accessible from any device on the same network:
- **Phone/Tablet**: `http://YOUR_COMPUTER_IP:5000`
- **Smart TV**: Browser access to web interface
- **Other devices**: Any modern web browser

## 🔍 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Kill process on port 5000 (Linux/macOS)
sudo lsof -ti:5000 | xargs kill

# Kill process on port 5000 (Windows)
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

#### Python Version Issues
```bash
# Check Python version
python --version
python3 --version

# Install correct Python version
# Windows: Download from python.org
# macOS: brew install python3
# Linux: sudo apt install python3
```

#### Permission Issues (Linux/macOS)
```bash
# Make script executable
chmod +x run.py

# Run with proper permissions
sudo python3 run.py
```

#### Database Lock Issues
```bash
# Remove lock file (if exists)
rm -f knowledge.db-journal
```

## 🚀 Performance Optimization

### Production Settings
- Use WSGI server (Gunicorn/uWSGI)
- Enable database caching
- Configure reverse proxy
- Monitor system resources

### Database Optimization
- Regular database cleanup
- Index optimization
- Backup strategies

## 📞 Support

### Platform-Specific Help
- **Windows**: Check Windows Defender/Firewall settings
- **macOS**: Ensure Gatekeeper allows Python execution
- **Linux**: Check SELinux/AppArmor permissions

### Community Support
- GitHub Issues: Report platform-specific bugs
- Documentation: Check platform-specific guides
- Community Forums: Get help from other users

---

**🎬 Rush AI works everywhere you do!**

Whether you're on Windows, macOS, or Linux, Rush AI provides the same great movie recommendation experience across all platforms.
