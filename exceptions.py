"""
Custom exceptions for the Student Management System.

Exception hierarchy:
    StudentManagementError (base)
    ├── StudentNotFoundError
    ├── DuplicateStudentError
    ├── ValidationError
    └── StorageError
"""


class StudentManagementError(Exception):
    """Base exception for all student management errors."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class StudentNotFoundError(StudentManagementError):
    """Raised when a student with the given ID is not found."""

    def __init__(self, student_id: str):
        super().__init__(
            "Student not found",
            {"student_id": student_id}
        )
        self.student_id = student_id


class DuplicateStudentError(StudentManagementError):
    """Raised when attempting to add a student that already exists."""

    def __init__(self, student_id: str, field: str = "id"):
        super().__init__(
            "Duplicate student",
            {"student_id": student_id, "field": field}
        )
        self.student_id = student_id
        self.field = field


class ValidationError(StudentManagementError):
    """Raised when student data fails validation."""

    def __init__(self, message: str, field: str | None = None, value: str | None = None):
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = value
        super().__init__(message, details)
        self.field = field
        self.value = value


class StorageError(StudentManagementError):
    """Raised when storage operations fail."""

    def __init__(self, message: str, operation: str | None = None, path: str | None = None):
        details = {}
        if operation:
            details["operation"] = operation
        if path:
            details["path"] = path
        super().__init__(message, details)
        self.operation = operation
        self.path = path
