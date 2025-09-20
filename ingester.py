"""
Neo4j database operations module for ingesting repository data.
"""

from typing import List, Dict, Tuple
from neo4j import GraphDatabase

from models import (
    FileNode, FunctionNode, ClassNode, ImportRelation, 
    CallRelation, RepositoryData
)


class Neo4jIngester:
    """Handles ingestion of parsed data into Neo4j."""
    
    def __init__(self, uri: str, auth: Tuple[str, str]):
        self.driver = GraphDatabase.driver(uri, auth=auth)
    
    def close(self):
        """Close the database connection."""
        self.driver.close()
    
    def test_connection(self) -> bool:
        """Test the Neo4j connection."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
    
    def create_constraints(self) -> None:
        """Create necessary constraints in Neo4j."""
        constraints = [
            "CREATE CONSTRAINT file_id IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE",
            "CREATE CONSTRAINT func_id IF NOT EXISTS FOR (fn:Function) REQUIRE fn.id IS UNIQUE",
            "CREATE CONSTRAINT class_id IF NOT EXISTS FOR (c:Class) REQUIRE c.id IS UNIQUE"
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                    print(f"✓ Constraint created/verified: {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")
                except Exception as e:
                    print(f"⚠ Constraint operation result: {e}")
    
    def clear_database(self) -> None:
        """Clear all nodes and relationships."""
        with self.driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            node_count = result.single()["node_count"]
            
            if node_count > 0:
                session.run("MATCH (n) DETACH DELETE n")
                print(f"✓ Cleared {node_count} existing nodes from database")
            else:
                print("✓ Database is already empty")
    
    def ingest_files(self, files: List[FileNode]) -> None:
        """Ingest file nodes into Neo4j."""
        if not files:
            print("No files to ingest")
            return
            
        with self.driver.session() as session:
            for file_node in files:
                session.run(
                    "MERGE (f:File {path: $path, relative_path: $relative_path})",
                    path=file_node.relative_path,
                    relative_path=file_node.relative_path
                )
        print(f"✓ Ingested {len(files)} file nodes")
    
    def ingest_functions(self, functions: List[FunctionNode]) -> None:
        """Ingest function nodes and their relationships to files."""
        if not functions:
            print("No functions to ingest")
            return
            
        with self.driver.session() as session:
            for func in functions:
                # Create function node
                session.run(
                    "MERGE (fn:Function {id: $id, name: $name, line_number: $line_number})",
                    id=func.id,
                    name=func.name,
                    line_number=func.line_number
                )
                
                # Create relationship to file
                session.run(
                    """
                    MATCH (f:File {path: $file_path})
                    MATCH (fn:Function {id: $func_id})
                    MERGE (f)-[:DEFINES]->(fn)
                    """,
                    file_path=func.file_path,
                    func_id=func.id
                )
        print(f"✓ Ingested {len(functions)} function nodes")
    
    def ingest_classes(self, classes: List[ClassNode]) -> None:
        """Ingest class nodes and their relationships to files."""
        if not classes:
            print("No classes to ingest")
            return
            
        with self.driver.session() as session:
            for cls in classes:
                # Create class node
                session.run(
                    "MERGE (c:Class {id: $id, name: $name, line_number: $line_number})",
                    id=cls.id,
                    name=cls.name,
                    line_number=cls.line_number
                )
                
                # Create relationship to file
                session.run(
                    """
                    MATCH (f:File {path: $file_path})
                    MATCH (c:Class {id: $class_id})
                    MERGE (f)-[:DEFINES]->(c)
                    """,
                    file_path=cls.file_path,
                    class_id=cls.id
                )
        print(f"✓ Ingested {len(classes)} class nodes")
    
    def ingest_imports(self, imports: List[ImportRelation]) -> None:
        """Ingest import relationships between files."""
        if not imports:
            print("No imports to ingest")
            return
            
        with self.driver.session() as session:
            import_count = 0
            for imp in imports:
                result = session.run(
                    """
                    MATCH (from_file:File {path: $from_file})
                    OPTIONAL MATCH (to_file:File {path: $to_file})
                    WITH from_file, to_file, $import_name as import_name
                    WHERE to_file IS NOT NULL
                    MERGE (from_file)-[:IMPORTS {name: import_name}]->(to_file)
                    RETURN count(*) as created
                    """,
                    from_file=imp.from_file,
                    to_file=imp.to_file,
                    import_name=imp.import_name
                )
                record = result.single()
                if record and record["created"] > 0:
                    import_count += 1
        print(f"✓ Ingested {import_count} import relationships")
    
    def ingest_calls(self, calls: List[CallRelation], function_map: Dict[str, str]) -> None:
        """Ingest function call relationships."""
        if not calls:
            print("No function calls to ingest")
            return
            
        with self.driver.session() as session:
            call_count = 0
            for call in calls:
                # Try to resolve the called function
                to_function_id = function_map.get(call.to_function)
                if to_function_id:
                    result = session.run(
                        """
                        MATCH (from_fn:Function {id: $from_function})
                        MATCH (to_fn:Function {id: $to_function})
                        MERGE (from_fn)-[:CALLS]->(to_fn)
                        RETURN count(*) as created
                        """,
                        from_function=call.from_function,
                        to_function=to_function_id
                    )
                    record = result.single()
                    if record and record["created"] > 0:
                        call_count += 1
        print(f"✓ Ingested {call_count} function call relationships")
    
    def ingest_repository_data(self, data: RepositoryData, clear_existing: bool = True) -> None:
        """Ingest all parsed repository data into Neo4j."""
        print("Starting Neo4j ingestion...")
        
        if not self.test_connection():
            raise Exception("Failed to connect to Neo4j database")
        
        if clear_existing:
            self.clear_database()
        
        self.create_constraints()
        self.ingest_files(data.files)
        self.ingest_functions(data.functions)
        self.ingest_classes(data.classes)
        self.ingest_imports(data.imports)
        self.ingest_calls(data.calls, data.function_map)
        
        print("✓ Neo4j ingestion completed successfully!")