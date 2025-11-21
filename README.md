# Rush - AI Movie Pro

An intelligent movie database and chat application powered by Ollama AI and TMDB API.

## Features

- **🎬 Movie Search**: Search for movies by title with detailed information
- **👥 Celebrity Search**: Find actors, directors, and other film industry professionals
- **🤖 AI Chat**: Interactive chat with Rush AI for movie recommendations and insights
- **🔥 Trending Movies**: Discover what's currently trending
- **⭐ Popular Movies**: Browse top-rated films
- **📊 Detailed Information**: Get comprehensive movie and celebrity data including cast, crew, ratings, and more

## Requirements

- Python 3.8+
- Ollama installed and running
- Internet connection for TMDB API access

## Setup

### 1. Install Ollama

Download and install Ollama from [https://ollama.ai/](https://ollama.ai/)

### 2. Pull the AI Model

```bash
ollama pull llama3.2:3b
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Ollama Server

Make sure Ollama is running:

```bash
ollama serve
```

### 5. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Main Dashboard
- Search for movies or people using the search bar
- Browse trending and popular movies
- Access the AI chat interface

### AI Chat
- Ask for movie recommendations
- Get information about actors, directors, and films
- Discuss movie plots and themes
- Compare movies and find similar films

### Movie Details
- Click on any movie card to see detailed information
- View cast, crew, ratings, and synopsis
- Access trailers and images (when available)

### Celebrity Profiles
- Click on any person card to see their profile
- View biography, filmography, and career highlights
- See known-for movies and roles

## API Endpoints

### Movie Search
- `GET /api/search/movies?q={query}&page={page}` - Search movies
- `GET /api/movie/{id}` - Get movie details
- `GET /api/popular/movies?page={page}` - Get popular movies
- `GET /api/trending/movies?window={day|week}` - Get trending movies

### People Search
- `GET /api/search/people?q={query}&page={page}` - Search people
- `GET /api/person/{id}` - Get person details

### AI Chat
- `POST /api/chat` - Send message to AI

## Configuration

The application uses the following configuration:
- **TMDB API Key**: Built-in (b2f549238e90b6a7593d30ad0d53021c)
- **Ollama Model**: llama3.2:3b
- **Ollama API URL**: http://localhost:11434/api/generate

## Troubleshooting

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Check if the model is installed: `ollama list`
- Verify the model is pulled: `ollama pull llama3.2:3b`

### TMDB API Issues
- Check internet connection
- Verify API key is valid
- Check TMDB service status

### Port Conflicts
- The app runs on port 5000 by default
- Change port in `app.py` if needed: `app.run(port=8080)`

## Technology Stack

- **Backend**: Flask (Python)
- **AI**: Ollama with Llama 3.2 3B model
- **Movie Database**: TMDB API
- **Frontend**: HTML5, Tailwind CSS, JavaScript
- **Icons**: Font Awesome

## License

This project is for educational and personal use. Please respect the terms of service of TMDB and Ollama.

## Contributing

Feel free to submit issues and enhancement requests!
