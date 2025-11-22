#!/usr/bin/env python3
"""
Rush AI Knowledge Database Tools
Access and manage your AI knowledge database directly
"""

import json
import csv
from database import knowledge_db

def view_all_knowledge():
    """View all knowledge in the database"""
    print("🧠 Rush AI Knowledge Database")
    print("=" * 50)
    
    knowledge = knowledge_db.get_all_knowledge(limit=20)
    
    if not knowledge:
        print("No knowledge in database yet!")
        return
    
    print(f"Showing {len(knowledge)} recent knowledge items:\n")
    
    for i, item in enumerate(knowledge, 1):
        print(f"{i}. Question: {item['question'][:100]}...")
        print(f"   Answer: {item['answer'][:150]}...")
        print(f"   Uses: {item['uses']}")
        print(f"   Created: {item['created_at']}")
        print("-" * 50)

def export_knowledge_json(filename="rush_ai_knowledge.json"):
    """Export all knowledge to JSON file"""
    print(f"📤 Exporting knowledge to {filename}...")
    
    exported_data = knowledge_db.export_knowledge('json')
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(exported_data)
    
    knowledge = json.loads(exported_data)
    print(f"✅ Exported {len(knowledge)} knowledge items to {filename}")

def export_knowledge_csv(filename="rush_ai_knowledge.csv"):
    """Export all knowledge to CSV file"""
    print(f"📤 Exporting knowledge to {filename}...")
    
    exported_data = knowledge_db.export_knowledge('csv')
    
    with open(filename, 'w', encoding='utf-8', newline='') as f:
        f.write(exported_data)
    
    print(f"✅ Exported knowledge to {filename}")

def show_statistics():
    """Show database statistics"""
    print("📊 Database Statistics")
    print("=" * 30)
    
    stats = knowledge_db.get_statistics()
    
    print(f"Total Knowledge Items: {stats['total_knowledge']}")
    print(f"Total Uses: {stats['total_uses']}")
    print(f"Contributors: {stats['contributors']}")
    print(f"Average Quality: {stats['average_quality']}")
    
    if stats['top_contributors']:
        print("\n🏆 Top Contributors:")
        for i, (api_key, count) in enumerate(stats['top_contributors'][:5], 1):
            print(f"  {i}. API Key: {api_key[:10]}... ({count} contributions)")

def search_knowledge(query):
    """Search knowledge by query"""
    print(f"🔍 Searching for: '{query}'")
    print("=" * 40)
    
    results = knowledge_db.search_knowledge(query, limit=10)
    
    if not results:
        print("No matching knowledge found!")
        return
    
    print(f"Found {len(results)} results:\n")
    
    for i, item in enumerate(results, 1):
        print(f"{i}. Question: {item['question']}")
        print(f"   Answer: {item['answer'][:200]}...")
        print(f"   Uses: {item['uses']}")
        print("-" * 50)

def add_knowledge_interactive():
    """Add knowledge interactively"""
    print("➕ Add New Knowledge")
    print("=" * 25)
    
    question = input("Question: ").strip()
    answer = input("Answer: ").strip()
    api_key = input("API Key (or press Enter for default): ").strip() or "manual_add"
    
    if len(question) < 5 or len(answer) < 20:
        print("❌ Question must be at least 5 chars, answer at least 20 chars")
        return
    
    try:
        knowledge_db.add_knowledge(question, answer, api_key)
        print("✅ Knowledge added successfully!")
    except Exception as e:
        print(f"❌ Error adding knowledge: {e}")

def main():
    """Main menu"""
    while True:
        print("\n🧠 Rush AI Knowledge Tools")
        print("=" * 30)
        print("1. View All Knowledge")
        print("2. Search Knowledge")
        print("3. Add Knowledge")
        print("4. Show Statistics")
        print("5. Export to JSON")
        print("6. Export to CSV")
        print("7. Exit")
        
        choice = input("\nSelect option (1-7): ").strip()
        
        if choice == '1':
            view_all_knowledge()
        elif choice == '2':
            query = input("Enter search query: ").strip()
            search_knowledge(query)
        elif choice == '3':
            add_knowledge_interactive()
        elif choice == '4':
            show_statistics()
        elif choice == '5':
            export_knowledge_json()
        elif choice == '6':
            export_knowledge_csv()
        elif choice == '7':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice!")

if __name__ == "__main__":
    main()
