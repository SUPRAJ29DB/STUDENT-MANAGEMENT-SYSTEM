"""
Student data model with validation.

Uses dataclass for clean, type-safe data representation.
"""
from __future__ import annotations

import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True, slots=True)
class Student:
    """
    Immutable student record.

    Attributes:
        id: Unique identifier (UUID4 string)
        first_name: Student's given name (required, 1-50 chars)
        last_name: Student's family name (required, 1-50 chars)
        email: Email address (required, valid format)
        date_of_birth: Birth date (required, must be in past)
        enrollment_date: When student enrolled (defaults to today)
        grade: Current grade level (optional, 1-12)
        major: Field of study (optional, max 100 chars)
        gpa: Grade point average (optional, 0.0-4.0)
        is_active: Enrollment status (defaults to True)
        metadata: Extensible dict for additional fields
    """
    id: str
    first_name: str
    last_name: str
    email: str
    date_of_birth: str  # ISO format: YYYY-MM-DD
    enrollment_date: str = field(default_factory=lambda: date.today().isoformat())
    grade: int | None = None
    major: str | None = None
    gpa: float | None = None
    is_active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    # ─── Class Methods ────────────────────────────────────────────

    @classmethod
    def create(
        cls,
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
        Factory method to create a validated Student.

        Args:
            first_name: Given name (1-50 chars)
            last_name: Family name (1-50 chars)
            email: Valid email address
            date_of_birth: ISO date string (YYYY-MM-DD)
            enrollment_date: ISO date string (defaults to today)
            grade: Grade level 1-12
            major: Field of study (max 100 chars)
            gpa: GPA 0.0-4.0
            is_active: Enrollment status
            metadata: Additional fields
            student_id: Optional custom ID (generates UUID4 if omitted)

        Returns:
            Validated Student instance

        Raises:
            ValidationError: If any field fails validation
        """

        # Validate and normalize
        first_name = _validate_name(first_name, "first_name")
        last_name = _validate_name(last_name, "last_name")
        email = _validate_email(email)
        date_of_birth = _validate_date(date_of_birth, "date_of_birth", allow_future=False)
        enrollment_date = _validate_date(enrollment_date or date.today().isoformat(), "enrollment_date")
        grade = _validate_grade(grade)
        major = _validate_major(major)
        gpa = _validate_gpa(gpa)
        student_id = student_id or str(uuid.uuid4())
        metadata = metadata or {}

        return cls(
            id=student_id,
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
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Student:
        """Create Student from dictionary (e.g., JSON deserialization)."""
        return cls(**data)

    # ─── Instance Methods ─────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @property
    def full_name(self) -> str:
        """Return 'First Last' format."""
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self) -> int:
        """Calculate age from date of birth."""
        dob = date.fromisoformat(self.date_of_birth)
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    def update(self, **kwargs) -> Student:
        """
        Return a new Student with updated fields (immutable update pattern).

        Args:
            **kwargs: Fields to update (first_name, last_name, email, etc.)

        Returns:
            New Student instance with changes applied

        Raises:
            ValidationError: If any updated field fails validation
        """
        data = self.to_dict()
        # Preserve original ID (don't allow changing it)
        student_id = data.pop("id")
        data.update(kwargs)
        return Student.create(student_id=student_id, **data)

    def __str__(self) -> str:
        status = "Active" if self.is_active else "Inactive"
        return f"{self.full_name} ({self.id[:8]}) - {status}"


# ─── Validation Helpers ────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Match letters (including Unicode), spaces, hyphens, apostrophes
_NAME_RE = re.compile(r"^[\w\s'-]+$", re.UNICODE)


def _validate_name(name: str, field_name: str) -> str:
    """Validate and normalize a name field."""
    from .exceptions import ValidationError

    if not isinstance(name, str):
        raise ValidationError(f"{field_name} must be a string", field=field_name, value=str(name))

    name = name.strip()
    if not name:
        raise ValidationError(f"{field_name} cannot be empty", field=field_name)
    if len(name) > 50:
        raise ValidationError(f"{field_name} cannot exceed 50 characters", field=field_name, value=name)
    if not _NAME_RE.match(name):
        raise ValidationError(
            f"{field_name} contains invalid characters (letters, spaces, hyphens, apostrophes only)",
            field=field_name,
            value=name
        )
    return name.title()


def _validate_email(email: str) -> str:
    """Validate and normalize email."""
    from .exceptions import ValidationError

    if not isinstance(email, str):
        raise ValidationError("Email must be a string", field="email", value=str(email))

    email = email.strip().lower()
    if not email:
        raise ValidationError("Email cannot be empty", field="email")
    if not _EMAIL_RE.match(email):
        raise ValidationError("Invalid email format", field="email", value=email)
    if len(email) > 254:
        raise ValidationError("Email cannot exceed 254 characters", field="email", value=email)
    return email


def _validate_date(date_str: str | None, field_name: str, allow_future: bool = True) -> str:
    """Validate ISO date string."""
    from .exceptions import ValidationError

    if date_str is None:
        raise ValidationError(f"{field_name} is required", field=field_name)

    if not isinstance(date_str, str):
        raise ValidationError(f"{field_name} must be a string (YYYY-MM-DD)", field=field_name, value=str(date_str))

    try:
        parsed = date.fromisoformat(date_str)
    except ValueError:
        raise ValidationError(
            f"{field_name} must be a valid date (YYYY-MM-DD)",
            field=field_name,
            value=date_str,
        ) from None

    if not allow_future and parsed > date.today():
        raise ValidationError(f"{field_name} cannot be in the future", field=field_name, value=date_str)

    return parsed.isoformat()


def _validate_grade(grade: int | None) -> int | None:
    """Validate grade level (1-12)."""
    from .exceptions import ValidationError

    if grade is None:
        return None
    if not isinstance(grade, int):
        raise ValidationError("Grade must be an integer", field="grade", value=str(grade))
    if not 1 <= grade <= 12:
        raise ValidationError("Grade must be between 1 and 12", field="grade", value=str(grade))
    return grade


def _validate_major(major: str | None) -> str | None:
    """Validate major field."""
    from .exceptions import ValidationError

    if major is None:
        return None
    if not isinstance(major, str):
        raise ValidationError("Major must be a string", field="major", value=str(major))
    major = major.strip()
    if not major:
        return None
    if len(major) > 100:
        raise ValidationError("Major cannot exceed 100 characters", field="major", value=major)
    return major


def _validate_gpa(gpa: float | None) -> float | None:
    """Validate GPA (0.0-4.0)."""
    from .exceptions import ValidationError

    if gpa is None:
        return None
    if not isinstance(gpa, (int, float)):
        raise ValidationError("GPA must be a number", field="gpa", value=str(gpa))
    gpa = float(gpa)
    if not 0.0 <= gpa <= 4.0:
        raise ValidationError("GPA must be between 0.0 and 4.0", field="gpa", value=str(gpa))
    return round(gpa, 2)
