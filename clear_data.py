"""
سكريبت لمسح الشكاوى والمشكلات من قاعدة البيانات
Script to clear complaints and issues from database
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from src.core.database import SessionLocal
from src.complaints.model.complaint import Complaint
from src.problems.model.issue import Issue
from src.votes.model.vote import Vote
from src.assignments.model.assignment import Assignment
from src.problems.model.issue_report import IssueReport

def clear_data():
    """مسح جميع الشكاوى والمشكلات والبيانات المرتبطة"""
    db = SessionLocal()
    try:
        print("جاري مسح البيانات...")
        
        # مسح البيانات المرتبطة أولاً
        print("  - مسح التقارير (Issue Reports)...")
        db.query(IssueReport).delete()
        
        print("  - مسح التصويتات (Votes)...")
        db.query(Vote).delete()
        
        print("  - مسح المهام (Assignments)...")
        db.query(Assignment).delete()
        
        # مسح الشكاوى
        print("  - مسح الشكاوى (Complaints)...")
        complaints_count = db.query(Complaint).count()
        db.query(Complaint).delete()
        print(f"    تم مسح {complaints_count} شكوى")
        
        # مسح المشكلات
        print("  - مسح المشكلات (Issues)...")
        issues_count = db.query(Issue).count()
        db.query(Issue).delete()
        print(f"    تم مسح {issues_count} مشكلة")
        
        # حفظ التغييرات
        db.commit()
        print("\n✅ تم مسح جميع البيانات بنجاح!")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ خطأ في مسح البيانات: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    import io
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    
    # Check if --yes flag is provided
    if '--yes' in sys.argv:
        clear_data()
    else:
        print("=" * 60)
        print("WARNING: This will delete ALL complaints and issues!")
        print("=" * 60)
        print("\nTo proceed, run:")
        print("  python clear_data.py --yes")
        print("\nOr modify the script to remove the confirmation check.")

