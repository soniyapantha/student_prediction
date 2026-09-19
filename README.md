# Student Performance Prediction System
### BCA 8th Semester Project — Python + Machine Learning

---

## What This Project Does
This web application predicts whether a student will **Pass or Fail**
using 3 advanced Machine Learning algorithms, each giving an independent result
with a confidence score. It also has full **CRUD** (Create, Read, Update, Delete)
for student records stored in a database.

---

## 3 Advanced ML Algorithms Used

| Algorithm | .NET Analogy | Why Advanced |
|---|---|---|
| **Random Forest** | 200 service methods voting on the same answer | Ensemble — 200 trees, majority wins |
| **Gradient Boosting** | Retry loop that learns from each failure | Sequential self-correcting trees |
| **SVM (RBF Kernel)** | Binary search in multi-dimensional space | Finds curved optimal boundary |

---

## Python → .NET Cheat Sheet

| You know in .NET | It's called in Python |
|---|---|
| `Program.cs` | `app.py` |
| `appsettings.json` | `config.py` |
| `AppDbContext` | `database.py` (SQLAlchemy) |
| `public class Student` | `class Student(Base)` in `models.py` |
| `db.SaveChanges()` | `db.commit()` |
| `db.Students.ToList()` | `db.query(Student).all()` |
| `[HttpGet]` / `[HttpPost]` | `@app.route("/", methods=["GET"])` |
| `return View(model)` | `return render_template("page.html", data=data)` |
| `@Model.Name` (Razor) | `{{ student.name }}` (Jinja2) |
| `@foreach(var s in list)` | `{% for s in students %}` |
| `TempData["msg"]` | `flash("message")` |
| `return RedirectToAction()` | `return redirect(url_for("index"))` |
| `return Json(data)` | `return jsonify(data)` |
| `NuGet install` | `pip install` |
| `.csproj` | `requirements.txt` |
| `dotnet run` | `python app.py` |

---

## Project File Structure

```
student_prediction/
│
├── app.py              ← Program.cs (entry point, starts the server)
├── config.py           ← appsettings.json (all settings)
├── database.py         ← AppDbContext.cs (DB connection + session)
├── models.py           ← Student.cs (entity/model class)
├── routes.py           ← StudentController.cs (all URL handlers)
├── ml_engine.py        ← MLPredictionService.cs (3 ML algorithms)
├── generate_data.py    ← DatabaseSeeder.cs (creates training CSV)
│
├── requirements.txt    ← .csproj (package dependencies)
├── RUN_ME_FIRST.bat    ← One-click setup and run (Windows)
│
├── student_data.csv    ← Training data (created by generate_data.py)
├── trained_models.pkl  ← Saved ML models (created on first run)
├── students.db         ← SQLite database (created automatically)
│
└── templates/          ← Views/ folder
    ├── base.html       ← _Layout.cshtml (shared layout)
    ├── index.html      ← Index.cshtml (dashboard)
    ├── add_student.html ← Create.cshtml (add form)
    ├── result.html     ← Detail.cshtml (prediction result)
    └── edit_student.html ← Edit.cshtml (edit form)
```

---

## How to Run (Step by Step)

### Option A — Double Click (Easiest)
1. Double-click **`RUN_ME_FIRST.bat`**
2. Wait for setup to complete (~30 seconds)
3. Open browser → `http://localhost:5000`

### Option B — Visual Studio Code Terminal
```bash
# Step 1: Install packages (only once — like dotnet restore)
pip install -r requirements.txt

# Step 2: Generate training data (only once)
python generate_data.py

# Step 3: Run the app (like dotnet run)
python app.py
```

### Option C — Visual Studio (with Python extension)
1. Open the `student_prediction` folder in Visual Studio
2. Open `app.py`
3. Press **F5** or click Run

---

## Pages / URLs

| URL | What it does | .NET equivalent |
|---|---|---|
| `http://localhost:5000/` | Dashboard — all students | `GET /Student/Index` |
| `http://localhost:5000/student/add` | Add new student form | `GET /Student/Create` |
| `http://localhost:5000/student/1` | View result for student ID 1 | `GET /Student/Detail/1` |
| `http://localhost:5000/student/edit/1` | Edit student | `GET /Student/Edit/1` |
| `http://localhost:5000/student/delete/1` | Delete student | `POST /Student/Delete/1` |
| `http://localhost:5000/api/students` | JSON API (bonus) | `GET /api/students` |

---

## Requirements
- Python 3.10 or higher
- Internet connection (for first-time package install)

---

## Viva Talking Points

**Q: Why 3 algorithms?**
A: Each algorithm approaches the problem differently. Random Forest votes across 200 trees for robustness. Gradient Boosting iteratively self-corrects for higher accuracy. SVM finds an optimal curved boundary between Pass and Fail students.

**Q: Why use cross-validation?**
A: Cross-validation tests the model on 5 different train/test splits and averages the score. This gives a more reliable accuracy than a single test split — like running your unit tests 5 times with different random data.

**Q: What is StandardScaler?**
A: It normalizes all feature values to have mean=0 and std=1. This is critical for SVM and Gradient Boosting — without it, features with large values (like marks 0-100) would dominate over small values (like GPA 0-4.0).

**Q: How is the best model selected?**
A: The model with the highest cross-validation mean score is selected as the recommended model, since CV score is a more reliable indicator of real-world performance than simple train/test accuracy.
