# models.py
# ─────────────────────────────────────────────────────────────────────────────
# Like your C# Entity / Model classes (Student.cs)
# SQLAlchemy maps these Python classes directly to database tables
# ─────────────────────────────────────────────────────────────────────────────

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Class(Base):
    """Class/Course information"""
    __tablename__ = "classes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # e.g., "BCA 8th Sem", "BSC CS"
    code = Column(String(20), unique=True, nullable=False)  # e.g., "BCA801"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    sections = relationship("Section", back_populates="class_obj", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="class_obj")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description
        }
    
    def __repr__(self):
        return f"<Class id={self.id} name='{self.name}'>"


class Section(Base):
    """Section/Division within a class"""
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)  # e.g., "A", "B", "C"
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    class_obj = relationship("Class", back_populates="sections")
    students = relationship("Student", back_populates="section")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "class_id": self.class_id,
            "class_name": self.class_obj.name if self.class_obj else None
        }
    
    def __repr__(self):
        return f"<Section id={self.id} name='{self.name}'>"


class Student(Base):
    """Student entity - maps to 'students' table"""
    __tablename__ = "students"

    # ── Primary Key ───────────────────────────────────────────────────────
    id = Column(Integer, primary_key=True, autoincrement=True)

    # ── Student Info ──────────────────────────────────────────────────────
    name = Column(String(100), nullable=False)
    roll_number = Column(String(20), nullable=True)  # Student roll number
    attendance = Column(Float, nullable=False)      # 0–100 %
    math_marks = Column(Float, nullable=False)      # 0–100
    science_marks = Column(Float, nullable=False)   # 0–100
    english_marks = Column(Float, nullable=False)   # 0–100
    hours_studied = Column(Float, nullable=False)   # hours per day
    assignments = Column(Float, nullable=False)     # % completed
    prev_gpa = Column(Float, nullable=False)        # 0.0 – 4.0

    # ── Class & Section ───────────────────────────────────────────────────
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=True)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    
    # ── Parent/Contact Info ───────────────────────────────────────────────
    parent_contact = Column(String(20), nullable=True)
    parent_email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    enrollment_date = Column(DateTime, default=func.now())

    # ── ML Prediction Results ─────────────────────────────────────────────
    prediction_rf = Column(String(10), default="")
    prediction_gb = Column(String(10), default="")
    prediction_svm = Column(String(10), default="")
    confidence_rf = Column(Float, default=0.0)
    confidence_gb = Column(Float, default=0.0)
    confidence_svm = Column(Float, default=0.0)
    best_model = Column(String(30), default="")

    # ── Timestamp ─────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=func.now())
    
    # ── Relationships ─────────────────────────────────────────────────────
    class_obj = relationship("Class", back_populates="students")
    section = relationship("Section", back_populates="students")

    # ── Helper Methods ────────────────────────────────────────────────────

    def average_marks(self):
        """Computed property - average of all subjects"""
        return round((self.math_marks + self.science_marks + self.english_marks) / 3, 1)

    def overall_score(self):
        """Weighted score for dashboard display"""
        marks_avg = self.average_marks()
        score = (marks_avg * 0.50 +
                 self.attendance * 0.25 +
                 min(self.hours_studied * 10, 100) * 0.15 +
                 self.assignments * 0.10)
        return round(score, 1)

    def to_dict(self):
        """Convert to dictionary for JSON API"""
        return {
            "id": self.id,
            "roll_number": self.roll_number,
            "name": self.name,
            "attendance": self.attendance,
            "math_marks": self.math_marks,
            "science_marks": self.science_marks,
            "english_marks": self.english_marks,
            "hours_studied": self.hours_studied,
            "assignments": self.assignments,
            "prev_gpa": self.prev_gpa,
            "avg_marks": self.average_marks(),
            "overall_score": self.overall_score(),
            "prediction_rf": self.prediction_rf,
            "prediction_gb": self.prediction_gb,
            "prediction_svm": self.prediction_svm,
            "confidence_rf": self.confidence_rf,
            "confidence_gb": self.confidence_gb,
            "confidence_svm": self.confidence_svm,
            "best_model": self.best_model,
            "class_id": self.class_id,
            "section_id": self.section_id,
            "parent_contact": self.parent_contact,
            "address": self.address,
        }

    def __repr__(self):
        return f"<Student id={self.id} name='{self.name}' prediction='{self.prediction_rf}'>"


class User(Base):
    """User account for login system (Admin, Teacher, Student)"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # admin, teacher, student
    full_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Student specific
    student_id = Column(Integer, unique=True, nullable=True)  # For student roll number
    
    # Relationships
    remarks_sent = relationship("Remark", foreign_keys="Remark.sender_id", backref="sender")
    remarks_received = relationship("Remark", foreign_keys="Remark.receiver_id", backref="receiver")
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "student_id": self.student_id,
        }
    
    def __repr__(self):
        return f"<User id={self.id} username='{self.username}' role='{self.role}'>"


class Remark(Base):
    """Remarks sent from Teacher to Student"""
    __tablename__ = "remarks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_record_id = Column(Integer, ForeignKey("students.id"), nullable=True)
    message = Column(Text, nullable=False)
    remark_type = Column(String(30), default="general")  # general, warning, appreciation, improvement
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "sender": self.sender.full_name if self.sender else "Unknown",
            "message": self.message,
            "remark_type": self.remark_type,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }
    
    def __repr__(self):
        return f"<Remark id={self.id} type='{self.remark_type}'>"


class TrainingHistory(Base):
    """Track when models were retrained (Admin feature)"""
    __tablename__ = "training_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trained_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trained_at = Column(DateTime, default=func.now())
    random_forest_accuracy = Column(Float)
    gradient_boosting_accuracy = Column(Float)
    svm_accuracy = Column(Float)
    best_model = Column(String(50))
    num_samples = Column(Integer)
    
    trained_by = relationship("User", backref="training_history")
    
    def to_dict(self):
        return {
            "id": self.id,
            "trained_by": self.trained_by.full_name if self.trained_by else "Unknown",
            "trained_at": self.trained_at.strftime("%Y-%m-%d %H:%M") if self.trained_at else None,
            "rf_acc": self.random_forest_accuracy,
            "gb_acc": self.gradient_boosting_accuracy,
            "svm_acc": self.svm_accuracy,
            "best_model": self.best_model,
            "num_samples": self.num_samples,
        }
    
    def __repr__(self):
        return f"<TrainingHistory id={self.id} trained_at={self.trained_at}>"