import sqlite3
import json
from datetime import datetime
import os
import secrets
import hashlib

class KnowledgeDatabase:
    def __init__(self, db_path=None):
        # Use absolute path and ensure cross-platform compatibility
        if db_path is None:
            # Get the directory of this file and create database there
            base_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(base_dir, 'knowledge.db')
        
        # Normalize path for cross-platform compatibility
        self.db_path = os.path.normpath(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize the knowledge database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create knowledge table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                api_key TEXT NOT NULL,
                knowledge_key TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                uses INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                tags TEXT,
                quality_score REAL DEFAULT 0.0
            )
        ''')
        
        # Create API keys table for tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                requests_used INTEGER DEFAULT 0,
                knowledge_contributed INTEGER DEFAULT 0
            )
        ''')
        
        # Create knowledge API keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                knowledge_key TEXT UNIQUE NOT NULL,
                name TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                knowledge_added INTEGER DEFAULT 0,
                last_used TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                permissions TEXT DEFAULT 'read,write'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def generate_knowledge_key(self, name="Default", description="Knowledge API Key"):
        """Generate a new knowledge API key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate unique key
        while True:
            key = f"rk_{secrets.token_urlsafe(16)}"
            cursor.execute('SELECT knowledge_key FROM knowledge_keys WHERE knowledge_key = ?', (key,))
            if not cursor.fetchone():
                break
        
        try:
            cursor.execute('''
                INSERT INTO knowledge_keys (knowledge_key, name, description)
                VALUES (?, ?, ?)
            ''', (key, name, description))
            
            conn.commit()
            return key
            
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def validate_knowledge_key(self, key):
        """Validate and update knowledge API key usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, is_active FROM knowledge_keys 
            WHERE knowledge_key = ?
        ''', (key,))
        
        result = cursor.fetchone()
        
        if result and result[1]:  # Key exists and is active
            # Update last used
            cursor.execute('''
                UPDATE knowledge_keys 
                SET last_used = CURRENT_TIMESTAMP 
                WHERE knowledge_key = ?
            ''', (key,))
            
            conn.commit()
            return True
        else:
            return False
    
    def add_knowledge_with_key(self, question, answer, knowledge_key, tags=None, source="api"):
        """Add knowledge using knowledge API key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Validate knowledge key
        if not self.validate_knowledge_key(knowledge_key):
            raise ValueError("Invalid or inactive knowledge key")
        
        try:
            cursor.execute('''
                INSERT INTO knowledge (question, answer, api_key, knowledge_key, tags)
                VALUES (?, ?, ?, ?, ?)
            ''', (question, answer, "knowledge_api", knowledge_key, json.dumps(tags) if tags else None))
            
            # Update knowledge key contribution count
            cursor.execute('''
                UPDATE knowledge_keys 
                SET knowledge_added = knowledge_added + 1 
                WHERE knowledge_key = ?
            ''', (knowledge_key,))
            
            conn.commit()
            return cursor.lastrowid
            
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_knowledge_keys(self):
        """Get all knowledge API keys"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT knowledge_key, name, description, created_at, knowledge_added, last_used, is_active, permissions
            FROM knowledge_keys 
            ORDER BY created_at DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        keys = []
        for row in results:
            keys.append({
                'key': row[0],
                'name': row[1],
                'description': row[2],
                'created_at': row[3],
                'knowledge_added': row[4],
                'last_used': row[5],
                'is_active': bool(row[6]),
                'permissions': row[7]
            })
        
        return keys
    
    def deactivate_knowledge_key(self, key):
        """Deactivate a knowledge API key"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE knowledge_keys 
            SET is_active = 0 
            WHERE knowledge_key = ?
        ''', (key,))
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_knowledge_by_source(self, source_type="all"):
        """Get knowledge filtered by source type"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if source_type == "knowledge_api":
            cursor.execute('''
                SELECT question, answer, uses, created_at, tags, knowledge_key
                FROM knowledge 
                WHERE api_key = 'knowledge_api'
                ORDER BY uses DESC, created_at DESC
            ''')
        else:
            cursor.execute('''
                SELECT question, answer, uses, created_at, tags, api_key, knowledge_key
                FROM knowledge 
                ORDER BY uses DESC, created_at DESC
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        knowledge_list = []
        for row in results:
            item = {
                'question': row[0],
                'answer': row[1],
                'uses': row[2],
                'created_at': row[3],
                'tags': json.loads(row[4]) if row[4] else []
            }
            if source_type == "knowledge_api":
                item['knowledge_key'] = row[5]
            else:
                item['api_key'] = row[5]
                item['knowledge_key'] = row[6] if len(row) > 6 else None
            
            knowledge_list.append(item)
        
        return knowledge_list
    
    def add_knowledge(self, question, answer, api_key, tags=None):
        """Add new knowledge to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO knowledge (question, answer, api_key, tags)
                VALUES (?, ?, ?, ?)
            ''', (question, answer, api_key, json.dumps(tags) if tags else None))
            
            # Update API key contribution count
            cursor.execute('''
                INSERT OR IGNORE INTO api_keys (api_key) VALUES (?)
            ''', (api_key,))
            
            cursor.execute('''
                UPDATE api_keys SET knowledge_contributed = knowledge_contributed + 1
                WHERE api_key = ?
            ''', (api_key,))
            
            conn.commit()
            return cursor.lastrowid
            
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def search_knowledge(self, query, limit=10):
        """Search knowledge by question keywords"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple keyword search - can be enhanced with FTS later
        keywords = query.lower().split()
        where_conditions = []
        params = []
        
        for keyword in keywords:
            if len(keyword) > 3:  # Only search meaningful keywords
                where_conditions.append("LOWER(question) LIKE ?")
                params.append(f"%{keyword}%")
        
        if where_conditions:
            sql = f'''
                SELECT question, answer, uses, created_at, tags
                FROM knowledge 
                WHERE {' OR '.join(where_conditions)}
                ORDER BY uses DESC, quality_score DESC
                LIMIT ?
            '''
            params.append(limit)
            
            cursor.execute(sql, params)
            results = cursor.fetchall()
            
            knowledge_list = []
            for row in results:
                knowledge_list.append({
                    'question': row[0],
                    'answer': row[1],
                    'uses': row[2],
                    'created_at': row[3],
                    'tags': json.loads(row[4]) if row[4] else []
                })
            
            return knowledge_list
        else:
            return []
    
    def get_all_knowledge(self, limit=None, offset=0):
        """Get all knowledge with pagination"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = '''
            SELECT question, answer, uses, created_at, tags, api_key, quality_score
            FROM knowledge 
            ORDER BY uses DESC, created_at DESC
        '''
        
        if limit:
            sql += ' LIMIT ? OFFSET ?'
            cursor.execute(sql, (limit, offset))
        else:
            cursor.execute(sql)
        
        results = cursor.fetchall()
        conn.close()
        
        knowledge_list = []
        for row in results:
            knowledge_list.append({
                'question': row[0],
                'answer': row[1],
                'uses': row[2],
                'created_at': row[3],
                'tags': json.loads(row[4]) if row[4] else [],
                'api_key': row[5],
                'quality_score': row[6]
            })
        
        return knowledge_list
    
    def update_knowledge_uses(self, question):
        """Increment usage count for knowledge"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE knowledge 
            SET uses = uses + 1, last_used = CURRENT_TIMESTAMP 
            WHERE question = ?
        ''', (question,))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total knowledge
        cursor.execute('SELECT COUNT(*) FROM knowledge')
        total_knowledge = cursor.fetchone()[0]
        
        # Total uses
        cursor.execute('SELECT SUM(uses) FROM knowledge')
        total_uses = cursor.fetchone()[0] or 0
        
        # Contributors
        cursor.execute('SELECT COUNT(DISTINCT api_key) FROM knowledge')
        contributors = cursor.fetchone()[0]
        
        # Average quality score
        cursor.execute('SELECT AVG(quality_score) FROM knowledge')
        avg_quality = cursor.fetchone()[0] or 0
        
        # Knowledge by API key
        cursor.execute('''
            SELECT api_key, COUNT(*) as contributions 
            FROM knowledge 
            GROUP BY api_key 
            ORDER BY contributions DESC
            LIMIT 10
        ''')
        top_contributors = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_knowledge': total_knowledge,
            'total_uses': total_uses,
            'contributors': contributors,
            'average_quality': round(avg_quality, 2),
            'top_contributors': top_contributors
        }
    
    def export_knowledge(self, format='json'):
        """Export all knowledge for backup or use in other AI systems"""
        knowledge = self.get_all_knowledge()
        
        if format == 'json':
            return json.dumps(knowledge, indent=2, default=str)
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['question', 'answer', 'uses', 'created_at', 'tags', 'api_key'])
            
            for item in knowledge:
                writer.writerow([
                    item['question'],
                    item['answer'],
                    item['uses'],
                    item['created_at'],
                    json.dumps(item['tags']),
                    item['api_key']
                ])
            
            return output.getvalue()
        else:
            return knowledge
    
    def import_knowledge(self, knowledge_data, api_key):
        """Import knowledge from other systems"""
        imported = 0
        failed = 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for item in knowledge_data:
                if isinstance(item, dict) and 'question' in item and 'answer' in item:
                    question = str(item['question']).strip()
                    answer = str(item['answer']).strip()
                    tags = item.get('tags', [])
                    
                    if len(question) >= 5 and len(answer) >= 20:
                        cursor.execute('''
                            INSERT INTO knowledge (question, answer, api_key, tags)
                            VALUES (?, ?, ?, ?)
                        ''', (question, answer, api_key, json.dumps(tags)))
                        imported += 1
                    else:
                        failed += 1
                else:
                    failed += 1
            
            conn.commit()
            
        except sqlite3.Error as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
        
        return {'imported': imported, 'failed': failed}

# Global database instance
knowledge_db = KnowledgeDatabase()
