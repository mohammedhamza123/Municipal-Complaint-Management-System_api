"""
Clear operational database data while keeping users (and their roles/permissions).
Optionally clears uploaded files in uploads/.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.database import SessionLocal, engine, Base
import src.core.models_registry  # noqa: F401
from src.users.model.user import User
from src.departments.model.department import Department
from src.notifications.model.notification import Notification
from src.assignments.model.assignment import Assignment
from src.votes.model.vote import Vote
from src.problems.model.issue_report import IssueReport
from src.complaints.model.complaint import Complaint
from src.problems.model.issue import Issue

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
UPLOAD_SUBDIRS = ("complaints", "issues_resolved", "profiles")


def clear_upload_files() -> dict[str, int]:
    """Delete uploaded files; keep folder structure and .gitkeep."""
    deleted: dict[str, int] = {}

    for subdir in UPLOAD_SUBDIRS:
        target_dir = os.path.join(UPLOAD_DIR, subdir)
        os.makedirs(target_dir, exist_ok=True)

        count = 0
        for name in os.listdir(target_dir):
            path = os.path.join(target_dir, name)
            if os.path.isfile(path):
                os.remove(path)
                count += 1

        deleted[subdir] = count

    return deleted


def clear_operational_data(clear_uploads: bool = True) -> None:
    """Delete all data except users, roles, permissions, and role assignments."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        print("Clearing operational data (keeping users)...")

        user_updates = {User.department_id: None}
        if clear_uploads:
            user_updates[User.profile_image] = None

        db.query(User).update(user_updates, synchronize_session=False)
        db.query(Department).update({Department.head_id: None}, synchronize_session=False)
        db.flush()

        deleted = {
            "notifications": db.query(Notification).delete(synchronize_session=False),
            "assignments": db.query(Assignment).delete(synchronize_session=False),
            "votes": db.query(Vote).delete(synchronize_session=False),
            "issue_reports": db.query(IssueReport).delete(synchronize_session=False),
            "complaints": db.query(Complaint).delete(synchronize_session=False),
            "issues": db.query(Issue).delete(synchronize_session=False),
            "departments": db.query(Department).delete(synchronize_session=False),
        }

        db.commit()

        users_count = db.query(User).count()

        print("\nDeleted records:")
        for table, count in deleted.items():
            print(f"  - {table}: {count}")

        print(f"\nKept users: {users_count}")

        if clear_uploads:
            upload_deleted = clear_upload_files()
            print("\nDeleted upload files:")
            for folder, count in upload_deleted.items():
                print(f"  - uploads/{folder}: {count}")

        print("\nData cleared successfully.")

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clear_operational_data()
