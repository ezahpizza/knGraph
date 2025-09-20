#!/usr/bin/env python3
"""
Neo4j Code Repository Ingestion Script

Parses Python repositories and creates a graph representation in Neo4j Aura.
Extracts files, functions, classes, and their relationships.
"""

import os
import sys
import argparse
from typing import Tuple

from config import Config
from parser import RepositoryParser
from ingester import Neo4jIngester


def ingest_repo(repo_path: str, neo4j_uri: str = None, neo4j_auth: Tuple[str, str] = None) -> None:
    """Main function to ingest a repository into Neo4j."""
    if not os.path.exists(repo_path):
        print(f"Error: Repository path '{repo_path}' does not exist")
        return
    
    # Use config defaults if not provided
    if neo4j_uri is None:
        neo4j_uri = Config.NEO4J_URI
    if neo4j_auth is None:
        neo4j_auth = Config.get_neo4j_auth()
    
    print(f"Starting ingestion of repository: {repo_path}")
    Config.print_config()
    
    # Validate configuration
    if not Config.validate_config():
        print("Please update your .env file with valid Neo4j credentials")
        return
    
    try:
        # Parse repository
        print("\n" + "="*50)
        print("PARSING REPOSITORY")
        print("="*50)
        parser = RepositoryParser(repo_path)
        data = parser.parse_repository()
        
        # Ingest into Neo4j
        print("\n" + "="*50)
        print("INGESTING INTO NEO4J")
        print("="*50)
        ingester = Neo4jIngester(neo4j_uri, neo4j_auth)
        try:
            ingester.ingest_repository_data(data)
            print("\n🎉 Repository ingestion completed successfully!")
        finally:
            ingester.close()
            
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        sys.exit(1)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ingest Python repository structure into Neo4j Aura",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python ingest.py ./my_repo
  python ingest.py ./my_repo --uri neo4j+s://abc123.databases.neo4j.io --password mypassword
  
Environment Variables (create .env file):
  NEO4J_URI=neo4j+s://your-aura-id.databases.neo4j.io
  NEO4J_USERNAME=neo4j
  NEO4J_PASSWORD=your-password
        """
    )
    parser.add_argument(
        "repo_path",
        help="Path to the Python repository to ingest"
    )
    parser.add_argument(
        "--uri",
        help="Neo4j connection URI (overrides .env file)"
    )
    parser.add_argument(
        "--username",
        help="Neo4j username (overrides .env file)"
    )
    parser.add_argument(
        "--password",
        help="Neo4j password (overrides .env file)"
    )
    parser.add_argument(
        "--config-check",
        action="store_true",
        help="Check configuration and exit"
    )
    
    args = parser.parse_args()
    
    # Handle config check
    if args.config_check:
        Config.print_config()
        if Config.validate_config():
            print("✓ Configuration is valid")
        else:
            print("❌ Configuration has issues")
        return
    
    # Build connection parameters
    neo4j_uri = args.uri or Config.NEO4J_URI
    neo4j_username = args.username or Config.NEO4J_USERNAME
    neo4j_password = args.password or Config.NEO4J_PASSWORD
    
    auth = (neo4j_username, neo4j_password)
    ingest_repo(args.repo_path, neo4j_uri, auth)


if __name__ == "__main__":
    main()