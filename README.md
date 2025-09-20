# Neo4j Code Repository Ingestion Tool

A Python tool that parses code repositories and creates a graph representation in Neo4j Aura for visualization and analysis.

## Features

- **AST-based Parsing**: Uses Python's `ast` module to parse source code
- **Graph Modeling**: Creates nodes for files, functions, and classes with relationships
- **Relationship Extraction**: Identifies imports, function calls, and definitions
- **Neo4j Integration**: Direct integration with Neo4j Aura using official driver
- **Modular Design**: Clean separation of concerns across multiple modules

## Project Structure

```
neograph/
├── ingest.py          # Main CLI entry point
├── config.py          # Configuration and environment variables
├── models.py          # Data models (FileNode, FunctionNode, etc.)
├── parser.py          # Repository parsing logic
├── ingester.py        # Neo4j database operations
├── .env.example       # Example environment configuration
└── README.md          # This file
```

## Installation

### Required Packages

Install the following Python packages:

```bash
pip install neo4j python-dotenv
```

- `neo4j` - Official Neo4j driver for Python (required)
- `python-dotenv` - Environment variable management (optional but recommended)

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your Neo4j Aura credentials:
   ```env
   NEO4J_URI=neo4j+s://your-aura-id.databases.neo4j.io
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your-password
   ```

## Usage

### Basic Usage

```bash
python ingest.py /path/to/your/repository
```

### Advanced Usage

```bash
# Check configuration
python ingest.py --config-check

# Override connection settings
python ingest.py ./repo --uri neo4j+s://abc123.databases.neo4j.io --password mypassword

# Get help
python ingest.py --help
```

## Graph Schema

### Nodes

- **File** `(:File {path, relative_path})`
  - Represents Python source files
  - `path`: Relative path from repository root

- **Function** `(:Function {id, name, line_number})`
  - Represents function definitions
  - `id`: Unique identifier (file_path::function_name)

- **Class** `(:Class {id, name, line_number})`
  - Represents class definitions
  - `id`: Unique identifier (file_path::class_name)

### Relationships

- **DEFINES**: `(File)-[:DEFINES]->(Function|Class)`
  - Links files to the functions/classes they define

- **IMPORTS**: `(File)-[:IMPORTS {name}]->(File)`
  - Links files that import from other files
  - `name`: Import statement details

- **CALLS**: `(Function)-[:CALLS]->(Function)`
  - Links functions that call other functions

### Constraints

The tool automatically creates these constraints:

```cypher
CREATE CONSTRAINT file_id IF NOT EXISTS FOR (f:File) REQUIRE f.path IS UNIQUE;
CREATE CONSTRAINT func_id IF NOT EXISTS FOR (fn:Function) REQUIRE fn.id IS UNIQUE;
CREATE CONSTRAINT class_id IF NOT EXISTS FOR (c:Class) REQUIRE c.id IS UNIQUE;
```

## Example Queries

Once data is ingested, you can run these queries in Neo4j Browser:

```cypher
// Find all files in the repository
MATCH (f:File) RETURN f.path

// Find functions that call the most other functions
MATCH (fn:Function)-[:CALLS]->(called:Function)
WITH fn, count(called) as call_count
ORDER BY call_count DESC
RETURN fn.name, call_count LIMIT 10

// Find import relationships
MATCH (from:File)-[r:IMPORTS]->(to:File)
RETURN from.path, r.name, to.path

// Find files that define the most functions
MATCH (f:File)-[:DEFINES]->(fn:Function)
WITH f, count(fn) as func_count
ORDER BY func_count DESC
RETURN f.path, func_count LIMIT 10
```

## Error Handling

- The tool validates Neo4j connection before starting
- Individual file parsing errors are logged but don't stop the process
- Configuration validation ensures required settings are present
- Proper cleanup of database connections

## Limitations

- Only processes `.py` files
- Function call detection is based on AST analysis (may miss dynamic calls)
- Import resolution is approximate (converts module names to file paths)
- Skips common directories (`.git`, `__pycache__`, `venv`, etc.)

## Development

The codebase is organized into modules for easy maintenance:

- `config.py`: Environment and configuration management
- `models.py`: Data structures for repository elements
- `parser.py`: AST parsing and code analysis
- `ingester.py`: Neo4j database operations
- `ingest.py`: CLI interface and orchestration
