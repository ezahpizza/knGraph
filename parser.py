"""
Repository parser module for extracting Python code structure using AST.
"""

import ast
import os
from pathlib import Path
from typing import List, Dict

from models import (
    FileNode, FunctionNode, ClassNode, ImportRelation, 
    CallRelation, RepositoryData
)
from config import Config


class RepositoryParser:
    """Parses Python repository structure using AST."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()
        self.data = RepositoryData([], [], [], [], [], {})
    
    def find_python_files(self) -> List[Path]:
        """Find all Python files in the repository."""
        python_files = []
        for root, dirs, files in os.walk(self.repo_path):
            # Skip ignore directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in Config.IGNORE_DIRECTORIES]
            
            for file in files:
                if any(file.endswith(ext) for ext in Config.PYTHON_FILE_EXTENSIONS):
                    python_files.append(Path(root) / file)
        
        return python_files
    
    def get_relative_path(self, file_path: Path) -> str:
        """Get relative path from repository root."""
        try:
            return str(file_path.relative_to(self.repo_path))
        except ValueError:
            return str(file_path)
    
    def parse_imports(self, tree: ast.AST, file_path: str) -> List[ImportRelation]:
        """Extract import statements from AST."""
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # Convert module name to potential file path
                    module_parts = alias.name.split('.')
                    potential_path = os.path.join(*module_parts) + '.py'
                    imports.append(ImportRelation(
                        from_file=file_path,
                        to_file=potential_path,
                        import_name=alias.name
                    ))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_parts = node.module.split('.')
                    potential_path = os.path.join(*module_parts) + '.py'
                    for alias in node.names:
                        imports.append(ImportRelation(
                            from_file=file_path,
                            to_file=potential_path,
                            import_name=f"{node.module}.{alias.name}"
                        ))
        
        return imports
    
    def parse_function_calls(self, tree: ast.AST, file_path: str) -> List[CallRelation]:
        """Extract function calls from AST."""
        calls = []
        
        class CallVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_function = None
                self.calls = []
            
            def visit_FunctionDef(self, node):
                # Update current function context
                old_func = self.current_function
                self.current_function = f"{file_path}::{node.name}"
                self.generic_visit(node)
                self.current_function = old_func
            
            def visit_AsyncFunctionDef(self, node):
                # Handle async functions
                old_func = self.current_function
                self.current_function = f"{file_path}::{node.name}"
                self.generic_visit(node)
                self.current_function = old_func
            
            def visit_Call(self, node):
                if self.current_function:
                    call_name = None
                    if isinstance(node.func, ast.Name):
                        call_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name):
                            call_name = f"{node.func.value.id}.{node.func.attr}"
                        else:
                            call_name = node.func.attr
                    
                    if call_name:
                        self.calls.append(CallRelation(
                            from_function=self.current_function,
                            to_function=call_name
                        ))
                
                self.generic_visit(node)
        
        visitor = CallVisitor()
        visitor.visit(tree)
        return visitor.calls
    
    def extract_functions_and_classes(self, tree: ast.AST, file_path: str) -> tuple:
        """Extract function and class definitions from AST."""
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_id = f"{file_path}::{node.name}"
                function_node = FunctionNode(
                    id=func_id,
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno
                )
                functions.append(function_node)
                self.data.function_map[node.name] = func_id
            
            elif isinstance(node, ast.ClassDef):
                class_id = f"{file_path}::{node.name}"
                class_node = ClassNode(
                    id=class_id,
                    name=node.name,
                    file_path=file_path,
                    line_number=node.lineno
                )
                classes.append(class_node)
        
        return functions, classes
    
    def parse_file(self, file_path: Path) -> bool:
        """Parse a single Python file and extract its structure."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            relative_path = self.get_relative_path(file_path)
            
            # Create file node
            file_node = FileNode(
                path=str(file_path),
                relative_path=relative_path
            )
            self.data.files.append(file_node)
            
            # Extract imports
            file_imports = self.parse_imports(tree, relative_path)
            self.data.imports.extend(file_imports)
            
            # Extract functions and classes
            functions, classes = self.extract_functions_and_classes(tree, relative_path)
            self.data.functions.extend(functions)
            self.data.classes.extend(classes)
            
            # Extract function calls
            file_calls = self.parse_function_calls(tree, relative_path)
            self.data.calls.extend(file_calls)
            
            return True
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return False
    
    def parse_repository(self) -> RepositoryData:
        """Parse the entire repository and return structured data."""
        python_files = self.find_python_files()
        print(f"Found {len(python_files)} Python files")
        
        success_count = 0
        for file_path in python_files:
            if self.parse_file(file_path):
                success_count += 1
        
        print(f"Successfully parsed {success_count}/{len(python_files)} files")
        print(self.data.summary())
        
        return self.data