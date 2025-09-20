"""
Data models for representing repository structure elements.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class FileNode:
    """Represents a Python file in the repository."""
    path: str
    relative_path: str


@dataclass
class FunctionNode:
    """Represents a function definition."""
    id: str
    name: str
    file_path: str
    line_number: int


@dataclass
class ClassNode:
    """Represents a class definition."""
    id: str
    name: str
    file_path: str
    line_number: int


@dataclass
class ImportRelation:
    """Represents an import relationship between files."""
    from_file: str
    to_file: str
    import_name: str


@dataclass
class CallRelation:
    """Represents a function call relationship."""
    from_function: str
    to_function: str


@dataclass
class RepositoryData:
    """Container for all parsed repository data."""
    files: List[FileNode]
    functions: List[FunctionNode]
    classes: List[ClassNode]
    imports: List[ImportRelation]
    calls: List[CallRelation]
    function_map: dict  # name -> id mapping
    
    def __post_init__(self):
        """Initialize empty collections if None."""
        if self.files is None:
            self.files = []
        if self.functions is None:
            self.functions = []
        if self.classes is None:
            self.classes = []
        if self.imports is None:
            self.imports = []
        if self.calls is None:
            self.calls = []
        if self.function_map is None:
            self.function_map = {}
    
    def summary(self) -> str:
        """Return a summary of the repository data."""
        return (f"Repository Data Summary: "
                f"{len(self.files)} files, "
                f"{len(self.functions)} functions, "
                f"{len(self.classes)} classes, "
                f"{len(self.imports)} imports, "
                f"{len(self.calls)} calls")