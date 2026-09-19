# config.py
# ─────────────────────────────────────────────────────────────────────────────
# Like appsettings.json in .NET
# All your app settings live here in one place.
# ─────────────────────────────────────────────────────────────────────────────

class Config:
    # Database — like "ConnectionStrings" in appsettings.json
    DATABASE_URL = "sqlite:///students.db"   # Creates students.db file automatically

    # Secret key — like JWT secret or DataProtection key in .NET
    SECRET_KEY = "bca-student-prediction-secret-2024"

    # Debug mode — like ASPNETCORE_ENVIRONMENT = Development
    DEBUG = True

    # ML model save file — so we don't retrain every restart
    MODEL_FILE = "trained_models.pkl"

    # Training data CSV
    DATA_FILE = "student_data.csv"
