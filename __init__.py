"""
Student Management System - Package initialization.
"""
from .exceptions import (
    DuplicateStudentError,
    StorageError,
    StudentManagementError,
    StudentNotFoundError,
    ValidationError,
)
from .manager import SearchCriteria, StudentManager
from .storage import JSONStorage
from .student import Student

__all__ = [
    "Student",
    "StudentManager",
    "SearchCriteria",
    "JSONStorage",
    "StudentManagementError",
    "StudentNotFoundError",
    "DuplicateStudentError",
    "ValidationError",
    "StorageError",
]

__version__ = "1.0.0"
