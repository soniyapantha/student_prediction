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



## Requirements
- Python 3.10 or higher
- Internet connection (for first-time package install)

---

