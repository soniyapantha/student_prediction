# fix_database.py
from database import SessionLocal
from models import User, Student

def fix_database():
    """Fix database issues with duplicate student_id constraints"""
    db = SessionLocal()
    
    print("\n" + "=" * 60)
    print("Fixing Database Issues")
    print("=" * 60)
    
    # Check for duplicate student_id in users
    users_with_student_id = db.query(User).filter(User.student_id.isnot(None)).all()
    
    print(f"\nFound {len(users_with_student_id)} users with student_id:")
    for user in users_with_student_id:
        print(f"  - ID: {user.id}, Username: {user.username}, Student ID: {user.student_id}")
    
    # Check if demo student exists
    demo_student = db.query(Student).filter(Student.roll_number == "DEMO001").first()
    
    if not demo_student:
        print("\nCreating demo student record...")
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
        db.refresh(demo_student)
        print(f"  ✓ Created demo student with ID: {demo_student.id}")
    
    # Fix the default student user
    default_student = db.query(User).filter(User.username == "student").first()
    if default_student:
        print(f"\nFixing default student user...")
        default_student.student_id = demo_student.id
        db.commit()
        print(f"  ✓ Updated student user to link with student ID: {demo_student.id}")
    
    # Check for any users with student_id that doesn't exist
    print("\nChecking for orphaned student_id links...")
    for user in users_with_student_id:
        if user.student_id:
            student_exists = db.query(Student).filter(Student.id == user.student_id).first()
            if not student_exists:
                print(f"  ⚠️ User {user.username} has student_id {user.student_id} but student doesn't exist")
                user.student_id = None
                db.commit()
                print(f"  ✓ Removed orphaned link from {user.username}")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("Database fix completed!")
    print("=" * 60)
    print("\nYou can now restart your application:")
    print("  python app.py")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    fix_database()