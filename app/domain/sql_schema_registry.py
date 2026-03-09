import re
# ============================================================
# USER MANAGEMENT
# ============================================================

USER_SCHEMA = """
TABLE: users

Columns:
- id (PRIMARY KEY)
- email (unique)
- first_name
- last_name
- password_hash
- role (admin | manager | employee | freelancer)
- created_at
- updated_at
"""

# ============================================================
# PROJECT MANAGEMENT
# ============================================================

PROJECT_SCHEMA = """
TABLE: projects

Columns:
- id (PRIMARY KEY)
- name
- description
- owner_id (FOREIGN KEY → users.id)
- start_date
- end_date
- status (not_started | in_progress | completed | archived)
- created_at
- updated_at
"""

# ============================================================
# TASK MANAGEMENT
# ============================================================

TASK_SCHEMA = """
TABLE: tasks

Columns:
- id (PRIMARY KEY)
- project_id (FOREIGN KEY → projects.id)
- title
- description
- assigned_to (FOREIGN KEY → users.id)
- status (backlog | to_do | in_progress | completed | blocked)
- priority (low | medium | high | critical)
- due_date
- start_date
- created_at
- updated_at
"""

# ============================================================
# TASK COMMENTS
# ============================================================

TASK_COMMENT_SCHEMA = """
TABLE: task_comments

Columns:
- id (PRIMARY KEY)
- task_id (FOREIGN KEY → tasks.id)
- user_id (FOREIGN KEY → users.id)
- comment
- created_at
- updated_at
"""

# ============================================================
# FILE SHARING & DOCUMENTS
# ============================================================

FILE_SHARING_SCHEMA = """
TABLE: file_sharing

Columns:
- id (PRIMARY KEY)
- task_id (FOREIGN KEY → tasks.id)
- file_name
- file_path
- uploaded_by (FOREIGN KEY → users.id)
- uploaded_at
- file_type
- size_in_bytes
"""

# ============================================================
# NOTIFICATIONS & ALERTS
# ============================================================

NOTIFICATION_SCHEMA = """
TABLE: notifications

Columns:
- id (PRIMARY KEY)
- user_id (FOREIGN KEY → users.id)
- notification_type (task_due_soon | task_overdue | new_task_assigned)
- message
- created_at
- read_at
"""

# ============================================================
# FINAL REGISTRY
# ============================================================

TASKFLOW_SCHEMA_REGISTRY = {
    "users": USER_SCHEMA,
    "projects": PROJECT_SCHEMA,
    "tasks": TASK_SCHEMA,
    "task_comments": TASK_COMMENT_SCHEMA,
    "file_sharing": FILE_SHARING_SCHEMA,
    "notifications": NOTIFICATION_SCHEMA,
}


def get_schemas(schema_keys: list[str]) -> str:
    """
    Returns merged SQL schema slices for multiple domains.
    Order is preserved.
    """

    if not schema_keys:
        raise ValueError("No schema keys provided")

    schemas = []

    for key in schema_keys:
        try:
            schemas.append(TASKFLOW_SCHEMA_REGISTRY[key])
        except KeyError:
            raise ValueError(f"Unsupported schema: {key}")

    return "\n\n".join(schemas)


_TABLE_PATTERN = re.compile(r"TABLE:\s+([a-zA-Z0-9_\.]+)")


def extract_allowed_tables(schema_text: str) -> set[str]:
    """
    Extract table names from schema slice.
    """
    return set(_TABLE_PATTERN.findall(schema_text))