# setup_classes.py
from database import SessionLocal, init_db
from models import Class, Section, User
from auth import hash_password, Roles

def setup_initial_data():
    print("Setting up initial data...")
    
    # Initialize database tables
    init_db()
    
    db = SessionLocal()
    
    try:
        # Create Classes
        classes = [
            Class(name="BCA 8th Semester", code="BCA801", description="Bachelor of Computer Applications - Final Year"),
            Class(name="BCA 7th Semester", code="BCA701", description="Bachelor of Computer Applications - 7th Sem"),
            Class(name="BSC CS 8th Semester", code="BSC801", description="BSc Computer Science - Final Year"),
            Class(name="MBA 4th Semester", code="MBA401", description="Master of Business Administration"),
        ]
        
        print("\n📚 Creating Classes...")
        for cls in classes:
            existing = db.query(Class).filter(Class.code == cls.code).first()
            if not existing:
                db.add(cls)
                print(f"  ✓ Added class: {cls.name} ({cls.code})")
            else:
                print(f"  - Class already exists: {cls.name}")
        
        db.commit()
        
        # Create Sections for each class
        print("\n📁 Creating Sections...")
        for cls in db.query(Class).all():
            for section_name in ['A', 'B', 'C']:
                existing = db.query(Section).filter(Section.class_id == cls.id, Section.name == section_name).first()
                if not existing:
                    section = Section(name=section_name, class_id=cls.id)
                    db.add(section)
                    print(f"  ✓ Added section {section_name} for {cls.name}")
                else:
                    print(f"  - Section {section_name} already exists for {cls.name}")
        
        db.commit()
        
        # Create default users if not exists
        print("\n👤 Creating default users...")
        
        # Admin
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@college.edu",
                password_hash=hash_password("admin123"),
                role=Roles.ADMIN,
                full_name="System Administrator",
                is_active=True
            )
            db.add(admin)
            print("  ✓ Admin created (admin / admin123)")
        else:
            print("  - Admin already exists")
        
        # Teacher
        teacher = db.query(User).filter(User.username == "teacher").first()
        if not teacher:
            teacher = User(
                username="teacher",
                email="teacher@college.edu",
                password_hash=hash_password("teacher123"),
                role=Roles.TEACHER,
                full_name="Professor Smith",
                is_active=True
            )
            db.add(teacher)
            print("  ✓ Teacher created (teacher / teacher123)")
        else:
            print("  - Teacher already exists")
        
        # Demo Student (optional)
        student = db.query(User).filter(User.username == "student").first()
        if not student:
            student = User(
                username="student",
                email="student@college.edu",
                password_hash=hash_password("student123"),
                role=Roles.STUDENT,
                full_name="John Doe",
                is_active=True,
                student_id=1
            )
            db.add(student)
            print("  ✓ Demo student created (student / student123)")
        else:
            print("  - Demo student already exists")
        
        db.commit()
        
        # Show summary
        print("\n" + "="*50)
        print("✅ SETUP COMPLETE!")
        print("="*50)
        print(f"📚 Total Classes: {db.query(Class).count()}")
        print(f"📁 Total Sections: {db.query(Section).count()}")
        print(f"👥 Total Users: {db.query(User).count()}")
        print("\n🔐 Login Credentials:")
        print("   Admin:   admin / admin123")
        print("   Teacher: teacher / teacher123")
        print("   Student: student / student123")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_initial_data()