"""
StudentManager - Core business logic for student management.

Provides high-level CRUD operations with validation, search, and error handling.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .exceptions import (
    DuplicateStudentError,
    StorageError,
    StudentNotFoundError,
)
from .storage import JSONStorage
from .student import Student


@dataclass(frozen=True, slots=True)
class SearchCriteria:
    """Search filter criteria for finding students."""
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    grade: int | None = None
    major: str | None = None
    is_active: bool | None = None
    min_gpa: float | None = None
    max_gpa: float | None = None

    def matches(self, student: Student) -> bool:
        """Check if student matches all non-None criteria."""
        if self.first_name and self.first_name.lower() not in student.first_name.lower():
            return False
        if self.last_name and self.last_name.lower() not in student.last_name.lower():
            return False
        if self.email and self.email.lower() != student.email.lower():
            return False
        if self.grade is not None and student.grade != self.grade:
            return False
        if self.major and self.major.lower() not in (student.major or "").lower():
            return False
        if self.is_active is not None and student.is_active != self.is_active:
            return False
        if self.min_gpa is not None and (student.gpa is None or student.gpa < self.min_gpa):
            return False
        if self.max_gpa is not None and (student.gpa is None or student.gpa > self.max_gpa):
            return False
        return True


class StudentManager:
    """
    Main entry point for student management operations.

    Encapsulates business logic, validation, and delegates persistence to JSONStorage.
    Thread-safe for concurrent read/write operations.
    """

    def __init__(self, storage_path: str | Path = "students.json"):
        """
        Initialize manager with JSON file storage.

        Args:
            storage_path: Path to JSON file for persistence
        """
        self._storage = JSONStorage(storage_path)

    # ─── CRUD Operations ─────────────────────────────────────────

    def add_student(
        self,
        first_name: str,
        last_name: str,
        email: str,
        date_of_birth: str,
        enrollment_date: str | None = None,
        grade: int | None = None,
        major: str | None = None,
        gpa: float | None = None,
        is_active: bool = True,
        metadata: dict[str, Any] | None = None,
        student_id: str | None = None,
    ) -> Student:
        """
        Add a new student.

        Args:
            first_name: Given name (1-50 chars)
            last_name: Family name (1-50 chars)
            email: Valid email (unique)
            date_of_birth: ISO date (YYYY-MM-DD)
            enrollment_date: ISO date (defaults to today)
            grade: Grade level 1-12
            major: Field of study (max 100 chars)
            gpa: GPA 0.0-4.0
            is_active: Enrollment status
            metadata: Additional fields
            student_id: Optional custom ID

        Returns:
            Created Student object

        Raises:
            ValidationError: If any field is invalid
            DuplicateStudentError: If email already exists
        """
        # Check email uniqueness
        if self._storage.search_by_email(email):
            raise DuplicateStudentError(email, field="email")

        # Create student (validates all fields)
        student = Student.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            date_of_birth=date_of_birth,
            enrollment_date=enrollment_date,
            grade=grade,
            major=major,
            gpa=gpa,
            is_active=is_active,
            metadata=metadata,
            student_id=student_id,
        )

        # Persist
        try:
            self._storage.add(student)
        except StorageError as e:
            if "already exists" in str(e):
                raise DuplicateStudentError(student.id, field="id") from e
            raise

        return student

    def remove_student(self, student_id: str) -> Student:
        """
        Remove a student by ID.

        Args:
            student_id: UUID of student to remove

        Returns:
            The removed Student object

        Raises:
            StudentNotFoundError: If student doesn't exist
        """
        student = self._storage.get(student_id)
        if not student:
            raise StudentNotFoundError(student_id)

        self._storage.delete(student_id)
        return student

    def get_student(self, student_id: str) -> Student:
        """
        Get a student by ID.

        Args:
            student_id: UUID of student

        Returns:
            Student object

        Raises:
            StudentNotFoundError: If student doesn't exist
        """
        student = self._storage.get(student_id)
        if not student:
            raise StudentNotFoundError(student_id)
        return student

    def update_student(self, student_id: str, **kwargs) -> Student:
        """
        Update student fields.

        Args:
            student_id: UUID of student to update
            **kwargs: Fields to update (first_name, last_name, email, etc.)

        Returns:
            Updated Student object

        Raises:
            StudentNotFoundError: If student doesn't exist
            ValidationError: If any updated field is invalid
            DuplicateStudentError: If email conflicts with another student
        """
        student = self.get_student(student_id)

        # Handle email uniqueness if email is being changed
        if "email" in kwargs and kwargs["email"] != student.email:
            if self._storage.search_by_email(kwargs["email"]):
                raise DuplicateStudentError(kwargs["email"], field="email")

        # Create updated student (validates)
        updated_student = student.update(**kwargs)

        # Persist
        self._storage.update(updated_student)
        return updated_student

    # ─── Search Operations ───────────────────────────────────────

    def search_students(self, criteria: SearchCriteria | None = None, **kwargs) -> list[Student]:
        """
        Search students matching criteria.

        Args:
            criteria: SearchCriteria object (or use kwargs)
            **kwargs: Alternative way to specify criteria

        Returns:
            List of matching students (empty if none)
        """
        if criteria is None:
            criteria = SearchCriteria(**kwargs)

        all_students = self._storage.get_all().values()
        return [s for s in all_students if criteria.matches(s)]

    def find_by_email(self, email: str) -> Student | None:
        """Find student by exact email (case-insensitive)."""
        return self._storage.search_by_email(email)

    def find_by_name(self, first_name: str | None = None, last_name: str | None = None) -> list[Student]:
        """Find students by name (partial, case-insensitive)."""
        return self._storage.search_by_name(first_name, last_name)

    def get_all_students(self) -> list[Student]:
        """Return all students (active and inactive)."""
        return list(self._storage.get_all().values())

    def get_active_students(self) -> list[Student]:
        """Return only active students."""
        return [s for s in self.get_all_students() if s.is_active]

    # ─── Utility Methods ─────────────────────────────────────────

    def count(self) -> int:
        """Total number of students."""
        return self._storage.count()

    def count_active(self) -> int:
        """Number of active students."""
        return len(self.get_active_students())

    def deactivate_student(self, student_id: str) -> Student:
        """Mark student as inactive."""
        return self.update_student(student_id, is_active=False)

    def activate_student(self, student_id: str) -> Student:
        """Mark student as active."""
        return self.update_student(student_id, is_active=True)

    def export_to_dict(self) -> dict[str, Any]:
        """Export all data as dictionary (for backup/serialization)."""
        return {
            "students": {sid: s.to_dict() for sid, s in self._storage.get_all().items()},
            "count": self.count(),
        }

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> StudentManager:
        """Create manager from existing JSON file."""
        return cls(file_path)
