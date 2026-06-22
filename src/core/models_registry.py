"""
Models Registry - Import all models here to ensure SQLAlchemy
resolves all relationships correctly before any queries.
"""
# Import all models so SQLAlchemy registers them
from src.users.model.user import User  # noqa: F401
from src.roles.model.role import Role, Permission  # noqa: F401
from src.departments.model.department import Department  # noqa: F401
from src.complaints.model.complaint import Complaint  # noqa: F401
from src.problems.model.issue import Issue  # noqa: F401
from src.problems.model.issue_report import IssueReport  # noqa: F401
from src.votes.model.vote import Vote  # noqa: F401
from src.assignments.model.assignment import Assignment  # noqa: F401
from src.notifications.model.notification import Notification  # noqa: F401
