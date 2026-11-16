"""
JSON file storage backend for Student records.

Handles serialization, deserialization, and file I/O with atomic writes.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from threading import RLock
from typing import Any

from .exceptions import StorageError
from .student import Student


class JSONStorage:
    """
    Thread-safe JSON file storage for Student objects.

    Features:
    - Atomic writes (write to temp file, then rename)
    - Automatic directory creation
    - Pretty-printed JSON for readability
    - Lazy loading (loads on first access)
    """

    def __init__(self, file_path: str | Path):
        """
        Initialize storage.

        Args:
            file_path: Path to JSON file (created if missing)
        """
        self._path = Path(file_path).resolve()
        self._lock = RLock()
        self._data: dict[str, dict[str, Any]] | None = None
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """Create file with empty object if it doesn't exist."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._atomic_write({})

    def _load(self) -> dict[str, dict[str, Any]]:
        """Load data from file (cached after first load)."""
        with self._lock:
            if self._data is not None:
                return self._data

            try:
                content = self._path.read_text(encoding="utf-8")
                self._data = json.loads(content) if content.strip() else {}
            except json.JSONDecodeError:
                self._data = {}
            except OSError as e:
                raise StorageError(
                    f"Failed to read storage file: {e}",
                    operation="load",
                    path=str(self._path)
                ) from e

            return self._data

    def _atomic_write(self, data: dict[str, dict[str, Any]]) -> None:
        """Write data atomically using temp file + rename."""
        with self._lock:
            tmp_path: Path | None = None
            try:
                # Write to temp file in same directory (for atomic rename)
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    encoding="utf-8",
                    dir=self._path.parent,
                    delete=False,
                    suffix=".tmp"
                ) as tmp:
                    json.dump(data, tmp, indent=2, ensure_ascii=False)
                    tmp_path = Path(tmp.name)

                # Atomic replace
                tmp_path.replace(self._path)
                self._data = data
            except OSError as e:
                raise StorageError(
                    f"Failed to write storage file: {e}",
                    operation="write",
                    path=str(self._path)
                ) from e
            finally:
                if tmp_path is not None:
                    try:
                        tmp_path.unlink(missing_ok=True)
                    except OSError:
                        pass

    # ─── Public API ──────────────────────────────────────────────

    def get_all(self) -> dict[str, Student]:
        """Return all students as {id: Student} dict."""
        raw = self._load()
        return {sid: Student.from_dict(sdata) for sid, sdata in raw.items()}

    def get(self, student_id: str) -> Student | None:
        """Get a single student by ID, or None if not found."""
        raw = self._load()
        if student_id not in raw:
            return None
        return Student.from_dict(raw[student_id])

    def exists(self, student_id: str) -> bool:
        """Check if student exists (without loading full object)."""
        raw = self._load()
        return student_id in raw

    def add(self, student: Student) -> None:
        """Add a new student. Raises if ID already exists."""
        with self._lock:
            raw = self._load()
            if student.id in raw:
                raise StorageError(
                    f"Student {student.id} already exists",
                    operation="add",
                    path=str(self._path)
                )
            raw[student.id] = student.to_dict()
            self._atomic_write(raw)

    def update(self, student: Student) -> None:
        """Update existing student. Raises if not found."""
        with self._lock:
            raw = self._load()
            if student.id not in raw:
                raise StorageError(
                    f"Student {student.id} not found for update",
                    operation="update",
                    path=str(self._path)
                )
            raw[student.id] = student.to_dict()
            self._atomic_write(raw)

    def delete(self, student_id: str) -> bool:
        """
        Delete a student by ID.

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            raw = self._load()
            if student_id not in raw:
                return False
            del raw[student_id]
            self._atomic_write(raw)
            return True

    def clear(self) -> int:
        """Remove all students. Returns count of removed records."""
        with self._lock:
            count = len(self._load())
            self._atomic_write({})
            return count

    def count(self) -> int:
        """Return total number of students."""
        return len(self._load())

    # ─── Search Helpers ──────────────────────────────────────────

    def search_by_email(self, email: str) -> Student | None:
        """Find student by email (case-insensitive)."""
        email_lower = email.lower()
        for student in self.get_all().values():
            if student.email.lower() == email_lower:
                return student
        return None

    def search_by_name(self, first_name: str | None = None, last_name: str | None = None) -> list[Student]:
        """Find students matching name (case-insensitive, partial)."""
        results = []
        first_lower = first_name.lower() if first_name else None
        last_lower = last_name.lower() if last_name else None

        for student in self.get_all().values():
            if first_lower and first_lower not in student.first_name.lower():
                continue
            if last_lower and last_lower not in student.last_name.lower():
                continue
            results.append(student)

        return results
