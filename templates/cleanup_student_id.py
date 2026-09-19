# cleanup_student_id.py
from database import SessionLocal
from models import User

db = SessionLocal()

# Find and fix the demo student with student_id=1
demo_user = db.query(User).filter(User.username == "student").first()
if demo_user:
    print(f"Found demo user: {demo_user.full_name} (ID: {demo_user.id}, student_id: {demo_user.student_id})")
    # Remove the student_id from demo user since it's conflicting
    demo_user.student_id = None
    db.commit()
    print("✅ Removed student_id from demo user account")
else:
    print("Demo user not found")

# Also check for any other users with student_id=1
conflicting_users = db.query(User).filter(User.student_id == 1).all()
for user in conflicting_users:
    print(f"Found conflicting user: {user.full_name} (student_id: {user.student_id})")
    user.student_id = None
    db.commit()
    print(f"✅ Fixed user: {user.full_name}")

db.close()
print("\n✅ Cleanup complete! You can now add new students.")