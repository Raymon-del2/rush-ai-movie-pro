from datetime import datetime, timedelta
import secrets
import hashlib

class APIKey:
    def __init__(self):
        self.keys = {}  # In-memory storage (in production, use database)
    
    def generate_key(self, tier='free'):
        """Generate a new Rush AI API key - always free and unlimited"""
        # Generate unique key
        key_prefix = "rush_"
        random_part = secrets.token_urlsafe(32)
        api_key = f"{key_prefix}{random_part}"
        
        # Hash the key for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Store key information - always free and unlimited
        key_data = {
            'key_hash': key_hash,
            'user_email': 'anonymous',
            'tier': 'free',
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(days=3650),  # 10 years
            'requests_used': 0,
            'requests_limit': 999999999,  # Unlimited
            'active': True
        }
        
        self.keys[key_hash] = key_data
        return api_key, key_data
    
    def _get_tier_limit(self, tier):
        """Get request limits based on tier"""
        limits = {
            'free': 100,
            'basic': 1000,
            'pro': 10000,
            'enterprise': 100000
        }
        return limits.get(tier, 100)
    
    def validate_key(self, api_key):
        """Validate and return key information"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        if key_hash not in self.keys:
            return None, "Invalid API key"
        
        key_data = self.keys[key_hash]
        
        # Check if key is active
        if not key_data['active']:
            return None, "API key is deactivated"
        
        # Check if key has expired
        if datetime.utcnow() > key_data['expires_at']:
            return None, "API key has expired"
        
        # Check if limit exceeded
        if key_data['requests_used'] >= key_data['requests_limit']:
            return None, "API key limit exceeded"
        
        return key_data, None
    
    def use_request(self, api_key):
        """Increment request count for a key"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        if key_hash in self.keys:
            self.keys[key_hash]['requests_used'] += 1
    
    def get_key_info(self, api_key):
        """Get information about an API key"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        return self.keys.get(key_hash)

# Global instance
api_key_manager = APIKey()
