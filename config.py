import os
# from dotenv import load_dotenv

# load_dotenv()  # Not needed in Vercel environment

class Config:
    # TMDB Configuration
    TMDB_API_KEY = os.getenv('TMDB_API_KEY', 'b2f549238e90b6a7593d30ad0d53021c')
    TMDB_BASE_URL = 'https://api.themoviedb.org/3'
    
    # Ollama Configuration
    OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
    
    # AI Provider Configuration
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'custom')  # Use custom API for free access
    
    # Free AI API (Groq - fast and free)
    CUSTOM_API_KEY = os.getenv('CUSTOM_API_KEY', 'gsk_YourGroqAPIKeyHere')
    CUSTOM_BASE_URL = os.getenv('CUSTOM_BASE_URL', 'https://api.groq.com/openai/v1')
    CUSTOM_MODEL = os.getenv('CUSTOM_MODEL', 'llama-3.1-8b-instant')
    
    # OpenAI Configuration (optional)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    
    # Anthropic Configuration (optional)
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307')
    
    # Google AI Configuration (optional)
    GOOGLE_AI_API_KEY = os.getenv('GOOGLE_AI_API_KEY', '')
    GOOGLE_AI_MODEL = os.getenv('GOOGLE_AI_MODEL', 'gemini-pro')
    
    # Custom AI Configuration (Groq - Free AI API)
    CUSTOM_API_KEY = os.getenv('CUSTOM_API_KEY', 'gsk_YourGroqAPIKeyHere')
    CUSTOM_BASE_URL = os.getenv('CUSTOM_BASE_URL', 'https://api.groq.com/openai/v1')
    CUSTOM_MODEL = os.getenv('CUSTOM_MODEL', 'llama3-8b-8192')
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'rush-ai-movie-pro-secret-key-2025')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
