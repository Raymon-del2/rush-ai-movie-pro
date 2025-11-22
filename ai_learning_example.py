#!/usr/bin/env python3
"""
Example: How to use Knowledge API Keys for AI Learning
"""

import requests
import json

# Your Rush AI API base URL
BASE_URL = "http://127.0.0.1:5000"

def generate_knowledge_key():
    """Generate a new knowledge API key"""
    print("🔑 Generating Knowledge API Key...")
    
    response = requests.post(f"{BASE_URL}/api/knowledge-keys", 
                           json={
                               "name": "My Movie AI",
                               "description": "AI learning for movie recommendations"
                           })
    
    if response.status_code == 200:
        data = response.json()
        knowledge_key = data['knowledge_key']
        print(f"✅ Knowledge Key Generated: {knowledge_key}")
        return knowledge_key
    else:
        print(f"❌ Error: {response.json()}")
        return None

def teach_ai(knowledge_key, question, answer, tags=None):
    """Teach the AI using knowledge API key"""
    print(f"🧠 Teaching AI: {question[:50]}...")
    
    headers = {
        "X-Knowledge-Key": knowledge_key,
        "Content-Type": "application/json"
    }
    
    data = {
        "question": question,
        "answer": answer,
        "tags": tags or []
    }
    
    response = requests.post(f"{BASE_URL}/api/knowledge/learn", 
                           headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ AI Learned! Knowledge ID: {result['knowledge_id']}")
        return True
    else:
        print(f"❌ Error: {response.json()}")
        return False

def list_knowledge_keys():
    """List all knowledge API keys"""
    print("\n📋 Knowledge API Keys:")
    
    response = requests.get(f"{BASE_URL}/api/knowledge-keys")
    
    if response.status_code == 200:
        data = response.json()
        for key in data['keys']:
            status = "🟢 Active" if key['is_active'] else "🔴 Inactive"
            print(f"  • {key['name']}: {key['key'][:20]}... ({status})")
            print(f"    - Added: {key['knowledge_added']} knowledge items")
    else:
        print(f"❌ Error: {response.json()}")

def get_knowledge_by_source():
    """Get knowledge filtered by source"""
    print("\n📊 Knowledge by Source:")
    
    # Get all knowledge
    response = requests.get(f"{BASE_URL}/api/knowledge/by-source?source=all")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total Knowledge: {data['total']}")
        
        # Get knowledge API knowledge only
        response2 = requests.get(f"{BASE_URL}/api/knowledge/by-source?source=knowledge_api")
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"Knowledge API Learning: {data2['total']}")
            print(f"Regular User Learning: {data['total'] - data2['total']}")
    else:
        print(f"❌ Error: {response.json()}")

def main():
    """Main example flow"""
    print("🤖 Rush AI Knowledge API Key Example")
    print("=" * 40)
    
    # Step 1: Generate knowledge key
    knowledge_key = generate_knowledge_key()
    if not knowledge_key:
        return
    
    # Step 2: Teach the AI some movie knowledge
    movie_knowledge = [
        {
            "question": "What is the plot of The Matrix?",
            "answer": "The Matrix follows a computer hacker who discovers reality is a simulation and joins a rebellion to free humanity.",
            "tags": ["sci-fi", "action", "1999"]
        },
        {
            "question": "Who directed Inception?",
            "answer": "Christopher Nolan directed Inception, a sci-fi thriller about dream thieves starring Leonardo DiCaprio.",
            "tags": ["nolan", "sci-fi", "thriller"]
        },
        {
            "question": "What is the highest-grossing movie of all time?",
            "answer": "Avatar (2009) directed by James Cameron is one of the highest-grossing movies of all time, earning over $2.7 billion worldwide.",
            "tags": ["avatar", "cameron", "box-office"]
        }
    ]
    
    print(f"\n📚 Teaching AI {len(movie_knowledge)} movie facts...")
    
    for i, knowledge in enumerate(movie_knowledge, 1):
        success = teach_ai(
            knowledge_key, 
            knowledge['question'], 
            knowledge['answer'], 
            knowledge['tags']
        )
        if success:
            print(f"  ✅ {i}/{len(movie_knowledge)} taught successfully")
        else:
            print(f"  ❌ {i}/{len(movie_knowledge)} failed")
    
    # Step 3: Show results
    list_knowledge_keys()
    get_knowledge_by_source()
    
    print(f"\n🎉 Example Complete!")
    print(f"🔑 Your Knowledge API Key: {knowledge_key}")
    print(f"📖 Use this key to teach your AI more movie knowledge!")

if __name__ == "__main__":
    main()
