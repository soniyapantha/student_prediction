# auth.py
from functools import wraps
from flask import session, redirect, url_for, flash
import hashlib
import re

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(plain) == hashed

class Roles:
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

def login_required(f):
    """Decorator: User must be logged in"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first!", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Decorator: User must have one of the allowed roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                flash("Please login first!", "warning")
                return redirect(url_for("login"))
            
            if session.get("role") not in allowed_roles:
                flash("Access denied! You don't have permission for this page.", "danger")
                return redirect(url_for(f"dashboard_{session.get('role', 'student')}"))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get current logged-in user from database"""
    from database import SessionLocal
    from models import User
    
    if "user_id" not in session:
        return None
    db = SessionLocal()
    user = db.query(User).filter(User.id == session["user_id"]).first()
    db.close()
    return user

def create_default_users():
    """Create default Admin, Teacher, and demo Student accounts"""
    from database import SessionLocal
    from models import User, Student
    
    db = SessionLocal()
    
    # Check if any users exist
    if db.query(User).count() > 0:
        db.close()
        return
    
    print("\n[SETUP] Creating default user accounts...")
    
    # First, create a demo student record
    demo_student = Student(
        roll_number="DEMO001",
        name="Demo Student",
        attendance=85.0,
        math_marks=75.0,
        science_marks=80.0,
        english_marks=78.0,
        hours_studied=5.0,
        assignments=85.0,
        prev_gpa=3.2,
        prediction_rf=78.5,
        prediction_gb=79.0,
        prediction_svm=77.5,
        best_model="Random Forest"
    )
    db.add(demo_student)
    db.commit()
    db.refresh(demo_student)  # This gets the auto-generated ID
    
    # Create admin user (no student_id)
    admin = User(
        username="admin",
        email="admin@college.edu",
        password_hash=hash_password("admin123"),
        role=Roles.ADMIN,
        full_name="System Administrator",
        is_active=True,
        student_id=None
    )
    db.add(admin)
    
    # Create teacher user (no student_id)
    teacher = User(
        username="teacher",
        email="teacher@college.edu",
        password_hash=hash_password("teacher123"),
        role=Roles.TEACHER,
        full_name="Professor Smith",
        is_active=True,
        student_id=None
    )
    db.add(teacher)
    
    # Create student user with the demo_student.id
    student_user = User(
        username="student",
        email="student@college.edu",
        password_hash=hash_password("student123"),
        role=Roles.STUDENT,
        full_name="Demo Student",
        is_active=True,
        student_id=demo_student.id
    )
    db.add(student_user)
    
    db.commit()
    db.close()
    
    print("  ✓ Admin: admin / admin123")
    print("  ✓ Teacher: teacher / teacher123")
    print(f"  ✓ Student: student / student123 (linked to student ID: {demo_student.id})")