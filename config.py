"""
Configuration module for Neo4j Code Repository Ingestion Script.
Handles environment variables and application settings.
"""

import os
from typing import Tuple

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv is optional - will use system environment variables only
    pass


class Config:
    """Configuration settings for the application."""
    
    # Neo4j connection settings
    NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://your-aura-id.databases.neo4j.io")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your-password")
    
    # Repository parsing settings
    IGNORE_DIRECTORIES = {'.git', '__pycache__', 'venv', 'env', '.venv', 'node_modules'}
    PYTHON_FILE_EXTENSIONS = {'.py'}
    
    @classmethod
    def get_neo4j_auth(cls) -> Tuple[str, str]:
        """Get Neo4j authentication tuple."""
        return (cls.NEO4J_USERNAME, cls.NEO4J_PASSWORD)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate that required configuration is present."""
        if cls.NEO4J_URI.endswith("your-aura-id.databases.neo4j.io"):
            print("Warning: NEO4J_URI appears to be using default value. Please set in .env file.")
            return False
        
        if cls.NEO4J_PASSWORD == "your-password":
            print("Warning: NEO4J_PASSWORD appears to be using default value. Please set in .env file.")
            return False
        
        return True
    
    @classmethod
    def print_config(cls) -> None:
        """Print current configuration (without password)."""
        print("Current Configuration:")
        print(f"  NEO4J_URI: {cls.NEO4J_URI}")
        print(f"  NEO4J_USERNAME: {cls.NEO4J_USERNAME}")
        print(f"  NEO4J_PASSWORD: {'*' * len(cls.NEO4J_PASSWORD) if cls.NEO4J_PASSWORD else 'Not set'}")