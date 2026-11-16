# Student Management System

A clean, object-oriented Python Student Management System with JSON persistence, comprehensive error handling, and both programmatic and CLI interfaces.

## Features

- **Full CRUD Operations** — Add, remove, search, update students
- **JSON Persistence** — Atomic file writes, thread-safe, human-readable
- **Rich Data Model** — Name, email, DOB, grade, major, GPA, status, metadata
- **Validation** — Type-safe dataclass with comprehensive field validation
- **Error Handling** — Custom exception hierarchy for precise error catching
- **Search & Filter** — Flexible criteria-based search (name, grade, GPA range, etc.)
- **CLI Interface** — Interactive menu + command-line arguments
- **Tested** — 40+ unit/integration tests with pytest

## Installation

```bash
# From source
pip install -e .

# Or install with dev dependencies
pip install -e .[dev]
```

## Quick Start

```python
from student_management import StudentManager

# Initialize (creates students.json automatically)
manager = StudentManager("students.json")

# Add a student
student = manager.add_student(
    first_name="Alice",
    last_name="Johnson",
    email="alice@university.edu",
    date_of_birth="2005-03-15",
    grade=11,
    major="Computer Science",
    gpa=3.8,
)

# Search students
results = manager.search_students(grade=11, min_gpa=3.5)

# Update
manager.update_student(student.id, gpa=3.9, major="Computer Engineering")

# Get active students
active = manager.get_active_students()

# Remove
manager.remove_student(student.id)
```

## CLI Usage

```bash
# Interactive mode
student-mgmt interactive

# Command-line operations
student-mgmt add "John" "Doe" "john@example.com" "2005-05-15" --grade 10 --gpa 3.5
student-mgmt list --active
student-mgmt search --grade 10 --min-gpa 3.0
student-mgmt get <student-id>
student-mgmt update <student-id> --gpa 3.8 --major "Physics"
student-mgmt remove <student-id>
student-mgmt stats
student-mgmt export
```

## Architecture

```
student_management/
├── __init__.py          # Package exports
├── student.py           # Student dataclass + validation
├── storage.py           # JSONStorage (persistence layer)
├── manager.py           # StudentManager (business logic)
├── exceptions.py        # Custom exception hierarchy
├── cli.py               # Command-line interface
├── demo.py              # Usage demonstration
└── test_student_mgmt.py # Unit & integration tests
```

### Component Responsibilities

| Module | Purpose |
|--------|---------|
| `Student` | Immutable data model with validation (dataclass) |
| `StudentManager` | Business logic: CRUD, search, validation orchestration |
| `JSONStorage` | File I/O: atomic writes, thread-safe, serialization |
| `exceptions` | Typed errors: `StudentNotFoundError`, `DuplicateStudentError`, etc. |

## Data Model

```python
Student(
    id: str                    # UUID4 (auto-generated)
    first_name: str            # 1-50 chars, letters only
    last_name: str             # 1-50 chars, letters only
    email: str                 # Valid email, unique
    date_of_birth: str         # ISO format YYYY-MM-DD
    enrollment_date: str       # ISO format (default: today)
    grade: int | None          # 1-12
    major: str | None          # Max 100 chars
    gpa: float | None          # 0.0-4.0
    is_active: bool            # Default: True
    metadata: dict             # Extensible additional fields
)
```

## Exception Hierarchy

```
StudentManagementError (base)
├── StudentNotFoundError      # ID not found
├── DuplicateStudentError     # Email/ID conflict
├── ValidationError           # Field validation failed
└── StorageError              # File I/O failure
```

## Running Tests

```bash
# Install dev dependencies
pip install -e .[dev]

# Run all tests
pytest

# With coverage
pytest --cov=student_management

# Specific test class
pytest test_student_mgmt.py::TestStudentManager -v
```

## Example Output

```
$ student-mgmt interactive

╔══════════════════════════════════════════════════════════╗
║        Student Management System - Interactive Mode       ║
╚══════════════════════════════════════════════════════════╝

┌────────────────────────────────────────────────────────────┐
│ 1. Add Student          │ 2. List All Students            │
│ 3. Search Students      │ 4. Get Student by ID            │
│ 5. Update Student       │ 6. Remove Student               │
│ 7. Toggle Active Status │ 8. Show Statistics              │
│ 9. Export Data          │ q. Quit                         │
└────────────────────────────────────────────────────────────┘

Enter choice (1-9, q to quit): 1

--- Add New Student ---
First name: Alice
Last name: Johnson
Email: alice@university.edu
Date of birth (YYYY-MM-DD): 2005-03-15
Grade (1-12, Enter to skip): 11
Major (Enter to skip): Computer Science
GPA (0.0-4.0, Enter to skip): 3.8
Enrollment date (YYYY-MM-DD, Enter for today): 

✅ Student added: Alice Johnson (a1b2c3d4)
   ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
```
