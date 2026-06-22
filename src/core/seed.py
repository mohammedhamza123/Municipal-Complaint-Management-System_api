"""
Database seeding script - Creates admin account with all permissions
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.core.database import SessionLocal, engine, Base
from src.core.security import get_password_hash
from src.users.model.user import User
from src.roles.model.role import Role, Permission, user_roles, role_permissions
from src.departments.model.department import Department
from src.problems.model.issue import Issue
from src.complaints.model.complaint import Complaint
from src.votes.model.vote import Vote
from src.assignments.model.assignment import Assignment
from src.notifications.model.notification import Notification


# All system permissions
ALL_PERMISSIONS = [
    # Users
    ("users:create", "users", "create", "Create users"),
    ("users:read", "users", "read", "View users"),
    ("users:update", "users", "update", "Update users"),
    ("users:delete", "users", "delete", "Delete users"),
    # Roles
    ("roles:create", "roles", "create", "Create roles"),
    ("roles:read", "roles", "read", "View roles"),
    ("roles:update", "roles", "update", "Update roles"),
    ("roles:delete", "roles", "delete", "Delete roles"),
    # Departments
    ("departments:create", "departments", "create", "Create departments"),
    ("departments:read", "departments", "read", "View departments"),
    ("departments:update", "departments", "update", "Update departments"),
    ("departments:delete", "departments", "delete", "Delete departments"),
    # Issues
    ("issues:create", "issues", "create", "Create issues"),
    ("issues:read", "issues", "read", "View issues"),
    ("issues:update", "issues", "update", "Update issues"),
    ("issues:delete", "issues", "delete", "Delete issues"),
    # Complaints
    ("complaints:create", "complaints", "create", "Create complaints"),
    ("complaints:read", "complaints", "read", "View complaints"),
    ("complaints:update", "complaints", "update", "Update complaints"),
    ("complaints:delete", "complaints", "delete", "Delete complaints"),
    # Assignments
    ("assignments:create", "assignments", "create", "Create assignments"),
    ("assignments:read", "assignments", "read", "View assignments"),
    ("assignments:update", "assignments", "update", "Update assignments"),
    ("assignments:delete", "assignments", "delete", "Delete assignments"),
    # Votes
    ("votes:create", "votes", "create", "Create votes"),
    ("votes:read", "votes", "read", "View votes"),
    ("votes:delete", "votes", "delete", "Delete votes"),
    # Notifications
    ("notifications:create", "notifications", "create", "Create notifications"),
    ("notifications:read", "notifications", "read", "View notifications"),
    ("notifications:update", "notifications", "update", "Update notifications"),
    ("notifications:delete", "notifications", "delete", "Delete notifications"),
]


def seed_database():
    """Seed database with admin account and all permissions"""

    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        # ─── 1. Create all permissions ───
        print("Creating permissions...")
        permission_objects = []

        for name, resource, action, description in ALL_PERMISSIONS:
            existing = db.query(Permission).filter(Permission.name == name).first()
            if existing:
                permission_objects.append(existing)
                print(f"  [EXISTS] {name}")
            else:
                perm = Permission(
                    name=name,
                    resource=resource,
                    action=action,
                    description=description
                )
                db.add(perm)
                db.flush()
                permission_objects.append(perm)
                print(f"  [CREATED] {name}")

        print(f"\n  Total permissions: {len(permission_objects)}")

        # ─── 2. Create admin role ───
        print("\nCreating admin role...")
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if not admin_role:
            admin_role = Role(
                name="admin",
                description="Administrator - Full access to all resources"
            )
            db.add(admin_role)
            db.flush()
            print("  [CREATED] admin role")
        else:
            print("  [EXISTS] admin role")

        # Assign all permissions to admin role
        admin_role.permissions = permission_objects
        print(f"  Assigned {len(permission_objects)} permissions to admin role")

        # ─── 3. Create common roles ───
        print("\nCreating common roles...")

        # Citizen role
        citizen_role = db.query(Role).filter(Role.name == "citizen").first()
        if not citizen_role:
            citizen_perms = [p for p in permission_objects if p.name in [
                "issues:create", "issues:read",
                "complaints:create", "complaints:read",
                "votes:create", "votes:read",
                "notifications:read", "notifications:update",
                "departments:read",
            ]]
            citizen_role = Role(
                name="citizen",
                description="Citizen - Can report issues, file complaints, and vote"
            )
            citizen_role.permissions = citizen_perms
            db.add(citizen_role)
            db.flush()
            print(f"  [CREATED] citizen role ({len(citizen_perms)} permissions)")
        else:
            print("  [EXISTS] citizen role")

        # Employee role
        employee_role = db.query(Role).filter(Role.name == "employee").first()
        if not employee_role:
            employee_perms = [p for p in permission_objects if p.name in [
                "issues:read", "issues:update",
                "complaints:read", "complaints:update",
                "assignments:read", "assignments:update",
                "notifications:read", "notifications:update",
                "departments:read", "users:read",
            ]]
            employee_role = Role(
                name="employee",
                description="Municipal Employee - Can handle assigned issues and complaints"
            )
            employee_role.permissions = employee_perms
            db.add(employee_role)
            db.flush()
            print(f"  [CREATED] employee role ({len(employee_perms)} permissions)")
        else:
            print("  [EXISTS] employee role")

        # Manager role
        manager_role = db.query(Role).filter(Role.name == "manager").first()
        manager_perms = [p for p in permission_objects if p.name in [
            "users:create", "users:read",
            "issues:read", "issues:update", "issues:delete",
            "complaints:read", "complaints:update", "complaints:delete",
            "assignments:create", "assignments:read", "assignments:update", "assignments:delete",
            "notifications:create", "notifications:read", "notifications:update",
            "departments:read",
        ]]
        if not manager_role:
            manager_role = Role(
                name="manager",
                description="Department Manager - Can manage issues, complaints, and assignments"
            )
            manager_role.permissions = manager_perms
            db.add(manager_role)
            db.flush()
            print(f"  [CREATED] manager role ({len(manager_perms)} permissions)")
        else:
            # Update existing manager role permissions
            manager_role.permissions = manager_perms
            db.flush()
            print(f"  [UPDATED] manager role ({len(manager_perms)} permissions)")

        # ─── 4. Create default departments ───
        print("\nCreating departments...")

        DEPARTMENTS = [
            ("الكهرباء", "قسم الكهرباء والإنارة العامة"),
            ("المياه والصرف الصحي", "قسم شبكات المياه والصرف الصحي"),
            ("الطرق والأرصفة", "قسم صيانة الطرق والأرصفة"),
            ("النظافة والبيئة", "قسم النظافة العامة وحماية البيئة"),
            ("الحدائق والمساحات الخضراء", "قسم الحدائق والتشجير"),
            ("البناء والتعمير", "قسم رخص البناء والتنظيم العمراني"),
            ("المرور والنقل", "قسم تنظيم المرور والنقل"),
            ("الصحة العامة", "قسم الرقابة الصحية والوقاية"),
            ("الخدمات الاجتماعية", "قسم الشؤون الاجتماعية والخدمات المجتمعية"),
            ("الشؤون الإدارية", "قسم الشؤون الإدارية والمالية"),
            ("تقنية المعلومات", "قسم تقنية المعلومات والتحول الرقمي"),
            ("أخرى", "شكاوى عامة لا تندرج تحت قسم محدد"),
        ]

        for dept_name, dept_desc in DEPARTMENTS:
            existing = db.query(Department).filter(Department.name == dept_name).first()
            if existing:
                print(f"  [EXISTS] {dept_name}")
            else:
                dept = Department(name=dept_name, description=dept_desc)
                db.add(dept)
                db.flush()
                print(f"  [CREATED] {dept_name}")

        print(f"\n  Total departments: {len(DEPARTMENTS)}")

        # ─── 5. Create admin user ───
        print("\nCreating admin user...")
        admin_user = db.query(User).filter(User.email == "admin@municipality.gov").first()
        if not admin_user:
            admin_user = User(
                email="admin@municipality.gov",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="System Administrator",
                is_active=True,
                is_superuser=True
            )
            db.add(admin_user)
            db.flush()
            print("  [CREATED] admin user")
        else:
            print("  [EXISTS] admin user")

        # Assign admin role
        if admin_role not in admin_user.roles:
            admin_user.roles.append(admin_role)
            print("  Assigned 'admin' role to admin user")

        # ─── 6. Create test users for each role ───
        print("\nCreating test users...")
        
        # Get first department for manager and employee
        first_dept = db.query(Department).first()
        
        # Citizen user
        citizen_user = db.query(User).filter(User.email == "citizen@test.com").first()
        if not citizen_user:
            citizen_user = User(
                email="citizen@test.com",
                username="citizen",
                hashed_password=get_password_hash("citizen123"),
                full_name="مواطن تجريبي",
                is_active=True,
                is_superuser=False
            )
            db.add(citizen_user)
            db.flush()
            print("  [CREATED] citizen user")
        else:
            print("  [EXISTS] citizen user")
        
        if citizen_role not in citizen_user.roles:
            citizen_user.roles.append(citizen_role)
            print("  Assigned 'citizen' role to citizen user")
        
        # Manager user (Department Head)
        manager_user = db.query(User).filter(User.email == "manager@test.com").first()
        if not manager_user:
            manager_user = User(
                email="manager@test.com",
                username="manager",
                hashed_password=get_password_hash("manager123"),
                full_name="رئيس قسم تجريبي",
                is_active=True,
                is_superuser=False,
                department_id=first_dept.id if first_dept else None
            )
            db.add(manager_user)
            db.flush()
            print("  [CREATED] manager user")
        else:
            print("  [EXISTS] manager user")
        
        if manager_role not in manager_user.roles:
            manager_user.roles.append(manager_role)
            print("  Assigned 'manager' role to manager user")
        
        # Assign manager as department head if department exists
        if first_dept and manager_user.department_id:
            first_dept.head_id = manager_user.id
            print(f"  Assigned manager as head of department: {first_dept.name}")
        
        # Employee user
        employee_user = db.query(User).filter(User.email == "employee@test.com").first()
        if not employee_user:
            employee_user = User(
                email="employee@test.com",
                username="employee",
                hashed_password=get_password_hash("employee123"),
                full_name="موظف تجريبي",
                is_active=True,
                is_superuser=False,
                department_id=first_dept.id if first_dept else None
            )
            db.add(employee_user)
            db.flush()
            print("  [CREATED] employee user")
        else:
            print("  [EXISTS] employee user")
        
        if employee_role not in employee_user.roles:
            employee_user.roles.append(employee_role)
            print("  Assigned 'employee' role to employee user")

        # ─── Commit ───
        db.commit()

        print("\n" + "=" * 50)
        print("  SEED COMPLETED SUCCESSFULLY!")
        print("=" * 50)
        print(f"\n  Test Accounts Created:")
        print(f"\n  1. Admin Account (أدمن رئيسي):")
        print(f"     Email:    admin@municipality.gov")
        print(f"     Username: admin")
        print(f"     Password: admin123")
        print(f"     Superuser: Yes")
        print(f"     Role: admin ({len(permission_objects)} permissions)")
        
        print(f"\n  2. Citizen Account (مواطن):")
        print(f"     Email:    citizen@test.com")
        print(f"     Username: citizen")
        print(f"     Password: citizen123")
        print(f"     Role: citizen")
        
        print(f"\n  3. Manager Account (رئيس قسم):")
        print(f"     Email:    manager@test.com")
        print(f"     Username: manager")
        print(f"     Password: manager123")
        print(f"     Department: {first_dept.name if first_dept else 'None'}")
        print(f"     Role: manager")
        if first_dept:
            print(f"     Status: Head of {first_dept.name}")
        
        print(f"\n  4. Employee Account (موظف):")
        print(f"     Email:    employee@test.com")
        print(f"     Username: employee")
        print(f"     Password: employee123")
        print(f"     Department: {first_dept.name if first_dept else 'None'}")
        print(f"     Role: employee")
        
        print(f"\n  Roles Created:")
        print(f"    - admin (full access)")
        print(f"    - citizen (report issues, file complaints, vote)")
        print(f"    - employee (handle assigned issues)")
        print(f"    - manager (manage issues, assignments)")
        print(f"\n  WARNING: Change all passwords in production!")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"\n  ERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()

