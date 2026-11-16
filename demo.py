#!/usr/bin/env python3
"""
Demo script showing Student Management System usage.

Run this to see the system in action without interactive CLI.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from student_management import (
    DuplicateStudentError,
    StudentManager,
    StudentNotFoundError,
    ValidationError,
)


def main() -> None:
    # Use a temporary file for demo
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        db_path = Path(tmp.name)

    try:
        print("=" * 60)
        print("Student Management System - Demo")
        print("=" * 60)

        # ─── Initialize ──────────────────────────────────────────
        manager = StudentManager(db_path)
        print(f"\n📁 Using database: {db_path}")

        # ─── Add Students ────────────────────────────────────────
        print("\n--- Adding Students ---")

        students_data = [
            {
                "first_name": "Alice",
                "last_name": "Johnson",
                "email": "alice.johnson@university.edu",
                "date_of_birth": "2005-03-15",
                "grade": 11,
                "major": "Computer Science",
                "gpa": 3.8,
            },
            {
                "first_name": "Bob",
                "last_name": "Smith",
                "email": "bob.smith@university.edu",
                "date_of_birth": "2004-07-22",
                "grade": 12,
                "major": "Mathematics",
                "gpa": 3.9,
            },
            {
                "first_name": "Carol",
                "last_name": "Williams",
                "email": "carol.williams@university.edu",
                "date_of_birth": "2006-01-10",
                "grade": 10,
                "major": "Physics",
                "gpa": 3.7,
            },
        ]

        created_students = []
        for data in students_data:
            student = manager.add_student(**data)
            created_students.append(student)
            print(f"  ✅ {student.full_name} (ID: {student.id[:8]}) - Grade {student.grade}, GPA: {student.gpa}")

        # ─── Demonstrate Error Handling ──────────────────────────
        print("\n--- Error Handling Demos ---")

        # Duplicate email
        try:
            manager.add_student(
                first_name="Alice",
                last_name="Duplicate",
                email="alice.johnson@university.edu",  # Same email!
                date_of_birth="2005-01-01",
            )
        except DuplicateStudentError as e:
            print(f"  ✅ Caught expected error: {e}")

        # Invalid GPA
        try:
            manager.add_student(
                first_name="Test",
                last_name="Student",
                email="test@test.com",
                date_of_birth="2005-01-01",
                gpa=5.0,  # Invalid!
            )
        except ValidationError as e:
            print(f"  ✅ Caught expected error: {e}")

        # Student not found
        try:
            manager.get_student("non-existent-id")
        except StudentNotFoundError as e:
            print(f"  ✅ Caught expected error: {e}")

        # ─── Search & Filter ─────────────────────────────────────
        print("\n--- Search Examples ---")

        # By name
        results = manager.search_students(first_name="Ali")
        print(f"  Search 'Ali': {len(results)} result(s) - {[s.full_name for s in results]}")

        # By grade
        results = manager.search_students(grade=11)
        print(f"  Grade 11: {len(results)} student(s) - {[s.full_name for s in results]}")

        # By GPA range
        results = manager.search_students(min_gpa=3.8)
        print(f"  GPA >= 3.8: {len(results)} student(s) - {[s.full_name for s in results]}")

        # Active only
        active = manager.get_active_students()
        print(f"  Active students: {len(active)}")

        # ─── Get & Update ────────────────────────────────────────
        print("\n--- Get & Update ---")

        alice = manager.get_student(created_students[0].id)
        print(f"  Before: {alice.full_name}, Major: {alice.major}, GPA: {alice.gpa}")

        updated = manager.update_student(
            alice.id,
            major="Computer Engineering",
            gpa=3.9,
        )
        print(f"  After:  {updated.full_name}, Major: {updated.major}, GPA: {updated.gpa}")

        # ─── Toggle Status ───────────────────────────────────────
        print("\n--- Toggle Status ---")
        bob = created_students[1]
        print(f"  Bob status before: {'Active' if bob.is_active else 'Inactive'}")
        manager.deactivate_student(bob.id)
        bob = manager.get_student(bob.id)
        print(f"  Bob status after:  {'Active' if bob.is_active else 'Inactive'}")

        # ─── Remove ──────────────────────────────────────────────
        print("\n--- Remove Student ---")
        carol = created_students[2]
        removed = manager.remove_student(carol.id)
        print(f"  Removed: {removed.full_name}")
        print(f"  Total students now: {manager.count()}")

        # ─── Export ──────────────────────────────────────────────
        print("\n--- Export Data ---")
        export = manager.export_to_dict()
        print(f"  Exported {export['count']} students")
        import json
        print(json.dumps(export, indent=2)[:500] + "...")

        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)

    finally:
        # Cleanup
        if db_path.exists():
            db_path.unlink()


if __name__ == "__main__":
    main()
