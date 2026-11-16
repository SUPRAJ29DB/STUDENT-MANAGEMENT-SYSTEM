"""
Command-line interface for Student Management System.

Demonstrates all features with interactive menu and command-line arguments.
"""
from __future__ import annotations

import argparse
import sys
from typing import Any, NoReturn

from .exceptions import (
    StudentManagementError,
)
from .manager import SearchCriteria, StudentManager
from .student import Student


class CLI:
    """Interactive and argument-driven CLI."""

    def __init__(self, manager: StudentManager):
        self.manager = manager

    # ─── Interactive Mode ────────────────────────────────────────

    def run_interactive(self) -> NoReturn:
        """Run interactive menu loop."""
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║        Student Management System - Interactive Mode       ║")
        print("╚══════════════════════════════════════════════════════════╝")

        while True:
            self._print_menu()
            choice = input("\nEnter choice (1-9, q to quit): ").strip().lower()

            if choice in ("q", "quit", "exit"):
                print("Goodbye!")
                sys.exit(0)

            try:
                self._handle_choice(choice)
            except StudentManagementError as e:
                print(f"\n❌ Error: {e}")
            except KeyboardInterrupt:
                print("\n\nCancelled.")
            except EOFError:
                print("\nGoodbye!")
                sys.exit(0)

    def _print_menu(self) -> None:
        print("\n┌────────────────────────────────────────────────────────────┐")
        print("│ 1. Add Student          │ 2. List All Students            │")
        print("│ 3. Search Students      │ 4. Get Student by ID            │")
        print("│ 5. Update Student       │ 6. Remove Student               │")
        print("│ 7. Toggle Active Status │ 8. Show Statistics              │")
        print("│ 9. Export Data          │ q. Quit                         │")
        print("└────────────────────────────────────────────────────────────┘")

    def _handle_choice(self, choice: str) -> None:
        handlers = {
            "1": self._add_student,
            "2": self._list_students,
            "3": self._search_students,
            "4": self._get_student,
            "5": self._update_student,
            "6": self._remove_student,
            "7": self._toggle_active,
            "8": self._show_stats,
            "9": self._export_data,
        }
        handler = handlers.get(choice)
        if handler:
            handler()
        else:
            print("Invalid choice. Please enter 1-9 or q.")

    def _add_student(self) -> None:
        print("\n--- Add New Student ---")
        first_name = self._prompt_required("First name: ")
        last_name = self._prompt_required("Last name: ")
        email = self._prompt_required("Email: ")
        dob = self._prompt_required("Date of birth (YYYY-MM-DD): ")

        grade = self._prompt_optional("Grade (1-12, Enter to skip): ", int)
        major = self._prompt_optional("Major (Enter to skip): ")
        gpa = self._prompt_optional("GPA (0.0-4.0, Enter to skip): ", float)
        enrollment = self._prompt_optional("Enrollment date (YYYY-MM-DD, Enter for today): ")

        student = self.manager.add_student(
            first_name=first_name,
            last_name=last_name,
            email=email,
            date_of_birth=dob,
            grade=grade,
            major=major or None,
            gpa=gpa,
            enrollment_date=enrollment or None,
        )
        print(f"\n✅ Student added: {student}")
        print(f"   ID: {student.id}")

    def _list_students(self) -> None:
        students = self.manager.get_all_students()
        if not students:
            print("\nNo students found.")
            return

        print(f"\n--- All Students ({len(students)}) ---")
        for i, s in enumerate(students, 1):
            status = "🟢" if s.is_active else "🔴"
            grade = f" Grade {s.grade}" if s.grade else ""
            gpa = f" GPA: {s.gpa}" if s.gpa is not None else ""
            print(f"  {i:3}. {status} {s.full_name} ({s.id[:8]}){grade}{gpa} - {s.email}")

    def _search_students(self) -> None:
        print("\n--- Search Students (leave blank to skip) ---")
        first = input("First name contains: ").strip() or None
        last = input("Last name contains: ").strip() or None
        email = input("Exact email: ").strip() or None
        grade = self._prompt_optional("Grade: ", int)
        major = input("Major contains: ").strip() or None
        active = input("Active only? (y/n/Enter for all): ").strip().lower()
        is_active = None if active not in ("y", "n") else active == "y"

        criteria = SearchCriteria(
            first_name=first,
            last_name=last,
            email=email,
            grade=grade,
            major=major,
            is_active=is_active,
        )

        results = self.manager.search_students(criteria)
        print(f"\nFound {len(results)} student(s):")
        for i, s in enumerate(results, 1):
            print(f"  {i}. {s.full_name} ({s.id[:8]}) - {s.email} - {'Active' if s.is_active else 'Inactive'}")

    def _get_student(self) -> None:
        student_id = self._prompt_required("Student ID: ")
        student = self.manager.get_student(student_id)
        self._print_student_detail(student)

    def _update_student(self) -> None:
        student_id = self._prompt_required("Student ID: ")
        student = self.manager.get_student(student_id)
        print(f"\nCurrent: {student.full_name} - {student.email}")
        print("Leave blank to keep current value.\n")

        updates = {}
        first = input(f"First name [{student.first_name}]: ").strip()
        if first:
            updates["first_name"] = first

        last = input(f"Last name [{student.last_name}]: ").strip()
        if last:
            updates["last_name"] = last

        email = input(f"Email [{student.email}]: ").strip()
        if email:
            updates["email"] = email

        grade = self._prompt_optional(f"Grade [{student.grade or 'none'}]: ", int)
        if grade is not None:
            updates["grade"] = grade

        major = input(f"Major [{student.major or 'none'}]: ").strip()
        if major:
            updates["major"] = major

        gpa = self._prompt_optional(f"GPA [{student.gpa or 'none'}]: ", float)
        if gpa is not None:
            updates["gpa"] = gpa

        if not updates:
            print("No changes made.")
            return

        updated = self.manager.update_student(student_id, **updates)
        print(f"\n✅ Updated: {updated.full_name} - {updated.email}")

    def _remove_student(self) -> None:
        student_id = self._prompt_required("Student ID: ")
        student = self.manager.get_student(student_id)
        confirm = input(f"Delete {student.full_name}? (y/N): ").strip().lower()
        if confirm == "y":
            removed = self.manager.remove_student(student_id)
            print(f"✅ Removed: {removed.full_name}")
        else:
            print("Cancelled.")

    def _toggle_active(self) -> None:
        student_id = self._prompt_required("Student ID: ")
        student = self.manager.get_student(student_id)
        if student.is_active:
            updated = self.manager.deactivate_student(student_id)
            print(f"✅ Deactivated: {updated.full_name}")
        else:
            updated = self.manager.activate_student(student_id)
            print(f"✅ Activated: {updated.full_name}")

    def _show_stats(self) -> None:
        total = self.manager.count()
        active = self.manager.count_active()
        students = self.manager.get_all_students()

        print("\n--- Statistics ---")
        print(f"  Total students:  {total}")
        print(f"  Active:          {active}")
        print(f"  Inactive:        {total - active}")

        if students:
            grades = [s.grade for s in students if s.grade]
            gpas = [s.gpa for s in students if s.gpa is not None]
            if grades:
                print(f"  Grade range:     {min(grades)}-{max(grades)}")
            if gpas:
                print(f"  GPA range:       {min(gpas):.2f}-{max(gpas):.2f}")
                print(f"  Average GPA:     {sum(gpas)/len(gpas):.2f}")

    def _export_data(self) -> None:
        data = self.manager.export_to_dict()
        print("\n--- Export Data (JSON) ---")
        import json
        print(json.dumps(data, indent=2))

    # ─── Helpers ─────────────────────────────────────────────────

    def _prompt_required(self, prompt: str) -> str:
        while True:
            value = input(prompt).strip()
            if value:
                return value
            print("This field is required.")

    def _prompt_optional(self, prompt: str, type_func: type = str) -> Any:
        value = input(prompt).strip()
        if not value:
            return None
        try:
            return type_func(value)
        except ValueError:
            print(f"Invalid {type_func.__name__}, skipping.")
            return None

    def _print_student_detail(self, student: Student) -> None:
        print(f"\n{'─'*50}")
        print(f"  ID:              {student.id}")
        print(f"  Name:            {student.full_name}")
        print(f"  Email:           {student.email}")
        print(f"  Date of Birth:   {student.date_of_birth} (Age: {student.age})")
        print(f"  Enrollment:      {student.enrollment_date}")
        print(f"  Grade:           {student.grade or 'N/A'}")
        print(f"  Major:           {student.major or 'N/A'}")
        print(f"  GPA:             {student.gpa if student.gpa is not None else 'N/A'}")
        print(f"  Status:          {'Active' if student.is_active else 'Inactive'}")
        if student.metadata:
            print(f"  Metadata:        {student.metadata}")
        print(f"{'─'*50}")


# ─── Argument Parser Mode ────────────────────────────────────────

def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="student-mgmt",
        description="Student Management System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  student-mgmt add "John" "Doe" "john@example.com" "2005-03-15" --grade 10 --gpa 3.5
  student-mgmt list --active
  student-mgmt search --first-name "John" --grade 10
  student-mgmt get <student-id>
  student-mgmt update <student-id> --email "new@example.com"
  student-mgmt remove <student-id>
  student-mgmt stats
        """
    )
    parser.add_argument(
        "--storage", "-s",
        default="students.json",
        help="Path to JSON storage file (default: students.json)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Add
    add_parser = subparsers.add_parser("add", help="Add a new student")
    add_parser.add_argument("first_name", help="First name")
    add_parser.add_argument("last_name", help="Last name")
    add_parser.add_argument("email", help="Email address")
    add_parser.add_argument("date_of_birth", help="Date of birth (YYYY-MM-DD)")
    add_parser.add_argument("--grade", type=int, choices=range(1, 13), help="Grade 1-12")
    add_parser.add_argument("--major", help="Major/field of study")
    add_parser.add_argument("--gpa", type=float, help="GPA 0.0-4.0")
    add_parser.add_argument("--enrollment", help="Enrollment date (YYYY-MM-DD)")
    add_parser.add_argument("--inactive", action="store_true", help="Mark as inactive")

    # List
    list_parser = subparsers.add_parser("list", help="List students")
    list_parser.add_argument("--active", action="store_true", help="Only active students")
    list_parser.add_argument("--inactive", action="store_true", help="Only inactive students")

    # Search
    search_parser = subparsers.add_parser("search", help="Search students")
    search_parser.add_argument("--first-name", help="First name contains")
    search_parser.add_argument("--last-name", help="Last name contains")
    search_parser.add_argument("--email", help="Exact email")
    search_parser.add_argument("--grade", type=int, help="Exact grade")
    search_parser.add_argument("--major", help="Major contains")
    search_parser.add_argument("--active", action="store_true", help="Only active")
    search_parser.add_argument("--inactive", action="store_true", help="Only inactive")
    search_parser.add_argument("--min-gpa", type=float, help="Minimum GPA")
    search_parser.add_argument("--max-gpa", type=float, help="Maximum GPA")

    # Get
    get_parser = subparsers.add_parser("get", help="Get student by ID")
    get_parser.add_argument("student_id", help="Student UUID")

    # Update
    update_parser = subparsers.add_parser("update", help="Update student")
    update_parser.add_argument("student_id", help="Student UUID")
    update_parser.add_argument("--first-name", help="New first name")
    update_parser.add_argument("--last-name", help="New last name")
    update_parser.add_argument("--email", help="New email")
    update_parser.add_argument("--grade", type=int, choices=range(1, 13), help="New grade")
    update_parser.add_argument("--major", help="New major")
    update_parser.add_argument("--gpa", type=float, help="New GPA")
    update_parser.add_argument("--activate", action="store_true", help="Set active")
    update_parser.add_argument("--deactivate", action="store_true", help="Set inactive")

    # Remove
    remove_parser = subparsers.add_parser("remove", help="Remove student")
    remove_parser.add_argument("student_id", help="Student UUID")
    remove_parser.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    # Stats
    subparsers.add_parser("stats", help="Show statistics")

    # Export
    subparsers.add_parser("export", help="Export all data as JSON")

    # Interactive
    subparsers.add_parser("interactive", help="Run interactive mode")

    return parser


def run_cli(args: argparse.Namespace) -> int:
    """Execute CLI command from parsed arguments."""
    manager = StudentManager(args.storage)
    cli = CLI(manager)

    try:
        if args.command == "interactive" or args.command is None:
            cli.run_interactive()
        elif args.command == "add":
            student = manager.add_student(
                first_name=args.first_name,
                last_name=args.last_name,
                email=args.email,
                date_of_birth=args.date_of_birth,
                grade=args.grade,
                major=args.major,
                gpa=args.gpa,
                enrollment_date=args.enrollment,
                is_active=not args.inactive,
            )
            print(f"✅ Added: {student.full_name} ({student.id})")
        elif args.command == "list":
            students = manager.get_active_students() if args.active else (
                [s for s in manager.get_all_students() if not s.is_active] if args.inactive else
                manager.get_all_students()
            )
            for s in students:
                status = "🟢" if s.is_active else "🔴"
                print(f"{status} {s.full_name} ({s.id[:8]}) - {s.email}")
        elif args.command == "search":
            criteria = SearchCriteria(
                first_name=args.first_name,
                last_name=args.last_name,
                email=args.email,
                grade=args.grade,
                major=args.major,
                is_active=True if args.active else (False if args.inactive else None),
                min_gpa=args.min_gpa,
                max_gpa=args.max_gpa,
            )
            results = manager.search_students(criteria)
            for s in results:
                print(f"{s.full_name} ({s.id[:8]}) - {s.email}")
        elif args.command == "get":
            student = manager.get_student(args.student_id)
            cli._print_student_detail(student)
        elif args.command == "update":
            updates = {}
            if args.first_name:
                updates["first_name"] = args.first_name
            if args.last_name:
                updates["last_name"] = args.last_name
            if args.email:
                updates["email"] = args.email
            if args.grade:
                updates["grade"] = args.grade
            if args.major:
                updates["major"] = args.major
            if args.gpa is not None:
                updates["gpa"] = args.gpa
            if args.activate:
                updates["is_active"] = True
            if args.deactivate:
                updates["is_active"] = False

            if not updates:
                print("No updates specified.")
                return 1

            student = manager.update_student(args.student_id, **updates)
            print(f"✅ Updated: {student.full_name} ({student.id})")
        elif args.command == "remove":
            if not args.force:
                student = manager.get_student(args.student_id)
                confirm = input(f"Delete {student.full_name}? (y/N): ").strip().lower()
                if confirm != "y":
                    print("Cancelled.")
                    return 0
            removed = manager.remove_student(args.student_id)
            print(f"✅ Removed: {removed.full_name}")
        elif args.command == "stats":
            cli._show_stats()
        elif args.command == "export":
            import json
            print(json.dumps(manager.export_to_dict(), indent=2))
        return 0
    except StudentManagementError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130


def main() -> NoReturn:
    """Entry point for console script."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = create_parser()
    args = parser.parse_args()
    sys.exit(run_cli(args))


if __name__ == "__main__":
    main()
