# app.py
from flask import Flask
from config import Config
from database import init_db
from ml_engine import load_models, train_models
from routes import register_routes
from auth import create_default_users
import os

def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = Config.SECRET_KEY

    # Initialize database
    print("\n[SETUP] Initializing database...")
    init_db()

    # Load or Train ML Models
    print("\n[SETUP] Checking ML models...")
    
    # Try to load existing models
    models = load_models()
    
    # If models is None or empty, train new ones
    if models is None or len(models) == 0:
        print("[SETUP] No valid models found. Training new models...")
        models = train_models(force_retrain=True)
        
        if models is None:
            print("[SETUP] ⚠️ WARNING: Failed to train models.")
            print("[SETUP] The system will use default predictions.")
            models = {}  # Set to empty dict instead of None
    
    # Store models in app config (ensure it's never None)
    app.config["ML_MODELS"] = models if models is not None else {}
    
    if app.config["ML_MODELS"] and len(app.config["ML_MODELS"]) > 0:
        print(f"[SETUP] ✓ ML models ready. Best model: {app.config['ML_MODELS'].get('best_model_selected', 'Unknown')}")
    else:
        print("[SETUP] ⚠️ ML models not available. Add student will still work with default predictions.")

    # Register routes
    register_routes(app)
    print("[SETUP] Routes registered.")
    
    # Create default users
    create_default_users()
    
    return app

if __name__ == "__main__":
    print("=" * 60)
    print("  Student Performance Prediction System")
    print("=" * 60)

    app = create_app()

    print("\n[READY] Open your browser and go to: http://localhost:5000")
    print("        Press Ctrl+C to stop the server.\n")

    app.run(
        debug=Config.DEBUG,
        host="0.0.0.0",
        port=5000
    )