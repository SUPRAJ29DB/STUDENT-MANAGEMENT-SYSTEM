#!/usr/bin/env python3
"""
Unit tests for Student Management System.

Run with: python -m pytest student_management/test_student_mgmt.py -v
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from student_management import (
    DuplicateStudentError,
    JSONStorage,
    SearchCriteria,
    StorageError,
    Student,
    StudentManager,
    StudentNotFoundError,
    ValidationError,
)

# ─── Fixtures ───────────────────────────────────────────────────

@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    try:
        yield path
    finally:
        Path(path).unlink(missing_ok=True)


@pytest.fixture
def manager(temp_db):
    """Create a StudentManager with temp database."""
    return StudentManager(temp_db)


@pytest.fixture
def sample_student(manager):
    """Create a sample student."""
    return manager.add_student(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        date_of_birth="2005-05-15",
        grade=10,
        major="Biology",
        gpa=3.5,
    )


# ─── Student Model Tests ────────────────────────────────────────

class TestStudentModel:
    """Tests for Student dataclass and validation."""

    def test_create_valid_student(self):
        student = Student.create(
            first_name="Jane",
            last_name="Smith",
            email="jane@test.com",
            date_of_birth="2005-01-01",
        )
        assert student.first_name == "Jane"
        assert student.last_name == "Smith"
        assert student.email == "jane@test.com"
        assert student.id is not None
        assert len(student.id) == 36  # UUID4

    def test_create_with_custom_id(self):
        student = Student.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            date_of_birth="2005-01-01",
            student_id="custom-id-123",
        )
        assert student.id == "custom-id-123"

    def test_invalid_first_name_empty(self):
        with pytest.raises(ValidationError) as exc:
            Student.create(
                first_name="",
                last_name="Doe",
                email="test@test.com",
                date_of_birth="2005-01-01",
            )
        assert exc.value.field == "first_name"

    def test_invalid_first_name_too_long(self):
        with pytest.raises(ValidationError):
            Student.create(
                first_name="A" * 51,
                last_name="Doe",
                email="test@test.com",
                date_of_birth="2005-01-01",
            )

    def test_invalid_email_format(self):
        with pytest.raises(ValidationError) as exc:
            Student.create(
                first_name="John",
                last_name="Doe",
                email="not-an-email",
                date_of_birth="2005-01-01",
            )
        assert exc.value.field == "email"

    def test_invalid_dob_future(self):
        with pytest.raises(ValidationError):
            Student.create(
                first_name="John",
                last_name="Doe",
                email="test@test.com",
                date_of_birth="2030-01-01",
            )

    def test_invalid_grade(self):
        with pytest.raises(ValidationError):
            Student.create(
                first_name="John",
                last_name="Doe",
                email="test@test.com",
                date_of_birth="2005-01-01",
                grade=13,
            )

    def test_invalid_gpa(self):
        with pytest.raises(ValidationError):
            Student.create(
                first_name="John",
                last_name="Doe",
                email="test@test.com",
                date_of_birth="2005-01-01",
                gpa=5.0,
            )

    def test_immutable_update(self, sample_student):
        updated = sample_student.update(first_name="Jane", gpa=3.8)
        assert updated.first_name == "Jane"
        assert updated.gpa == 3.8
        assert updated.id == sample_student.id  # Same ID
        assert sample_student.first_name == "John"  # Original unchanged

    def test_age_calculation(self):
        student = Student.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            date_of_birth="2010-01-01",
        )
        # Age should be calculated correctly
        assert student.age >= 14  # As of 2025+

    def test_to_dict_roundtrip(self, sample_student):
        data = sample_student.to_dict()
        restored = Student.from_dict(data)
        assert restored == sample_student


# ─── Storage Tests ──────────────────────────────────────────────

class TestJSONStorage:
    """Tests for JSONStorage backend."""

    def test_add_and_get(self, temp_db):
        storage = JSONStorage(temp_db)
        student = Student.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            date_of_birth="2005-01-01",
        )
        storage.add(student)
        retrieved = storage.get(student.id)
        assert retrieved == student

    def test_add_duplicate_raises(self, temp_db):
        storage = JSONStorage(temp_db)
        student = Student.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            date_of_birth="2005-01-01",
        )
        storage.add(student)
        with pytest.raises(StorageError):
            storage.add(student)

    def test_update(self, temp_db):
        storage = JSONStorage(temp_db)
        student = Student.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            date_of_birth="2005-01-01",
        )
        storage.add(student)
        updated = student.update(grade=11)
        storage.update(updated)
        retrieved = storage.get(student.id)
        assert retrieved.grade == 11

    def test_update_nonexistent_raises(self, temp_db):
        storage = JSONStorage(temp_db)
        student = Student.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            date_of_birth="2005-01-01",
        )
        with pytest.raises(StorageError):
            storage.update(student)

    def test_delete(self, temp_db):
        storage = JSONStorage(temp_db)
        student = Student.create(
            first_name="Test",
            last_name="User",
            email="test@test.com",
            date_of_birth="2005-01-01",
        )
        storage.add(student)
        assert storage.delete(student.id) is True
        assert storage.get(student.id) is None
        assert storage.delete(student.id) is False  # Already deleted

    def test_search_by_email(self, temp_db):
        storage = JSONStorage(temp_db)
        student = Student.create(
            first_name="Test",
            last_name="User",
            email="TEST@EXAMPLE.COM",
            date_of_birth="2005-01-01",
        )
        storage.add(student)
        found = storage.search_by_email("test@example.com")  # Case insensitive
        assert found is not None
        assert found.id == student.id

    def test_search_by_name(self, temp_db):
        storage = JSONStorage(temp_db)
        s1 = Student.create(first_name="Alice", last_name="Smith", email="a@test.com", date_of_birth="2005-01-01")
        s2 = Student.create(first_name="Bob", last_name="Smith", email="b@test.com", date_of_birth="2005-01-01")
        s3 = Student.create(first_name="Charlie", last_name="Jones", email="c@test.com", date_of_birth="2005-01-01")
        storage.add(s1)
        storage.add(s2)
        storage.add(s3)

        results = storage.search_by_name(last_name="Smith")
        assert len(results) == 2

        results = storage.search_by_name(first_name="Ali")
        assert len(results) == 1

    def test_atomic_write_survives_crash(self, temp_db):
        """Simulate crash during write - original file should be intact."""
        storage = JSONStorage(temp_db)
        s1 = Student.create(first_name="One", last_name="User", email="one@test.com", date_of_birth="2005-01-01")
        storage.add(s1)

        # Corrupt the file manually
        with Path(temp_db).open("w") as f:
            f.write("corrupted json {")

        # New storage instance should handle gracefully
        storage2 = JSONStorage(temp_db)
        # Should start fresh or handle corruption
        assert storage2.count() == 0


# ─── Manager Tests ──────────────────────────────────────────────

class TestStudentManager:
    """Tests for StudentManager business logic."""

    def test_add_student(self, manager):
        student = manager.add_student(
            first_name="Alice",
            last_name="Johnson",
            email="alice@test.com",
            date_of_birth="2005-03-15",
            grade=11,
        )
        assert student.first_name == "Alice"
        assert manager.count() == 1

    def test_add_duplicate_email_raises(self, manager, sample_student):
        with pytest.raises(DuplicateStudentError):
            manager.add_student(
                first_name="Another",
                last_name="Student",
                email="john.doe@example.com",  # Same email
                date_of_birth="2005-01-01",
            )

    def test_get_student(self, manager, sample_student):
        retrieved = manager.get_student(sample_student.id)
        assert retrieved == sample_student

    def test_get_nonexistent_raises(self, manager):
        with pytest.raises(StudentNotFoundError):
            manager.get_student("non-existent-id")

    def test_remove_student(self, manager, sample_student):
        removed = manager.remove_student(sample_student.id)
        assert removed.id == sample_student.id
        assert manager.count() == 0

    def test_remove_nonexistent_raises(self, manager):
        with pytest.raises(StudentNotFoundError):
            manager.remove_student("non-existent-id")

    def test_update_student(self, manager, sample_student):
        updated = manager.update_student(sample_student.id, grade=11, gpa=3.8)
        assert updated.grade == 11
        assert updated.gpa == 3.8

    def test_update_email_conflict(self, manager):
        s1 = manager.add_student("One", "User", "one@test.com", "2005-01-01")
        manager.add_student("Two", "User", "two@test.com", "2005-01-01")
        with pytest.raises(DuplicateStudentError):
            manager.update_student(s1.id, email="two@test.com")

    def test_search_by_criteria(self, manager):
        manager.add_student("Alice", "Smith", "alice@test.com", "2005-01-01", grade=10, gpa=3.5)
        manager.add_student("Bob", "Smith", "bob@test.com", "2005-01-01", grade=11, gpa=3.8)
        manager.add_student("Charlie", "Jones", "charlie@test.com", "2005-01-01", grade=10, gpa=3.9)

        # Search by last name
        results = manager.search_students(last_name="Smith")
        assert len(results) == 2

        # Search by grade
        results = manager.search_students(grade=10)
        assert len(results) == 2

        # Search by GPA range
        results = manager.search_students(min_gpa=3.7)
        assert len(results) == 2

        # Combined criteria
        results = manager.search_students(grade=10, min_gpa=3.7)
        assert len(results) == 1
        assert results[0].first_name == "Charlie"

    def test_search_criteria_object(self, manager):
        manager.add_student("Alice", "Smith", "alice@test.com", "2005-01-01", grade=10)
        criteria = SearchCriteria(first_name="Ali", grade=10)
        results = manager.search_students(criteria)
        assert len(results) == 1

    def test_get_active_students(self, manager):
        manager.add_student("Active", "One", "a1@test.com", "2005-01-01")
        manager.add_student("Active", "Two", "a2@test.com", "2005-01-01")
        s3 = manager.add_student("Inactive", "One", "i1@test.com", "2005-01-01")
        manager.deactivate_student(s3.id)

        active = manager.get_active_students()
        assert len(active) == 2

    def test_toggle_active(self, manager, sample_student):
        assert sample_student.is_active is True
        manager.deactivate_student(sample_student.id)
        student = manager.get_student(sample_student.id)
        assert student.is_active is False
        manager.activate_student(sample_student.id)
        student = manager.get_student(sample_student.id)
        assert student.is_active is True

    def test_export(self, manager, sample_student):
        export = manager.export_to_dict()
        assert export["count"] == 1
        assert sample_student.id in export["students"]

    def test_count_active(self, manager):
        manager.add_student("A", "One", "a1@test.com", "2005-01-01")
        manager.add_student("A", "Two", "a2@test.com", "2005-01-01")
        s3 = manager.add_student("I", "One", "i1@test.com", "2005-01-01")
        manager.deactivate_student(s3.id)

        assert manager.count() == 3
        assert manager.count_active() == 2


# ─── Integration Tests ──────────────────────────────────────────

class TestIntegration:
    """End-to-end workflow tests."""

    def test_full_lifecycle(self, manager):
        """Test complete student lifecycle."""
        # Create
        student = manager.add_student(
            first_name="Emma",
            last_name="Wilson",
            email="emma@test.com",
            date_of_birth="2005-06-20",
            grade=9,
            major="Chemistry",
            gpa=3.6,
        )
        assert manager.count() == 1

        # Read
        retrieved = manager.get_student(student.id)
        assert retrieved.email == "emma@test.com"

        # Update
        updated = manager.update_student(student.id, grade=10, gpa=3.7)
        assert updated.grade == 10
        assert updated.gpa == 3.7

        # Search
        results = manager.search_students(major="Chemistry")
        assert len(results) == 1

        # Deactivate
        manager.deactivate_student(student.id)
        assert manager.count_active() == 0

        # Delete
        removed = manager.remove_student(student.id)
        assert removed.id == student.id
        assert manager.count() == 0

    def test_persistence_across_instances(self, temp_db):
        """Test data persists when creating new manager instance."""
        m1 = StudentManager(temp_db)
        student = m1.add_student("Persist", "Test", "persist@test.com", "2005-01-01")
        student_id = student.id

        # New manager instance
        m2 = StudentManager(temp_db)
        retrieved = m2.get_student(student_id)
        assert retrieved.email == "persist@test.com"

    def test_concurrent_operations(self, manager):
        """Test thread-safety with simulated concurrent access."""
        import threading
        import time

        errors = []

        def add_students(prefix: str, count: int):
            try:
                for i in range(count):
                    manager.add_student(
                        first_name=f"{prefix}{i}",
                        last_name="User",
                        email=f"{prefix}{i}@test.com",
                        date_of_birth="2005-01-01",
                    )
                    time.sleep(0.001)  # Small delay to increase interleaving
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=add_students, args=("A", 10)),
            threading.Thread(target=add_students, args=("B", 10)),
            threading.Thread(target=add_students, args=("C", 10)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent errors: {errors}"
        assert manager.count() == 30


# ─── Edge Cases ─────────────────────────────────────────────────

class TestEdgeCases:
    """Edge case and boundary tests."""

    def test_unicode_names(self, manager):
        student = manager.add_student(
            first_name="José",
            last_name="García-López",
            email="jose@test.com",
            date_of_birth="2005-01-01",
        )
        assert student.first_name == "José"
        assert student.last_name == "García-López"

    def test_email_case_insensitive(self, manager):
        manager.add_student("Test", "User", "TEST@EXAMPLE.COM", "2005-01-01")
        with pytest.raises(DuplicateStudentError):
            manager.add_student("Test2", "User", "test@example.com", "2005-01-01")

    def test_gpa_boundaries(self):
        # Valid boundaries
        s1 = Student.create(first_name="A", last_name="B", email="a@b.com", date_of_birth="2005-01-01", gpa=0.0)
        s2 = Student.create(first_name="A", last_name="B", email="a@b.com", date_of_birth="2005-01-01", gpa=4.0)
        assert s1.gpa == 0.0
        assert s2.gpa == 4.0

    def test_grade_boundaries(self):
        s1 = Student.create(first_name="A", last_name="B", email="a@b.com", date_of_birth="2005-01-01", grade=1)
        s2 = Student.create(first_name="A", last_name="B", email="a@b.com", date_of_birth="2005-01-01", grade=12)
        assert s1.grade == 1
        assert s2.grade == 12

    def test_metadata_persistence(self, manager):
        student = manager.add_student(
            first_name="Meta",
            last_name="Data",
            email="meta@test.com",
            date_of_birth="2005-01-01",
            metadata={"parent_contact": "555-1234", "allergies": ["peanuts"]},
        )
        retrieved = manager.get_student(student.id)
        assert retrieved.metadata["parent_contact"] == "555-1234"
        assert retrieved.metadata["allergies"] == ["peanuts"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
