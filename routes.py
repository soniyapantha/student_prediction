# routes.py
# ─────────────────────────────────────────────────────────────────────────────
# Complete routes with Authentication, Roles, Classes, Sections, and Remarks
# ─────────────────────────────────────────────────────────────────────────────

from flask import (render_template, request, redirect,
                   url_for, flash, jsonify, current_app, session, send_file)
from database import SessionLocal
from models import Student, User, Remark, TrainingHistory, Class, Section
from ml_engine import predict_student, train_models, check_models_status
from auth import (login_required, role_required, get_current_user,
                  verify_password, hash_password, Roles)
import os
from config import Config
import pandas as pd
import io
from datetime import datetime
import re


# =============================================================================
# REGISTER ROUTES
# =============================================================================

def register_routes(app):
    
    # ──────────────────────────────────────────────────────────────────────────
    # AUTHENTICATION ROUTES
    # ──────────────────────────────────────────────────────────────────────────
    
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if "user_id" in session:
            role = session.get("role")
            return redirect(url_for(f"dashboard_{role}"))
        
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            
            db = SessionLocal()
            user = db.query(User).filter(User.username == username).first()
            db.close()
            
            if user and verify_password(password, user.password_hash) and user.is_active:
                session["user_id"] = user.id
                session["username"] = user.username
                session["role"] = user.role
                session["full_name"] = user.full_name
                
                flash(f"Welcome back, {user.full_name}!", "success")
                
                if user.role == Roles.ADMIN:
                    return redirect(url_for("dashboard_admin"))
                elif user.role == Roles.TEACHER:
                    return redirect(url_for("dashboard_teacher"))
                else:
                    return redirect(url_for("dashboard_student"))
            else:
                flash("Invalid username or password!", "danger")
        
        return render_template("login.html")
    
    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("login"))
    
    # =========================================================================
    # ADMIN DASHBOARD
    # =========================================================================
    
    @app.route("/admin/dashboard")
    @login_required
    @role_required(Roles.ADMIN)
    def dashboard_admin():
        db = SessionLocal()
        
        try:
            total_students = db.query(Student).count()
            total_users = db.query(User).count()
            total_remarks = db.query(Remark).count()
            unread_remarks = db.query(Remark).filter(Remark.is_read == False).count()
            total_classes = db.query(Class).count()
            total_sections = db.query(Section).count()
            
            recent_students = db.query(Student).order_by(Student.created_at.desc()).limit(10).all()
            recent_predictions = []
            for s in recent_students:
                avg_marks = (s.math_marks + s.science_marks + s.english_marks) / 3
                recent_predictions.append({
                    "id": s.id,
                    "name": s.name,
                    "roll_number": s.roll_number,
                    "avg_marks": round(avg_marks, 1),
                    "prediction_rf": s.prediction_rf,
                    "prediction_gb": s.prediction_gb or s.prediction_rf,
                    "prediction_svm": s.prediction_svm or s.prediction_rf,
                    "best_model": s.best_model or "Random Forest",
                    "created_at": s.created_at
                })
            
            training_history = db.query(TrainingHistory).order_by(TrainingHistory.trained_at.desc()).limit(5).all()
            history_list = []
            for h in training_history:
                history_list.append({
                    "id": h.id,
                    "trained_at": h.trained_at,
                    "trained_by": h.trained_by.full_name if h.trained_by else "Unknown",
                    "rf_acc": h.random_forest_accuracy,
                    "gb_acc": h.gradient_boosting_accuracy,
                    "svm_acc": h.svm_accuracy,
                    "best_model": h.best_model,
                    "num_samples": h.num_samples
                })
            
            models_data = current_app.config.get("ML_MODELS", {})
            models_available = models_data and len(models_data) > 0 and 'Random Forest' in models_data
            
            db.close()
            
            return render_template("dashboard_admin.html",
                                 total_students=total_students,
                                 total_users=total_users,
                                 total_remarks=total_remarks,
                                 unread_remarks=unread_remarks,
                                 total_classes=total_classes,
                                 total_sections=total_sections,
                                 recent_predictions=recent_predictions,
                                 training_history=history_list,
                                 models_data=models_data,
                                 models_available=models_available)
        except Exception as e:
            db.close()
            flash(f"Error loading admin dashboard: {str(e)}", "danger")
            return render_template("dashboard_admin.html", 
                                 total_students=0, total_users=0, total_remarks=0,
                                 unread_remarks=0, total_classes=0, total_sections=0,
                                 recent_predictions=[], training_history=[], models_data={})
    
    # ──────────────────────────────────────────────────────────────────────────
    # ADMIN - CLASS MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────────
    
    @app.route("/admin/classes")
    @login_required
    @role_required(Roles.ADMIN)
    def admin_classes():
        db = SessionLocal()
        classes = db.query(Class).all()
        class_list = []
        for c in classes:
            section_count = db.query(Section).filter(Section.class_id == c.id).count()
            student_count = db.query(Student).filter(Student.class_id == c.id).count()
            class_list.append({
                "id": c.id,
                "name": c.name,
                "code": c.code,
                "description": c.description,
                "section_count": section_count,
                "student_count": student_count
            })
        db.close()
        return render_template("admin_classes.html", classes=class_list)
    
    @app.route("/admin/class/add", methods=["GET", "POST"])
    @login_required
    @role_required(Roles.ADMIN)
    def admin_add_class():
        if request.method == "POST":
            db = SessionLocal()
            try:
                new_class = Class(
                    name=request.form["name"],
                    code=request.form["code"],
                    description=request.form.get("description", "")
                )
                db.add(new_class)
                db.commit()
                flash(f"Class '{new_class.name}' created successfully!", "success")
            except Exception as e:
                db.rollback()
                flash(f"Error: {str(e)}", "danger")
            finally:
                db.close()
            return redirect(url_for("admin_classes"))
        return render_template("admin_add_class.html")
    
    @app.route("/admin/class/<int:class_id>/sections")
    @login_required
    @role_required(Roles.ADMIN)
    def admin_class_sections(class_id):
        db = SessionLocal()
        class_obj = db.query(Class).filter(Class.id == class_id).first()
        sections = db.query(Section).filter(Section.class_id == class_id).all()
        section_list = []
        for s in sections:
            student_count = db.query(Student).filter(Student.section_id == s.id).count()
            section_list.append({
                "id": s.id,
                "name": s.name,
                "student_count": student_count
            })
        db.close()
        return render_template("admin_sections.html", class_obj=class_obj, sections=section_list)
    
    @app.route("/admin/section/add", methods=["POST"])
    @login_required
    @role_required(Roles.ADMIN)
    def admin_add_section():
        class_id = request.form.get("class_id")
        section_name = request.form.get("section_name")
        db = SessionLocal()
        try:
            section = Section(name=section_name, class_id=int(class_id))
            db.add(section)
            db.commit()
            flash(f"Section {section_name} added successfully!", "success")
        except Exception as e:
            db.rollback()
            flash(f"Error: {str(e)}", "danger")
        finally:
            db.close()
        return redirect(url_for("admin_class_sections", class_id=class_id))
    
    # ──────────────────────────────────────────────────────────────────────────
    # ADMIN - USER MANAGEMENT
    # ──────────────────────────────────────────────────────────────────────────
    
    @app.route("/admin/users")
    @login_required
    @role_required(Roles.ADMIN)
    def admin_users():
        db = SessionLocal()
        users = db.query(User).all()
        user_list = []
        for u in users:
            user_list.append({
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "email": u.email,
                "role": u.role,
                "student_id": u.student_id,
                "is_active": u.is_active
            })
        db.close()
        return render_template("admin_users.html", users=user_list)
    
    @app.route("/admin/user/add", methods=["GET", "POST"])
    @login_required
    @role_required(Roles.ADMIN)
    def admin_add_user():
        if request.method == "POST":
            db = SessionLocal()
            try:
                existing_user = db.query(User).filter(User.username == request.form["username"]).first()
                if existing_user:
                    flash(f"Username '{request.form['username']}' already exists!", "danger")
                    db.close()
                    return redirect(url_for("admin_add_user"))
                
                existing_email = db.query(User).filter(User.email == request.form["email"]).first()
                if existing_email:
                    flash(f"Email '{request.form['email']}' already exists!", "danger")
                    db.close()
                    return redirect(url_for("admin_add_user"))
                
                role = request.form["role"]
                student_id = None
                
                if role == "student":
                    student_id_str = request.form.get("student_id", "")
                    if student_id_str and student_id_str.isdigit():
                        student_id = int(student_id_str)
                        student_record = db.query(Student).filter(Student.id == student_id).first()
                        if not student_record:
                            flash(f"Student record with ID {student_id} does not exist!", "danger")
                            db.close()
                            return redirect(url_for("admin_add_user"))
                        
                        existing_link = db.query(User).filter(User.student_id == student_id).first()
                        if existing_link:
                            flash(f"Student ID {student_id} is already linked to user '{existing_link.full_name}'!", "danger")
                            db.close()
                            return redirect(url_for("admin_add_user"))
                
                user = User(
                    username=request.form["username"],
                    email=request.form["email"],
                    password_hash=hash_password(request.form["password"]),
                    role=role,
                    full_name=request.form["full_name"],
                    student_id=student_id if role == "student" else None,
                    is_active=True
                )
                db.add(user)
                db.commit()
                flash(f"User '{user.full_name}' created successfully!", "success")
                
            except Exception as e:
                db.rollback()
                flash(f"Error: {str(e)}", "danger")
            finally:
                db.close()
            return redirect(url_for("admin_users"))
        
        db = SessionLocal()
        linked_student_ids = [u.student_id for u in db.query(User.student_id).filter(User.student_id.isnot(None)).all()]
        available_students = db.query(Student).filter(~Student.id.in_(linked_student_ids)).all() if linked_student_ids else db.query(Student).all()
        
        student_list = [{"id": s.id, "name": s.name, "roll_number": s.roll_number} for s in available_students]
        db.close()
        
        return render_template("admin_add_user.html", available_students=student_list)
    
    @app.route("/admin/user/delete/<int:user_id>")
    @login_required
    @role_required(Roles.ADMIN)
    def admin_delete_user(user_id):
        if user_id == session.get("user_id"):
            flash("Cannot delete your own account!", "danger")
            return redirect(url_for("admin_users"))
        
        db = SessionLocal()
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            name = user.full_name
            db.delete(user)
            db.commit()
            flash(f"User '{name}' deleted.", "info")
        db.close()
        return redirect(url_for("admin_users"))
    
    # ──────────────────────────────────────────────────────────────────────────
    # ADMIN - STUDENT MANAGEMENT (MODIFIED: Academic marks are now OPTIONAL)
    # ──────────────────────────────────────────────────────────────────────────
    
    @app.route("/admin/add-student", methods=["GET", "POST"])
    @login_required
    @role_required(Roles.ADMIN)
    def admin_add_student():
        # Get classes for dropdown
        db = SessionLocal()
        try:
            classes_db = db.query(Class).all()
            class_list = []
            for c in classes_db:
                class_list.append({
                    "id": c.id,
                    "name": c.name
                })
        except Exception as e:
            print(f"Error loading classes: {e}")
            class_list = []
        finally:
            db.close()
        
        if request.method == "POST":
            db = SessionLocal()
            try:
                # Get form values - with proper handling for empty/optional fields
                roll_number = request.form.get("roll_number", "")
                name = request.form.get("name", "").strip()
                
                # Academic marks - OPTIONAL, default to 0 if empty
                attendance_str = request.form.get("attendance", "")
                attendance = float(attendance_str) if attendance_str and attendance_str.strip() else 0.0
                
                math_marks_str = request.form.get("math_marks", "")
                math_marks = float(math_marks_str) if math_marks_str and math_marks_str.strip() else 0.0
                
                science_marks_str = request.form.get("science_marks", "")
                science_marks = float(science_marks_str) if science_marks_str and science_marks_str.strip() else 0.0
                
                english_marks_str = request.form.get("english_marks", "")
                english_marks = float(english_marks_str) if english_marks_str and english_marks_str.strip() else 0.0
                
                hours_studied_str = request.form.get("hours_studied", "")
                hours_studied = float(hours_studied_str) if hours_studied_str and hours_studied_str.strip() else 0.0
                
                assignments_str = request.form.get("assignments", "")
                assignments = float(assignments_str) if assignments_str and assignments_str.strip() else 0.0
                
                prev_gpa_str = request.form.get("prev_gpa", "")
                prev_gpa = float(prev_gpa_str) if prev_gpa_str and prev_gpa_str.strip() else 0.0
                
                class_id_str = request.form.get("class_id", "")
                class_id = int(class_id_str) if class_id_str and class_id_str.isdigit() else None
                
                section_id_str = request.form.get("section_id", "")
                section_id = None
                if section_id_str and section_id_str.isdigit():
                    section_id = int(section_id_str)
                
                parent_contact = request.form.get("parent_contact", "")
                address = request.form.get("address", "")
                
                # Validate required fields
                if not name:
                    flash("Student name is required!", "danger")
                    db.close()
                    return redirect(url_for("admin_add_student"))
                
                # Create student FIRST (without user account)
                student = Student(
                    roll_number=roll_number,
                    name=name,
                    attendance=attendance,
                    math_marks=math_marks,
                    science_marks=science_marks,
                    english_marks=english_marks,
                    hours_studied=hours_studied,
                    assignments=assignments,
                    prev_gpa=prev_gpa,
                    class_id=class_id,
                    section_id=section_id,
                    parent_contact=parent_contact,
                    address=address
                )
                
                # Run prediction only if at least some academic data is provided
                has_academic_data = any([
                    attendance > 0, math_marks > 0, science_marks > 0, 
                    english_marks > 0, hours_studied > 0, assignments > 0, prev_gpa > 0
                ])
                
                if has_academic_data:
                    student_input = {
                        "attendance": student.attendance,
                        "math_marks": student.math_marks,
                        "science_marks": student.science_marks,
                        "english_marks": student.english_marks,
                        "hours_studied": student.hours_studied,
                        "assignments": student.assignments,
                        "prev_gpa": student.prev_gpa,
                    }
                    
                    models_data = current_app.config.get("ML_MODELS", {})
                    
                    # Check if models are available and valid
                    if not models_data or len(models_data) == 0 or 'Random Forest' not in models_data:
                        print("[WARNING] ML models not available, using default predictions")
                        student.prediction_rf = 65.0
                        student.prediction_gb = 65.0
                        student.prediction_svm = 65.0
                        student.confidence_rf = 70.0
                        student.confidence_gb = 70.0
                        student.confidence_svm = 70.0
                        student.best_model = "Default (Train models for better predictions)"
                        flash("ℹ️ Note: Using default predictions. Train ML models for better accuracy.", "info")
                    else:
                        try:
                            predictions = predict_student(models_data, student_input)
                            student.prediction_rf = predictions["Random Forest"]["result"]
                            student.prediction_gb = predictions["Gradient Boosting"]["result"]
                            student.prediction_svm = predictions["SVM"]["result"]
                            student.confidence_rf = predictions["Random Forest"]["confidence"]
                            student.confidence_gb = predictions["Gradient Boosting"]["confidence"]
                            student.confidence_svm = predictions["SVM"]["confidence"]
                            student.best_model = predictions["best_model"]
                        except Exception as e:
                            print(f"[ERROR] Prediction failed: {str(e)}")
                            student.prediction_rf = 65.0
                            student.prediction_gb = 65.0
                            student.prediction_svm = 65.0
                            student.confidence_rf = 70.0
                            student.confidence_gb = 70.0
                            student.confidence_svm = 70.0
                            student.best_model = "Default (Prediction Error)"
                            flash(f"⚠️ Warning: Could not generate ML predictions. Using default values.", "warning")
                else:
                    # No academic data provided, set default predictions
                    student.prediction_rf = 0.0
                    student.prediction_gb = 0.0
                    student.prediction_svm = 0.0
                    student.confidence_rf = 0.0
                    student.confidence_gb = 0.0
                    student.confidence_svm = 0.0
                    student.best_model = "No Data Available"
                    flash("ℹ️ Note: No academic marks provided. Predictions will be available after adding marks.", "info")
                
                # Add student to database FIRST to get the auto-generated ID
                db.add(student)
                db.commit()
                db.refresh(student)
                
                # Now create login if requested
                create_login = request.form.get("create_login", "no")
                if create_login == "yes":
                    # Generate username
                    username = request.form.get("username", "").strip()
                    if not username:
                        base_username = student.name.lower().replace(" ", "_").replace(".", "")
                        base_username = re.sub(r'[^a-z0-9_]', '', base_username)
                        if student.roll_number:
                            username = f"{base_username}_{student.roll_number}"
                        else:
                            username = f"{base_username}_{student.id}"
                    
                    password = request.form.get("password", "").strip()
                    if not password:
                        password = "student123"
                    
                    email = request.form.get("email", "").strip()
                    if not email:
                        email = f"{username}@college.edu"
                    
                    # Check if username already exists
                    existing_user_by_username = db.query(User).filter(User.username == username).first()
                    if existing_user_by_username:
                        flash(f"⚠️ Student '{student.name}' added! But username '{username}' already exists. No login created.", "warning")
                    else:
                        # Check if student_id is already linked to another user
                        existing_user_by_student_id = db.query(User).filter(User.student_id == student.id).first()
                        if existing_user_by_student_id:
                            flash(f"⚠️ Student '{student.name}' added! But this student already has a login account.", "warning")
                        else:
                            try:
                                student_user = User(
                                    username=username,
                                    email=email,
                                    password_hash=hash_password(password),
                                    role=Roles.STUDENT,
                                    full_name=student.name,
                                    student_id=student.id,
                                    is_active=True
                                )
                                db.add(student_user)
                                db.commit()
                                flash(f"✅ Student '{student.name}' added successfully with login!", "success")
                                flash(f"🔐 Login credentials - Username: {username}, Password: {password}", "info")
                            except Exception as e:
                                db.rollback()
                                flash(f"⚠️ Student '{student.name}' added! But could not create login: {str(e)}", "warning")
                else:
                    flash(f"✅ Student '{student.name}' added successfully! (No login created)", "success")
                
                db.close()
                return redirect(url_for("admin_students_list"))
                
            except Exception as e:
                db.rollback()
                error_msg = str(e)
                flash(f"Error adding student: {error_msg}", "danger")
                print(f"[ERROR] Failed to add student: {error_msg}")
                import traceback
                traceback.print_exc()
                db.close()
        
        return render_template("admin_add_student.html", classes=class_list)
    
    @app.route("/admin/students")
    @login_required
    @role_required(Roles.ADMIN)
    def admin_students_list():
        db = SessionLocal()
        students = db.query(Student).order_by(Student.created_at.desc()).all()
        student_list = []
        for s in students:
            avg_marks = (s.math_marks + s.science_marks + s.english_marks) / 3 if (s.math_marks + s.science_marks + s.english_marks) > 0 else 0
            user_exists = db.query(User).filter(User.student_id == s.id).first() is not None
            student_list.append({
                "id": s.id,
                "roll_number": s.roll_number,
                "name": s.name,
                "attendance": s.attendance,
                "avg_marks": round(avg_marks, 1),
                "prediction_rf": s.prediction_rf,
                "has_login": user_exists,
                "created_at": s.created_at
            })
        db.close()
        return render_template("admin_students_list.html", students=student_list)
    
    # NEW ROUTE: Admin Student Detail View
    @app.route("/admin/student/<int:student_id>")
    @login_required
    @role_required(Roles.ADMIN)
    def admin_student_detail(student_id):
        """Admin view for student details"""
        db = SessionLocal()
        try:
            student_db = db.query(Student).filter(Student.id == student_id).first()
            
            if not student_db:
                flash("Student record not found.", "danger")
                db.close()
                return redirect(url_for("admin_students_list"))
            
            avg_marks = (student_db.math_marks + student_db.science_marks + student_db.english_marks) / 3 if (student_db.math_marks + student_db.science_marks + student_db.english_marks) > 0 else 0
            
            # Get class and section info
            class_info = None
            section_info = None
            if student_db.class_id:
                class_obj = db.query(Class).filter(Class.id == student_db.class_id).first()
                class_info = class_obj.name if class_obj else None
            if student_db.section_id:
                section_obj = db.query(Section).filter(Section.id == student_db.section_id).first()
                section_info = section_obj.name if section_obj else None
            
            student = {
                "id": student_db.id,
                "roll_number": student_db.roll_number,
                "name": student_db.name,
                "attendance": student_db.attendance,
                "math_marks": student_db.math_marks,
                "science_marks": student_db.science_marks,
                "english_marks": student_db.english_marks,
                "hours_studied": student_db.hours_studied,
                "assignments": student_db.assignments,
                "prev_gpa": student_db.prev_gpa,
                "prediction_rf": student_db.prediction_rf,
                "prediction_gb": student_db.prediction_gb or student_db.prediction_rf,
                "prediction_svm": student_db.prediction_svm or student_db.prediction_rf,
                "confidence_rf": student_db.confidence_rf or 85.0,
                "confidence_gb": student_db.confidence_gb or 85.0,
                "confidence_svm": student_db.confidence_svm or 85.0,
                "best_model": student_db.best_model or "Random Forest",
                "avg_marks": round(avg_marks, 1),
                "class_name": class_info,
                "section_name": section_info,
                "parent_contact": student_db.parent_contact,
                "address": student_db.address,
                "overall_score": round((avg_marks * 0.50 + student_db.attendance * 0.25 + min(student_db.hours_studied * 10, 100) * 0.15 + student_db.assignments * 0.10), 1) if avg_marks > 0 else 0,
                "created_at": student_db.created_at
            }
            
            # Get user account info if exists
            user_account = db.query(User).filter(User.student_id == student_id).first()
            user_info = None
            if user_account:
                user_info = {
                    "username": user_account.username,
                    "email": user_account.email,
                    "is_active": user_account.is_active
                }
            
            # Get remarks for this student
            remarks = []
            if user_account:
                remarks_db = db.query(Remark).filter(Remark.receiver_id == user_account.id)\
                           .order_by(Remark.created_at.desc()).all()
                for r in remarks_db:
                    remarks.append({
                        "id": r.id,
                        "message": r.message,
                        "remark_type": r.remark_type,
                        "created_at": r.created_at,
                        "sender": r.sender.full_name if r.sender else "Teacher"
                    })
            
            db.close()
            return render_template("admin_student_detail.html", 
                                 student=student, 
                                 user_info=user_info,
                                 remarks=remarks)
            
        except Exception as e:
            db.close()
            flash(f"Error loading student details: {str(e)}", "danger")
            return redirect(url_for("admin_students_list"))
    
    @app.route("/admin/retrain", methods=["POST"])
    @login_required
    @role_required(Roles.ADMIN)
    def admin_retrain():
        current_user = get_current_user()
        
        if os.path.exists(Config.MODEL_FILE):
            os.remove(Config.MODEL_FILE)
        
        trained_models = train_models(force_retrain=True)
        
        if trained_models:
            current_app.config["ML_MODELS"] = trained_models
            
            db = SessionLocal()
            try:
                df = pd.read_csv(Config.DATA_FILE)
                num_samples = len(df)
            except:
                num_samples = 0
                
            history = TrainingHistory(
                trained_by_id=current_user.id,
                random_forest_accuracy=trained_models.get("Random Forest", {}).get("accuracy", 0),
                gradient_boosting_accuracy=trained_models.get("Gradient Boosting", {}).get("accuracy", 0),
                svm_accuracy=trained_models.get("SVM", {}).get("accuracy", 0),
                best_model=trained_models.get("best_model_selected", "Random Forest"),
                num_samples=num_samples
            )
            db.add(history)
            db.commit()
            db.close()
            
            flash("All 3 ML models retrained successfully!", "success")
        else:
            flash("Failed to retrain models. Please check your data file.", "danger")
        
        return redirect(url_for("dashboard_admin"))
    
    @app.route("/admin/training-history")
    @login_required
    @role_required(Roles.ADMIN)
    def admin_training_history():
        db = SessionLocal()
        history = db.query(TrainingHistory).order_by(TrainingHistory.trained_at.desc()).all()
        history_list = []
        for h in history:
            history_list.append({
                "id": h.id,
                "trained_at": h.trained_at.strftime("%Y-%m-%d %H:%M") if h.trained_at else "Unknown",
                "trained_by": h.trained_by.full_name if h.trained_by else "Unknown",
                "rf_acc": h.random_forest_accuracy,
                "gb_acc": h.gradient_boosting_accuracy,
                "svm_acc": h.svm_accuracy,
                "best_model": h.best_model,
                "num_samples": h.num_samples
            })
        db.close()
        return render_template("admin_training_history.html", history=history_list)
    
    # =========================================================================
    # TEACHER DASHBOARD
    # =========================================================================
    
    @app.route("/teacher/dashboard")
    @login_required
    @role_required(Roles.TEACHER)
    def dashboard_teacher():
        db = SessionLocal()
        classes = db.query(Class).all()
        class_list = [{"id": c.id, "name": c.name, "code": c.code} for c in classes]
        db.close()
        return render_template("teacher_dashboard_new.html", classes=class_list)
    
    @app.route("/teacher/add-student-api", methods=["POST"])
    @login_required
    @role_required(Roles.TEACHER)
    def teacher_add_student_api():
        db = SessionLocal()
        try:
            roll_number = request.form.get("roll_number", "")
            name = request.form.get("name", "").strip()
            attendance = float(request.form.get("attendance", 0))
            math_marks = float(request.form.get("math_marks", 0))
            science_marks = float(request.form.get("science_marks", 0))
            english_marks = float(request.form.get("english_marks", 0))
            hours_studied = float(request.form.get("hours_studied", 0))
            assignments = float(request.form.get("assignments", 0))
            prev_gpa = float(request.form.get("prev_gpa", 0))
            
            class_id_str = request.form.get("class_id", "")
            class_id = int(class_id_str) if class_id_str and class_id_str.isdigit() else None
            
            section_id_str = request.form.get("section_id", "")
            section_id = None
            if section_id_str and section_id_str.isdigit():
                section_id = int(section_id_str)
            
            parent_contact = request.form.get("parent_contact", "")
            address = request.form.get("address", "")
            
            student = Student(
                roll_number=roll_number,
                name=name,
                attendance=attendance,
                math_marks=math_marks,
                science_marks=science_marks,
                english_marks=english_marks,
                hours_studied=hours_studied,
                assignments=assignments,
                prev_gpa=prev_gpa,
                class_id=class_id,
                section_id=section_id,
                parent_contact=parent_contact,
                address=address
            )
            
            student_input = {
                "attendance": student.attendance,
                "math_marks": student.math_marks,
                "science_marks": student.science_marks,
                "english_marks": student.english_marks,
                "hours_studied": student.hours_studied,
                "assignments": student.assignments,
                "prev_gpa": student.prev_gpa,
            }
            
            models_data = current_app.config.get("ML_MODELS", {})
            
            if not models_data or len(models_data) == 0:
                student.prediction_rf = 65.0
                student.prediction_gb = 65.0
                student.prediction_svm = 65.0
                student.confidence_rf = 70.0
                student.confidence_gb = 70.0
                student.confidence_svm = 70.0
                student.best_model = "Default"
            else:
                predictions = predict_student(models_data, student_input)
                student.prediction_rf = predictions["Random Forest"]["result"]
                student.prediction_gb = predictions["Gradient Boosting"]["result"]
                student.prediction_svm = predictions["SVM"]["result"]
                student.confidence_rf = predictions["Random Forest"]["confidence"]
                student.confidence_gb = predictions["Gradient Boosting"]["confidence"]
                student.confidence_svm = predictions["SVM"]["confidence"]
                student.best_model = predictions["best_model"]
            
            db.add(student)
            db.commit()
            db.refresh(student)
            
            base_username = student.name.lower().replace(" ", "_")
            if student.roll_number:
                username = f"{base_username}_{student.roll_number}"
            else:
                username = f"{base_username}_{student.id}"
            
            default_password = "student123"
            
            existing_user = db.query(User).filter(User.student_id == student.id).first()
            if not existing_user:
                student_user = User(
                    username=username,
                    email=f"{username}@college.edu",
                    password_hash=hash_password(default_password),
                    role=Roles.STUDENT,
                    full_name=student.name,
                    student_id=student.id,
                    is_active=True
                )
                db.add(student_user)
                db.commit()
                
                flash(f"✅ Student '{student.name}' added successfully!", "success")
                flash(f"🔐 Login credentials - Username: {username}, Password: {default_password}", "info")
            else:
                flash(f"✅ Student '{student.name}' added!", "success")
            
            db.close()
            return redirect(url_for("teacher_student_detail", student_id=student.id))
            
        except Exception as e:
            db.rollback()
            flash(f"Error: {str(e)}", "danger")
            db.close()
            return redirect(url_for("dashboard_teacher"))
    
    @app.route("/teacher/bulk-marks", methods=["POST"])
    @login_required
    @role_required(Roles.TEACHER)
    def teacher_bulk_marks():
        if 'csv_file' not in request.files:
            flash("No file uploaded", "danger")
            return redirect(url_for("dashboard_teacher"))
        
        file = request.files['csv_file']
        if file.filename == '':
            flash("No file selected", "danger")
            return redirect(url_for("dashboard_teacher"))
        
        try:
            df = pd.read_csv(file)
            db = SessionLocal()
            updated = 0
            
            for _, row in df.iterrows():
                student = db.query(Student).filter(Student.roll_number == str(row['roll_number'])).first()
                if student:
                    student.math_marks = float(row['math_marks'])
                    student.science_marks = float(row['science_marks'])
                    student.english_marks = float(row['english_marks'])
                    student.attendance = float(row['attendance'])
                    
                    student_input = {
                        "attendance": student.attendance,
                        "math_marks": student.math_marks,
                        "science_marks": student.science_marks,
                        "english_marks": student.english_marks,
                        "hours_studied": student.hours_studied,
                        "assignments": student.assignments,
                        "prev_gpa": student.prev_gpa,
                    }
                    models_data = current_app.config.get("ML_MODELS", {})
                    
                    if models_data and len(models_data) > 0:
                        predictions = predict_student(models_data, student_input)
                        student.prediction_rf = predictions["Random Forest"]["result"]
                        student.prediction_gb = predictions["Gradient Boosting"]["result"]
                        student.prediction_svm = predictions["SVM"]["result"]
                        student.best_model = predictions["best_model"]
                    updated += 1
            
            db.commit()
            db.close()
            flash(f"Updated {updated} students successfully!", "success")
        except Exception as e:
            flash(f"Error processing file: {str(e)}", "danger")
        
        return redirect(url_for("dashboard_teacher"))
    
    @app.route("/teacher/download-template")
    @login_required
    @role_required(Roles.TEACHER)
    def download_marks_template():
        template = pd.DataFrame({
            'roll_number': ['BCA001', 'BCA002'],
            'math_marks': [85, 45],
            'science_marks': [90, 50],
            'english_marks': [88, 55],
            'attendance': [95, 60]
        })
        
        output = io.BytesIO()
        template.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(output, mimetype='text/csv', as_attachment=True, download_name='marks_template.csv')
    
    @app.route("/teacher/student/<int:student_id>")
    @login_required
    @role_required(Roles.TEACHER)
    def teacher_student_detail(student_id):
        db = SessionLocal()
        try:
            student_db = db.query(Student).filter(Student.id == student_id).first()
            
            if not student_db:
                flash("Student record not found.", "danger")
                db.close()
                return redirect(url_for("dashboard_teacher"))
            
            avg_marks = (student_db.math_marks + student_db.science_marks + student_db.english_marks) / 3 if (student_db.math_marks + student_db.science_marks + student_db.english_marks) > 0 else 0
            
            student = {
                "id": student_db.id,
                "roll_number": student_db.roll_number,
                "name": student_db.name,
                "attendance": student_db.attendance,
                "math_marks": student_db.math_marks,
                "science_marks": student_db.science_marks,
                "english_marks": student_db.english_marks,
                "hours_studied": student_db.hours_studied,
                "assignments": student_db.assignments,
                "prev_gpa": student_db.prev_gpa,
                "prediction_rf": student_db.prediction_rf,
                "prediction_gb": student_db.prediction_gb or student_db.prediction_rf,
                "prediction_svm": student_db.prediction_svm or student_db.prediction_rf,
                "confidence_rf": student_db.confidence_rf or 85.0,
                "confidence_gb": student_db.confidence_gb or 85.0,
                "confidence_svm": student_db.confidence_svm or 85.0,
                "best_model": student_db.best_model or "Random Forest",
                "avg_marks": round(avg_marks, 1),
                "parent_contact": student_db.parent_contact,
                "address": student_db.address,
                "overall_score": round((avg_marks * 0.50 + student_db.attendance * 0.25 + min(student_db.hours_studied * 10, 100) * 0.15 + student_db.assignments * 0.10), 1) if avg_marks > 0 else 0,
                "created_at": student_db.created_at
            }
            
            student_user = db.query(User).filter(User.student_id == student_id).first()
            remarks = []
            if student_user:
                remarks_db = db.query(Remark).filter(Remark.receiver_id == student_user.id)\
                           .order_by(Remark.created_at.desc()).all()
                for r in remarks_db:
                    remarks.append({
                        "id": r.id,
                        "message": r.message,
                        "remark_type": r.remark_type,
                        "created_at": r.created_at,
                        "sender": r.sender.full_name if r.sender else "Teacher"
                    })
            
            db.close()
            return render_template("teacher_student_detail.html", student=student, remarks=remarks)
            
        except Exception as e:
            db.close()
            flash(f"Error: {str(e)}", "danger")
            return redirect(url_for("dashboard_teacher"))
    
    @app.route("/teacher/send-remark/<int:student_record_id>", methods=["GET", "POST"])
    @login_required
    @role_required(Roles.TEACHER)
    def teacher_send_remark(student_record_id):
        db = SessionLocal()
        
        student_db = db.query(Student).filter(Student.id == student_record_id).first()
        if not student_db:
            flash("Student record not found.", "danger")
            db.close()
            return redirect(url_for("dashboard_teacher"))
        
        student = {
            "id": student_db.id,
            "name": student_db.name,
            "prediction_rf": student_db.prediction_rf
        }
        
        student_user = db.query(User).filter(User.student_id == student_record_id).first()
        
        if not student_user:
            flash("No user account linked to this student record.", "warning")
            db.close()
            return redirect(url_for("teacher_student_detail", student_id=student_record_id))
        
        if request.method == "POST":
            remark_type = request.form.get("remark_type", "general")
            message = request.form.get("message", "").strip()
            
            if message:
                remark = Remark(
                    sender_id=session["user_id"],
                    receiver_id=student_user.id,
                    student_record_id=student_record_id,
                    message=message,
                    remark_type=remark_type
                )
                db.add(remark)
                db.commit()
                flash(f"Remark sent to {student['name']}!", "success")
                db.close()
                return redirect(url_for("teacher_student_detail", student_id=student_record_id))
            else:
                flash("Please enter a message.", "danger")
        
        db.close()
        return render_template("teacher_send_remark.html", student=student)
    
    # =========================================================================
    # STUDENT DASHBOARD
    # =========================================================================
    
    @app.route("/student/dashboard")
    @login_required
    @role_required(Roles.STUDENT)
    def dashboard_student():
        current_user_obj = get_current_user()
        db = SessionLocal()
        
        try:
            student_dict = None
            if current_user_obj and current_user_obj.student_id:
                student_db = db.query(Student).filter(Student.id == current_user_obj.student_id).first()
                
                if student_db:
                    avg_marks = (student_db.math_marks + student_db.science_marks + student_db.english_marks) / 3 if (student_db.math_marks + student_db.science_marks + student_db.english_marks) > 0 else 0
                    
                    class_info = None
                    section_info = None
                    if student_db.class_id:
                        class_obj = db.query(Class).filter(Class.id == student_db.class_id).first()
                        class_info = class_obj.name if class_obj else None
                    if student_db.section_id:
                        section_obj = db.query(Section).filter(Section.id == student_db.section_id).first()
                        section_info = section_obj.name if section_obj else None
                    
                    student_dict = {
                        "id": student_db.id,
                        "roll_number": student_db.roll_number,
                        "name": student_db.name,
                        "attendance": student_db.attendance,
                        "math_marks": student_db.math_marks,
                        "science_marks": student_db.science_marks,
                        "english_marks": student_db.english_marks,
                        "hours_studied": student_db.hours_studied,
                        "assignments": student_db.assignments,
                        "prev_gpa": student_db.prev_gpa,
                        "prediction_rf": student_db.prediction_rf,
                        "prediction_gb": student_db.prediction_gb or student_db.prediction_rf,
                        "prediction_svm": student_db.prediction_svm or student_db.prediction_rf,
                        "confidence_rf": student_db.confidence_rf or 85.0,
                        "confidence_gb": student_db.confidence_gb or 85.0,
                        "confidence_svm": student_db.confidence_svm or 85.0,
                        "best_model": student_db.best_model or "Random Forest",
                        "avg_marks": round(avg_marks, 1),
                        "class_name": class_info,
                        "section_name": section_info,
                        "overall_score": round((avg_marks * 0.50 + student_db.attendance * 0.25 + min(student_db.hours_studied * 10, 100) * 0.15 + student_db.assignments * 0.10), 1) if avg_marks > 0 else 0,
                    }
            
            remarks = []
            remarks_db = db.query(Remark).filter(Remark.receiver_id == current_user_obj.id)\
                      .order_by(Remark.created_at.desc()).all()
            
            for r in remarks_db:
                if not r.is_read:
                    r.is_read = True
                remarks.append({
                    "id": r.id,
                    "sender": r.sender.full_name if r.sender else "Teacher",
                    "message": r.message,
                    "remark_type": r.remark_type,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "Unknown"
                })
            
            db.commit()
            db.close()
            
            user_dict = {
                "id": current_user_obj.id,
                "username": current_user_obj.username,
                "full_name": current_user_obj.full_name,
                "role": current_user_obj.role
            }
            
            return render_template("dashboard_student.html",
                                 student=student_dict,
                                 remarks=remarks,
                                 user=user_dict)
            
        except Exception as e:
            db.close()
            flash(f"Error loading dashboard: {str(e)}", "danger")
            return render_template("dashboard_student.html",
                                 student=None,
                                 remarks=[],
                                 user={"full_name": "Student"})
    
    @app.route("/student/my-prediction")
    @login_required
    @role_required(Roles.STUDENT)
    def student_my_prediction():
        current_user_obj = get_current_user()
        db = SessionLocal()
        
        try:
            student_dict = None
            if current_user_obj and current_user_obj.student_id:
                student_db = db.query(Student).filter(Student.id == current_user_obj.student_id).first()
                
                if student_db:
                    avg_marks = (student_db.math_marks + student_db.science_marks + student_db.english_marks) / 3 if (student_db.math_marks + student_db.science_marks + student_db.english_marks) > 0 else 0
                    
                    student_dict = {
                        "id": student_db.id,
                        "roll_number": student_db.roll_number,
                        "name": student_db.name,
                        "attendance": student_db.attendance,
                        "math_marks": student_db.math_marks,
                        "science_marks": student_db.science_marks,
                        "english_marks": student_db.english_marks,
                        "hours_studied": student_db.hours_studied,
                        "assignments": student_db.assignments,
                        "prev_gpa": student_db.prev_gpa,
                        "prediction_rf": student_db.prediction_rf,
                        "prediction_gb": student_db.prediction_gb or student_db.prediction_rf,
                        "prediction_svm": student_db.prediction_svm or student_db.prediction_rf,
                        "confidence_rf": student_db.confidence_rf or 85.0,
                        "confidence_gb": student_db.confidence_gb or 85.0,
                        "confidence_svm": student_db.confidence_svm or 85.0,
                        "best_model": student_db.best_model or "Random Forest",
                        "avg_marks": round(avg_marks, 1),
                    }
            
            db.close()
            
            if not student_dict:
                flash("No student record found linked to your account.", "warning")
            
            return render_template("student_my_prediction.html", student=student_dict)
            
        except Exception as e:
            db.close()
            flash(f"Error: {str(e)}", "danger")
            return render_template("student_my_prediction.html", student=None)
    
    # =========================================================================
    # API ROUTES
    # =========================================================================
    
    @app.route("/api/classes")
    @login_required
    def api_classes():
        db = SessionLocal()
        classes = db.query(Class).all()
        result = [{"id": c.id, "name": c.name, "code": c.code} for c in classes]
        db.close()
        return jsonify(result)
    
    @app.route("/api/classes/<int:class_id>/sections")
    @login_required
    def api_class_sections(class_id):
        db = SessionLocal()
        sections = db.query(Section).filter(Section.class_id == class_id).all()
        result = [{"id": s.id, "name": s.name} for s in sections]
        db.close()
        return jsonify(result)
    
    @app.route("/api/sections/<int:section_id>/students")
    @login_required
    def api_section_students(section_id):
        db = SessionLocal()
        students = db.query(Student).filter(Student.section_id == section_id).all()
        student_list = []
        for s in students:
            avg_marks = (s.math_marks + s.science_marks + s.english_marks) / 3 if (s.math_marks + s.science_marks + s.english_marks) > 0 else 0
            student_list.append({
                "id": s.id,
                "roll_number": s.roll_number,
                "name": s.name,
                "attendance": s.attendance,
                "math_marks": s.math_marks,
                "science_marks": s.science_marks,
                "english_marks": s.english_marks,
                "avg_marks": round(avg_marks, 1),
                "prediction": s.prediction_rf
            })
        db.close()
        return jsonify({"total": len(student_list), "students": student_list})
    
    @app.route("/api/students/<int:student_id>", methods=["DELETE"])
    @login_required
    def api_delete_student(student_id):
        db = SessionLocal()
        student = db.query(Student).filter(Student.id == student_id).first()
        if student:
            user = db.query(User).filter(User.student_id == student_id).first()
            if user:
                db.delete(user)
            db.delete(student)
            db.commit()
            db.close()
            return jsonify({"success": True})
        db.close()
        return jsonify({"success": False, "error": "Student not found"}), 404
    
    @app.route("/api/students")
    @login_required
    def api_students():
        db = SessionLocal()
        students = db.query(Student).all()
        student_list = []
        for s in students:
            student_list.append({
                "id": s.id,
                "name": s.name,
                "roll_number": s.roll_number,
                "prediction_rf": s.prediction_rf
            })
        db.close()
        return jsonify(student_list)
    
    # =========================================================================
    # CRUD ROUTES (Shared)
    # =========================================================================
    
    @app.route("/student/edit/<int:student_id>", methods=["GET", "POST"])
    @login_required
    @role_required(Roles.TEACHER, Roles.ADMIN)
    def edit_student(student_id):
        db = SessionLocal()
        student = db.query(Student).filter(Student.id == student_id).first()
        
        if not student:
            flash("Student not found.", "danger")
            db.close()
            return redirect(url_for("dashboard_teacher"))
        
        if request.method == "POST":
            try:
                student.name = request.form["name"].strip()
                student.attendance = float(request.form["attendance"]) if request.form.get("attendance") else 0
                student.math_marks = float(request.form["math_marks"]) if request.form.get("math_marks") else 0
                student.science_marks = float(request.form["science_marks"]) if request.form.get("science_marks") else 0
                student.english_marks = float(request.form["english_marks"]) if request.form.get("english_marks") else 0
                student.hours_studied = float(request.form["hours_studied"]) if request.form.get("hours_studied") else 0
                student.assignments = float(request.form["assignments"]) if request.form.get("assignments") else 0
                student.prev_gpa = float(request.form["prev_gpa"]) if request.form.get("prev_gpa") else 0
                
                # Only run prediction if there is academic data
                has_academic_data = any([
                    student.attendance > 0, student.math_marks > 0, student.science_marks > 0,
                    student.english_marks > 0, student.hours_studied > 0, student.assignments > 0, student.prev_gpa > 0
                ])
                
                if has_academic_data:
                    student_input = {
                        "attendance": student.attendance,
                        "math_marks": student.math_marks,
                        "science_marks": student.science_marks,
                        "english_marks": student.english_marks,
                        "hours_studied": student.hours_studied,
                        "assignments": student.assignments,
                        "prev_gpa": student.prev_gpa,
                    }
                    
                    models_data = current_app.config.get("ML_MODELS", {})
                    
                    if models_data and len(models_data) > 0:
                        predictions = predict_student(models_data, student_input)
                        student.prediction_rf = predictions["Random Forest"]["result"]
                        student.prediction_gb = predictions["Gradient Boosting"]["result"]
                        student.prediction_svm = predictions["SVM"]["result"]
                        student.confidence_rf = predictions["Random Forest"]["confidence"]
                        student.confidence_gb = predictions["Gradient Boosting"]["confidence"]
                        student.confidence_svm = predictions["SVM"]["confidence"]
                        student.best_model = predictions["best_model"]
                
                db.commit()
                flash(f"Student '{student.name}' updated successfully!", "success")
                db.close()
                
                # Redirect based on role
                if session.get("role") == Roles.ADMIN:
                    return redirect(url_for("admin_student_detail", student_id=student_id))
                else:
                    return redirect(url_for("teacher_student_detail", student_id=student_id))
                
            except Exception as e:
                db.rollback()
                flash(f"Error: {str(e)}", "danger")
        
        student_dict = {
            "id": student.id,
            "name": student.name,
            "attendance": student.attendance,
            "math_marks": student.math_marks,
            "science_marks": student.science_marks,
            "english_marks": student.english_marks,
            "hours_studied": student.hours_studied,
            "assignments": student.assignments,
            "prev_gpa": student.prev_gpa,
        }
        db.close()
        return render_template("edit_student.html", student=student_dict)
    
    @app.route("/student/delete/<int:student_id>")
    @login_required
    @role_required(Roles.TEACHER, Roles.ADMIN)
    def delete_student(student_id):
        db = SessionLocal()
        student = db.query(Student).filter(Student.id == student_id).first()
        if student:
            name = student.name
            user = db.query(User).filter(User.student_id == student_id).first()
            if user:
                db.delete(user)
            db.delete(student)
            db.commit()
            flash(f"Student '{name}' deleted.", "info")
        db.close()
        
        role = session.get("role")
        return redirect(url_for(f"dashboard_{role}"))
    
    # =========================================================================
    # ROOT REDIRECT
    # =========================================================================
    
    @app.route("/")
    def index():
        if "user_id" in session:
            role = session.get("role")
            return redirect(url_for(f"dashboard_{role}"))
        return redirect(url_for("login"))