"""
Test module for code review workflow demonstration
This file intentionally contains issues for code review practice
"""

import sqlite3
import os

# Issue 1: Hardcoded credentials
DB_PASSWORD = "super_secret_password123"
API_KEY = "sk-1234567890abcdef"

def get_user(user_id):
    """Get user from database - has SQL injection vulnerability"""
    # Issue 2: SQL injection via f-string
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = f"SELECT * FROM users WHERE id = {user_id}"  # VULNERABLE!
    cursor.execute(query)
    return cursor.fetchone()

def process_items(items):
    """Process items - has performance issue"""
    # Issue 3: N+1 query pattern
    results = []
    for item in items:
        # This creates a query per item (N+1 problem)
        conn = sqlite3.connect('items.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM details WHERE item_id = {item['id']}")
        results.append(cursor.fetchone())
    return results

def calculate_total(numbers):
    """Calculate total - inefficient algorithm"""
    # Issue 4: Inefficient - O(n²) when O(n) is possible
    total = 0
    for i in range(len(numbers)):
        for j in range(i + 1):
            total += numbers[j]
    return total

def read_config(config_path):
    """Read config file - no error handling"""
    # Issue 5: No error handling, no input validation
    # Issue 6: Path traversal vulnerability
    with open(config_path, 'r') as f:
        return f.read()

def authenticate(username, password):
    """Authenticate user - multiple issues"""
    # Issue 7: Hardcoded credentials comparison
    if username == "admin" and password == "admin123":
        return True
    # Issue 8: Timing attack vulnerability
    elif password == DB_PASSWORD:
        return True
    return False

class DataProcessor:
    """Data processor with state management issues"""
    
    # Issue 9: Mutable default argument
    def __init__(self, data=[], cache={}):
        self.data = data
        self.cache = cache
    
    # Issue 10: No type hints, no docstring
    def process(self, input_data):
        result = []
        for item in input_data:
            if item > 0:
                result.append(item * 2)
        return result
    
    # Issue 11: Bare except clause
    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                self.data = eval(f.read())  # Issue 12: eval() is dangerous!
        except:
            pass  # Silent failure
    
    # Issue 13: No validation on user input
    def query(self, user_query):
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        # Direct string interpolation - SQL injection
        cursor.execute(f"SELECT * FROM data WHERE query = '{user_query}'")
        return cursor.fetchall()

# Issue 14: Global state modification
GLOBAL_CACHE = {}

def cache_result(key, value):
    """Cache a result - thread unsafe"""
    GLOBAL_CACHE[key] = value  # No locking!

def get_cached(key):
    """Get cached value - no existence check"""
    return GLOBAL_CACHE[key]  # Will raise KeyError if missing
