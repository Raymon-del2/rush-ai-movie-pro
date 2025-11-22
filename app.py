from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime
import os
from config import Config
from models import api_key_manager
from database import knowledge_db

# Get the directory where this file is located
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__, 
           static_folder=os.path.join(basedir, 'static'), 
           static_url_path='/static',
           template_folder=os.path.join(basedir, 'templates'))
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
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True

    @staticmethod
    def get_instance():
        """Get singleton instance"""
        return AIService()

    def add_shared_knowledge(self, question, answer, api_key):
        """Add knowledge to shared pool using database"""
        try:
            knowledge_db.add_knowledge(question, answer, api_key)
        except Exception as e:
            print(f"Error adding knowledge to database: {e}")

    def get_shared_knowledge(self, question):
        """Get relevant knowledge from database"""
        try:
            # Search for relevant knowledge
            relevant_knowledge = knowledge_db.search_knowledge(question, limit=3)

            # Update usage count for found knowledge
            for knowledge in relevant_knowledge:
                knowledge_db.update_knowledge_uses(knowledge['question'])

            # Return just the answers
            return [k['answer'] for k in relevant_knowledge]
        except Exception as e:
            print(f"Error retrieving knowledge from database: {e}")
            return []

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
            
            # Auto-learn from good responses (no API key required)
            if len(response) > 50 and "Error" not in response and "API error" not in response:
                # Add to shared knowledge automatically
                self.add_shared_knowledge(prompt, response, api_key or "auto_learning")
            
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

@app.route('/knowledge-keys')
def knowledge_keys_page():
    """Knowledge API keys management page"""
    return render_template('knowledge_keys.html')

@app.route('/api/learn', methods=['POST'])
def api_simple_learn():
    """Simple AI learning endpoint - no API key required"""
    try:
        # Get learning data
        data = request.get_json()
        if not data or 'question' not in data or 'answer' not in data:
            return jsonify({'error': 'Question and answer are required'}), 400
        
        question = data['question'].strip()
        answer = data['answer'].strip()
        tags = data.get('tags', [])
        source = data.get('source', 'direct_api')
        
        if len(question) < 5 or len(answer) < 20:
            return jsonify({'error': 'Question must be at least 5 chars, answer at least 20 chars'}), 400
        
        # Add knowledge directly (no API key validation)
        knowledge_id = knowledge_db.add_knowledge(question, answer, source, tags)
        
        return jsonify({
            'success': True,
            'knowledge_id': knowledge_id,
            'question': question,
            'answer_length': len(answer),
            'message': 'AI learned successfully!',
            'source': source
        })
        
    except Exception as e:
        return jsonify({'error': f'Learning failed: {str(e)}'}), 500

@app.route('/api/knowledge-keys', methods=['POST'])
def api_generate_knowledge_key():
    """Generate a new knowledge API key"""
    try:
        data = request.get_json() or {}
        name = data.get('name', 'Knowledge API Key')
        description = data.get('description', 'API key for AI learning')
        
        # Generate knowledge key
        key = knowledge_db.generate_knowledge_key(name, description)
        
        return jsonify({
            'success': True,
            'knowledge_key': key,
            'name': name,
            'description': description,
            'message': 'Knowledge API key generated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate knowledge key: {str(e)}'}), 500

@app.route('/api/knowledge-keys', methods=['GET'])
def api_list_knowledge_keys():
    """List all knowledge API keys"""
    try:
        keys = knowledge_db.get_knowledge_keys()
        
        return jsonify({
            'success': True,
            'keys': keys,
            'total': len(keys)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to list knowledge keys: {str(e)}'}), 500

@app.route('/api/knowledge-keys/<key>', methods=['DELETE'])
def api_deactivate_knowledge_key(key):
    """Deactivate or permanently delete a knowledge API key"""
    try:
        # Check if this is a permanent delete request
        permanent_delete = request.headers.get('X-Permanent-Delete') == 'true'
        
        if permanent_delete:
            # Permanently delete the key from database
            conn = knowledge_db.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM knowledge_keys WHERE knowledge_key = ?', (key,))
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': 'Knowledge API key deleted permanently'
            })
        else:
            # Just deactivate (soft delete)
            knowledge_db.deactivate_knowledge_key(key)
            
            return jsonify({
                'success': True,
                'message': 'Knowledge API key deactivated successfully'
            })
        
    except Exception as e:
        return jsonify({'error': f'Failed to process key: {str(e)}'}), 500

@app.route('/api/knowledge/learn', methods=['POST'])
def api_knowledge_learn():
    """AI learning endpoint using knowledge API key"""
    try:
        # Get knowledge key from header
        knowledge_key = request.headers.get('X-Knowledge-Key')
        if not knowledge_key:
            return jsonify({'error': 'Knowledge API key required'}), 401
        
        # Validate knowledge key
        if not knowledge_db.validate_knowledge_key(knowledge_key):
            return jsonify({'error': 'Invalid or inactive knowledge API key'}), 401
        
        # Get learning data
        data = request.get_json()
        if not data or 'question' not in data or 'answer' not in data:
            return jsonify({'error': 'Question and answer are required'}), 400
        
        question = data['question'].strip()
        answer = data['answer'].strip()
        tags = data.get('tags', [])
        
        if len(question) < 5 or len(answer) < 20:
            return jsonify({'error': 'Question must be at least 5 chars, answer at least 20 chars'}), 400
        
        # Add knowledge using knowledge key
        knowledge_id = knowledge_db.add_knowledge_with_key(question, answer, knowledge_key, tags)
        
        return jsonify({
            'success': True,
            'knowledge_id': knowledge_id,
            'question': question,
            'answer_length': len(answer),
            'message': 'AI learned successfully!'
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    except Exception as e:
        return jsonify({'error': f'Learning failed: {str(e)}'}), 500

@app.route('/api/knowledge/by-source', methods=['GET'])
def api_knowledge_by_source():
    """Get knowledge filtered by source type"""
    try:
        source_type = request.args.get('source', 'all')
        if source_type not in ['all', 'knowledge_api']:
            source_type = 'all'
        
        knowledge = knowledge_db.get_knowledge_by_source(source_type)
        
        return jsonify({
            'success': True,
            'source_type': source_type,
            'knowledge': knowledge,
            'total': len(knowledge)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get knowledge: {str(e)}'}), 500

@app.route('/api/knowledge/add', methods=['POST'])
def api_add_knowledge():
    """Add knowledge to the shared pool (requires API key)"""
    try:
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key
        key_data = api_key_manager.get_key(api_key)
        if not key_data:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Get knowledge data
        data = request.get_json()
        if not data or 'question' not in data or 'answer' not in data:
            return jsonify({'error': 'Question and answer are required'}), 400
        
        question = data['question'].strip()
        answer = data['answer'].strip()
        
        if len(question) < 5 or len(answer) < 20:
            return jsonify({'error': 'Question must be at least 5 chars, answer at least 20 chars'}), 400
        
        # Add to shared knowledge
        ai_service = AIService.get_instance()
        ai_service.add_shared_knowledge(question, answer, api_key)
        
        return jsonify({
            'success': True,
            'message': 'Knowledge added successfully',
            'question': question,
            'answer_length': len(answer)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to add knowledge: {str(e)}'}), 500

@app.route('/api/knowledge/search', methods=['GET'])
def api_search_knowledge():
    """Search the shared knowledge pool (requires API key)"""
    try:
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key
        key_data = api_key_manager.get_key(api_key)
        if not key_data:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Get search query
        query = request.args.get('q', '').strip()
        if len(query) < 3:
            return jsonify({'error': 'Query must be at least 3 characters'}), 400
        
        # Search knowledge
        ai_service = AIService.get_instance()
        shared_knowledge = ai_service.get_shared_knowledge(query)
        
        return jsonify({
            'query': query,
            'results_count': len(shared_knowledge),
            'knowledge': shared_knowledge[:10]  # Limit to 10 results
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to search knowledge: {str(e)}'}), 500

@app.route('/api/knowledge/import', methods=['POST'])
def api_import_knowledge():
    """Bulk import knowledge (requires API key)"""
    try:
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key
        key_data = api_key_manager.get_key(api_key)
        if not key_data:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Get knowledge data
        data = request.get_json()
        if not data or 'knowledge' not in data:
            return jsonify({'error': 'Knowledge array is required'}), 400
        
        knowledge_items = data['knowledge']
        if not isinstance(knowledge_items, list):
            return jsonify({'error': 'Knowledge must be an array'}), 400
        
        if len(knowledge_items) > 100:  # Limit bulk imports
            return jsonify({'error': 'Maximum 100 items per bulk import'}), 400
        
        # Validate and import each item
        ai_service = AIService.get_instance()
        imported = 0
        failed = 0
        
        for item in knowledge_items:
            if not isinstance(item, dict) or 'question' not in item or 'answer' not in item:
                failed += 1
                continue
            
            question = str(item['question']).strip()
            answer = str(item['answer']).strip()
            
            if len(question) >= 5 and len(answer) >= 20:
                ai_service.add_shared_knowledge(question, answer, api_key)
                imported += 1
            else:
                failed += 1
        
        return jsonify({
            'success': True,
            'imported': imported,
            'failed': failed,
            'total': len(knowledge_items)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to import knowledge: {str(e)}'}), 500

@app.route('/api/knowledge/stats', methods=['GET'])
def api_knowledge_stats():
    """Get knowledge pool statistics (requires API key)"""
    try:
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key
        key_data = api_key_manager.get_key(api_key)
        if not key_data:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Get stats from database
        stats = knowledge_db.get_statistics()
        
        return jsonify({
            'total_knowledge_items': stats['total_knowledge'],
            'total_uses': stats['total_uses'],
            'contributors': stats['contributors'],
            'average_quality': stats['average_quality'],
            'api_key_requests': key_data['requests_used']
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@app.route('/api/knowledge/export', methods=['GET'])
def api_export_knowledge():
    """Export all knowledge (requires API key)"""
    try:
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key
        key_data = api_key_manager.get_key(api_key)
        if not key_data:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Get export format
        export_format = request.args.get('format', 'json').lower()
        if export_format not in ['json', 'csv']:
            export_format = 'json'
        
        # Export knowledge
        exported_data = knowledge_db.export_knowledge(export_format)
        
        if export_format == 'json':
            return jsonify({
                'success': True,
                'data': json.loads(exported_data),
                'total_items': len(json.loads(exported_data))
            })
        else:
            return exported_data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=rush_ai_knowledge.csv'
            }
        
    except Exception as e:
        return jsonify({'error': f'Failed to export knowledge: {str(e)}'}), 500

@app.route('/api/knowledge/all', methods=['GET'])
def api_get_all_knowledge():
    """Get all knowledge with pagination (requires API key)"""
    try:
        # Get API key from header
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key
        key_data = api_key_manager.get_key(api_key)
        if not key_data:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Get pagination parameters
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        if limit > 100:
            limit = 100  # Maximum limit
        
        # Get knowledge
        knowledge = knowledge_db.get_all_knowledge(limit=limit, offset=offset)
        
        return jsonify({
            'knowledge': knowledge,
            'limit': limit,
            'offset': offset,
            'total': len(knowledge)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get knowledge: {str(e)}'}), 500

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

@app.route('/debug')
def debug():
    """Debug route - no authentication, no dependencies"""
    return "Rush AI Debug - Working!", 200

@app.route('/health')
def health_check():
    """Health check endpoint - no authentication required"""
    return jsonify({
        'status': 'healthy',
        'app': 'Rush AI',
        'version': '1.0.0'
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
