from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime
import os
from config import Config
from models import api_key_manager

app = Flask(__name__)
app.config.from_object(Config)

class TMDBService:
    @staticmethod
    def search_movies(query, page=1):
        """Search for movies by title"""
        url = f"{app.config['TMDB_BASE_URL']}/search/movie"
        params = {
            'api_key': app.config['TMDB_API_KEY'],
            'query': query,
            'page': page
        }
        response = requests.get(url, params=params)
        return response.json()
    
    @staticmethod
    def get_movie_details(movie_id):
        """Get detailed information about a specific movie"""
        url = f"{app.config['TMDB_BASE_URL']}/movie/{movie_id}"
        params = {
            'api_key': app.config['TMDB_API_KEY'],
            'append_to_response': 'credits,videos,images'
        }
        response = requests.get(url, params=params)
        return response.json()
    
    @staticmethod
    def search_people(query, page=1):
        """Search for actors/celebrities by name"""
        url = f"{app.config['TMDB_BASE_URL']}/search/person"
        params = {
            'api_key': app.config['TMDB_API_KEY'],
            'query': query,
            'page': page
        }
        response = requests.get(url, params=params)
        return response.json()
    
    @staticmethod
    def get_person_details(person_id):
        """Get detailed information about a specific person"""
        url = f"{app.config['TMDB_BASE_URL']}/person/{person_id}"
        params = {
            'api_key': app.config['TMDB_API_KEY'],
            'append_to_response': 'movie_credits,images'
        }
        response = requests.get(url, params=params)
        return response.json()
    
    @staticmethod
    def get_popular_movies(page=1):
        """Get popular movies"""
        url = f"{app.config['TMDB_BASE_URL']}/movie/popular"
        params = {
            'api_key': app.config['TMDB_API_KEY'],
            'page': page
        }
        response = requests.get(url, params=params)
        return response.json()
    
    @staticmethod
    def get_trending_movies(time_window='day'):
        """Get trending movies (day or week)"""
        url = f"{app.config['TMDB_BASE_URL']}/trending/movie/{time_window}"
        params = {
            'api_key': app.config['TMDB_API_KEY']
        }
        response = requests.get(url, params=params)
        return response.json()

class AIService:
    def __init__(self):
        self.shared_knowledge = {}  # Store shared knowledge
    
    @staticmethod
    def get_instance():
        """Get singleton instance"""
        if not hasattr(AIService, '_instance'):
            AIService._instance = AIService()
        return AIService._instance
    
    @staticmethod
    def get_provider():
        """Get the current AI provider from configuration"""
        return app.config.get('AI_PROVIDER', 'ollama')
    
    def add_shared_knowledge(self, question, answer, api_key=None):
        """Add knowledge to the shared pool"""
        knowledge_id = hashlib.md5(f"{question}_{answer}".encode()).hexdigest()
        self.shared_knowledge[knowledge_id] = {
            'question': question,
            'answer': answer,
            'api_key': api_key,
            'timestamp': datetime.utcnow().isoformat(),
            'uses': 0
        }
    
    def get_shared_knowledge(self, question):
        """Get relevant knowledge from shared pool"""
        relevant = []
        for kid, knowledge in self.shared_knowledge.items():
            if any(word.lower() in knowledge['question'].lower() for word in question.lower().split() if len(word) > 3):
                knowledge['uses'] += 1
                relevant.append(knowledge['answer'])
        return relevant
    
    def generate_response(self, prompt, context="", api_key=None):
        """Generate AI response using the configured provider with shared knowledge"""
        try:
            provider = self.get_provider()
            
            # Check shared knowledge first
            shared_answers = self.get_shared_knowledge(prompt)
            
            if provider == 'openai':
                response = self._generate_openai_response(prompt, context, shared_answers)
            elif provider == 'anthropic':
                response = self._generate_anthropic_response(prompt, context, shared_answers)
            elif provider == 'google':
                response = self._generate_google_response(prompt, context, shared_answers)
            elif provider == 'custom':
                response = self._generate_custom_response(prompt, context, shared_answers)
            else:
                response = self._generate_ollama_response(prompt, context, shared_answers)
            
            # Add good responses to shared knowledge
            if api_key and len(response) > 50 and "Error" not in response:
                self.add_shared_knowledge(prompt, response, api_key)
            
            return response
            
        except Exception as e:
            return f"AI Error: {str(e)}"
    
    def _generate_ollama_response(self, prompt, context="", shared_answers=[]):
        """Generate response using Ollama"""
        # Add shared knowledge to context
        knowledge_context = ""
        if shared_answers:
            knowledge_context = f"\n\nShared Knowledge from previous similar questions:\n" + "\n".join([f"- {answer}" for answer in shared_answers[:3]])
        
        system_prompt = f"""You are Rush, a movie expert AI. Help with movie recommendations, actor info, and film insights. Be concise and helpful.
        You can generate movie poster descriptions and provide social media information when available.
        Context: {context}{knowledge_context}
        """
        
        full_prompt = f"{system_prompt}\n\nUser: {prompt}\nAssistant:"
        
        payload = {
            "model": app.config.get('OLLAMA_MODEL', 'llama3.2:3b'),
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "max_tokens": 150,
                "num_predict": 150,
                "num_ctx": 512
            }
        }
        
        response = requests.post(app.config.get('OLLAMA_API_URL'), json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            return result.get('response', 'Sorry, I could not generate a response.')
        else:
            return f"Ollama API error: {response.status_code}"
    
    def _generate_openai_response(self, prompt, context="", shared_answers=[]):
        """Generate response using OpenAI"""
        if not app.config.get('OPENAI_API_KEY'):
            return "OpenAI API key not configured"
        
        system_prompt = f"""You are Rush, a movie expert AI. Help with movie recommendations, actor info, and film insights. Be concise and helpful.
        You can generate movie poster descriptions and provide social media information when available.
        Context: {context}"""
        
        headers = {
            'Authorization': f'Bearer {app.config["OPENAI_API_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        response = requests.post(f"{app.config['OPENAI_BASE_URL']}/chat/completions", 
                               headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            return f"OpenAI API error: {response.status_code}"
    
    def _generate_anthropic_response(self, prompt, context="", shared_answers=[]):
        """Generate response using Anthropic Claude"""
        if not app.config.get('ANTHROPIC_API_KEY'):
            return "Anthropic API key not configured"
        
        system_prompt = f"""You are Rush, a movie expert AI. Help with movie recommendations, actor info, and film insights. Be concise and helpful.
        You can generate movie poster descriptions and provide social media information when available.
        Context: {context}"""
        
        headers = {
            'x-api-key': app.config['ANTHROPIC_API_KEY'],
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        payload = {
            "model": app.config.get('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            "max_tokens": 300,
            "temperature": 0.7,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post('https://api.anthropic.com/v1/messages', 
                               headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['content'][0]['text']
        else:
            return f"Anthropic API error: {response.status_code}"
    
    def _generate_google_response(self, prompt, context="", shared_answers=[]):
        """Generate response using Google AI"""
        if not app.config.get('GOOGLE_AI_API_KEY'):
            return "Google AI API key not configured"
        
        system_prompt = f"""You are Rush, a movie expert AI. Help with movie recommendations, actor info, and film insights. Be concise and helpful.
        You can generate movie poster descriptions and provide social media information when available.
        Context: {context}"""
        
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_prompt}\n\nUser: {prompt}"
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 300
            }
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{app.config.get('GOOGLE_AI_MODEL', 'gemini-pro')}:generateContent?key={app.config['GOOGLE_AI_API_KEY']}"
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Google AI API error: {response.status_code}"
    
    def _generate_custom_response(self, prompt, context="", shared_answers=[]):
        """Generate response using custom API"""
        if not app.config.get('CUSTOM_API_KEY') or app.config.get('CUSTOM_API_KEY') == 'gsk_YourGroqAPIKeyHere' or not app.config.get('CUSTOM_API_KEY').startswith('gsk_'):
            # Fallback response when no API key is configured
            return f"I'm Rush AI! I can help you find movies and celebrities. Try searching for movies like 'Avatar' or people like 'Tom Cruise'. For personalized AI responses, configure a Groq API key in your settings. Your question was: {prompt[:100]}..."
        
        system_prompt = f"""You are Rush, a movie expert AI. Help with movie recommendations, actor info, and film insights. Be concise and helpful.
        You can generate movie poster descriptions and provide social media information when available.
        Context: {context}"""
        
        headers = {
            'Authorization': f'Bearer {app.config["CUSTOM_API_KEY"]}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": app.config.get('CUSTOM_MODEL', 'custom-model'),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 300,
            "temperature": 0.7
        }
        
        response = requests.post(f"{app.config['CUSTOM_BASE_URL']}/chat/completions", 
                               headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            try:
                result = response.json()
                return result['choices'][0]['message']['content']
            except (KeyError, IndexError, ValueError) as e:
                return f"Custom API response error: Invalid response format"
        else:
            return f"Custom API error: {response.status_code} - {response.text[:100]}"

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/search/movies')
def api_search_movies():
    """API endpoint for movie search"""
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    result = TMDBService.search_movies(query, page)
    return jsonify(result)

@app.route('/api/movie/<int:movie_id>')
def api_movie_details(movie_id):
    """API endpoint for movie details"""
    result = TMDBService.get_movie_details(movie_id)
    return jsonify(result)

@app.route('/api/search/people')
def api_search_people():
    """API endpoint for people search"""
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    
    if not query:
        return jsonify({'error': 'Query parameter is required'}), 400
    
    result = TMDBService.search_people(query, page)
    return jsonify(result)

@app.route('/api/person/<int:person_id>')
def api_person_details(person_id):
    """API endpoint for person details"""
    result = TMDBService.get_person_details(person_id)
    return jsonify(result)

@app.route('/api/popular/movies')
def api_popular_movies():
    """API endpoint for popular movies"""
    page = int(request.args.get('page', 1))
    result = TMDBService.get_popular_movies(page)
    return jsonify(result)

@app.route('/api/trending/movies')
def api_trending_movies():
    """API endpoint for trending movies"""
    time_window = request.args.get('window', 'day')
    result = TMDBService.get_trending_movies(time_window)
    return jsonify(result)

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """API endpoint for AI chat"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    message = data['message']
    context = data.get('context', '')
    
    ai_service = AIService.get_instance()
    response = ai_service.generate_response(message, context)
    return jsonify({'response': response})

@app.route('/api/generate', methods=['POST'])
def api_generate_content():
    """API endpoint for AI-generated content"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data received'}), 400
        
        if 'type' not in data or 'query' not in data:
            return jsonify({'error': 'Type and query are required'}), 400
        
        content_type = data['type']
        query = data['query']
        
        if content_type == 'poster':
            prompt = f"Generate a creative and detailed movie poster description for: {query}. Include visual elements, color scheme, mood, and tagline."
        elif content_type == 'social':
            prompt = f"Provide social media information and web presence for: {query}. Include Instagram, Twitter, official website if available."
        else:
            prompt = query
        
        ai_service = AIService.get_instance()
        response = ai_service.generate_response(prompt)
        return jsonify({'response': response, 'type': content_type})
    
    except Exception as e:
        print(f"Error in generate API: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/dev')
def dev_page():
    """Developer configuration page"""
    return render_template('dev.html')

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """Get or update AI configuration"""
    if request.method == 'GET':
        return jsonify({
            'ai_provider': app.config.get('AI_PROVIDER', 'ollama'),
            'ollama_url': app.config.get('OLLAMA_API_URL'),
            'ollama_model': app.config.get('OLLAMA_MODEL'),
            'openai_model': app.config.get('OPENAI_MODEL'),
            'anthropic_model': app.config.get('ANTHROPIC_MODEL'),
            'google_model': app.config.get('GOOGLE_AI_MODEL'),
            'status': 'configured',
            'current_model': AIService.get_provider()
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Update app configuration
            if 'ai_provider' in data:
                app.config['AI_PROVIDER'] = data['ai_provider']
            
            if 'ollama_url' in data:
                app.config['OLLAMA_API_URL'] = data['ollama_url']
            
            if 'ollama_model' in data:
                app.config['OLLAMA_MODEL'] = data['ollama_model']
            
            if 'openai_key' in data:
                app.config['OPENAI_API_KEY'] = data['openai_key']
            
            if 'openai_model' in data:
                app.config['OPENAI_MODEL'] = data['openai_model']
            
            if 'openai_base_url' in data:
                app.config['OPENAI_BASE_URL'] = data['openai_base_url']
            
            if 'anthropic_key' in data:
                app.config['ANTHROPIC_API_KEY'] = data['anthropic_key']
            
            if 'anthropic_model' in data:
                app.config['ANTHROPIC_MODEL'] = data['anthropic_model']
            
            if 'google_key' in data:
                app.config['GOOGLE_AI_API_KEY'] = data['google_key']
            
            if 'google_model' in data:
                app.config['GOOGLE_AI_MODEL'] = data['google_model']
            
            if 'custom_key' in data:
                app.config['CUSTOM_API_KEY'] = data['custom_key']
            
            if 'custom_base_url' in data:
                app.config['CUSTOM_BASE_URL'] = data['custom_base_url']
            
            if 'custom_model' in data:
                app.config['CUSTOM_MODEL'] = data['custom_model']
            
            return jsonify({'success': True, 'message': 'Configuration updated'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/test-connection')
def api_test_connection():
    """Test the current AI provider connection"""
    try:
        test_prompt = "Hello, can you respond with just 'Connection successful'?"
        response = AIService.generate_response(test_prompt)
        
        if "Connection successful" in response or "Error" not in response:
            return jsonify({
                'success': True, 
                'message': 'AI is responding correctly',
                'provider': AIService.get_provider()
            })
        else:
            return jsonify({
                'success': False, 
                'error': response,
                'provider': AIService.get_provider()
            })
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e),
            'provider': AIService.get_provider()
        })

@app.route('/chat')
def chat_page():
    """Dedicated chat page"""
    return render_template('chat.html')

# Rush AI API endpoints for external users
@app.route('/api/v1/chat', methods=['POST'])
def rush_ai_chat():
    """Rush AI Chat API - External access with API key"""
    # Get API key from header
    api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not api_key:
        return jsonify({'error': 'API key required. Get your Rush AI API key at /api-keys'}), 401
    
    # Validate API key
    key_data, error = api_key_manager.validate_key(api_key)
    if error:
        return jsonify({'error': error}), 401
    
    # Get request data
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    message = data['message']
    context = data.get('context', '')
    
    # Generate AI response with knowledge sharing
    ai_service = AIService.get_instance()
    response = ai_service.generate_response(message, context, api_key)
    
    # Use one request from the API key
    api_key_manager.use_request(api_key)
    
    # Return response with usage info
    return jsonify({
        'response': response,
        'usage': {
            'requests_used': key_data['requests_used'],
            'requests_limit': key_data['requests_limit'],
            'tier': key_data['tier']
        }
    })

@app.route('/api/v1/movie-search', methods=['GET'])
def rush_ai_movie_search():
    """Rush AI Movie Search API"""
    api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    key_data, error = api_key_manager.validate_key(api_key)
    if error:
        return jsonify({'error': error}), 401
    
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    # Search movies
    results = TMDBService.search_movies(query)
    
    # Use one request
    api_key_manager.use_request(api_key)
    
    return jsonify({
        'results': results,
        'usage': {
            'requests_used': key_data['requests_used'],
            'requests_limit': key_data['requests_limit'],
            'tier': key_data['tier']
        }
    })

@app.route('/api/v1/people-search', methods=['GET'])
def rush_ai_people_search():
    """Rush AI People Search API"""
    api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    key_data, error = api_key_manager.validate_key(api_key)
    if error:
        return jsonify({'error': error}), 401
    
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query parameter "q" is required'}), 400
    
    # Search people
    results = TMDBService.search_people(query)
    
    # Use one request
    api_key_manager.use_request(api_key)
    
    return jsonify({
        'results': results,
        'usage': {
            'requests_used': key_data['requests_used'],
            'requests_limit': key_data['requests_limit'],
            'tier': key_data['tier']
        }
    })

@app.route('/api-keys', methods=['GET', 'POST'])
def manage_api_keys():
    """Generate or view Rush AI API keys"""
    if request.method == 'GET':
        # Show API key generation page
        return render_template('api_keys.html')
    
    elif request.method == 'POST':
        # Generate new API key - no email required
        data = request.get_json() or {}
        tier = 'free'  # Always free
        
        # Generate API key
        api_key, key_data = api_key_manager.generate_key(tier)
        
        return jsonify({
            'api_key': api_key,
            'tier': tier,
            'requests_limit': key_data['requests_limit'],
            'expires_at': key_data['expires_at'].isoformat(),
            'usage_url': '/api/v1/usage'
        })

@app.route('/api/v1/usage', methods=['GET'])
def api_usage():
    """Check API key usage"""
    api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not api_key:
        return jsonify({'error': 'API key required'}), 401
    
    key_data, error = api_key_manager.validate_key(api_key)
    if error:
        return jsonify({'error': error}), 401
    
    return jsonify({
        'usage': {
            'requests_used': key_data['requests_used'],
            'requests_limit': key_data['requests_limit'],
            'remaining': key_data['requests_limit'] - key_data['requests_used'],
            'tier': key_data['tier'],
            'expires_at': key_data['expires_at'].isoformat()
        }
    })

@app.route('/test-env')
def test_env():
    """Test endpoint to check environment variables"""
    return jsonify({
        'CUSTOM_API_KEY_set': bool(app.config.get('CUSTOM_API_KEY')),
        'CUSTOM_API_KEY_prefix': app.config.get('CUSTOM_API_KEY', '')[:10] if app.config.get('CUSTOM_API_KEY') else 'NOT_SET',
        'CUSTOM_BASE_URL': app.config.get('CUSTOM_BASE_URL'),
        'CUSTOM_MODEL': app.config.get('CUSTOM_MODEL'),
        'AI_PROVIDER': app.config.get('AI_PROVIDER')
    })

@app.route('/docs')
def api_docs():
    """Rush AI API Documentation"""
    return render_template('api_docs.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
