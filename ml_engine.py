# ml_engine.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
import pickle
import os
from config import Config
import warnings
warnings.filterwarnings('ignore')

def prepare_features(df):
    """Prepare features for ML models"""
    # Basic features
    features = [
        'attendance', 'math_marks', 'science_marks', 'english_marks',
        'hours_studied', 'assignments', 'prev_gpa'
    ]
    
    # Add derived features
    df['avg_marks'] = (df['math_marks'] + df['science_marks'] + df['english_marks']) / 3
    df['total_marks'] = df['math_marks'] + df['science_marks'] + df['english_marks']
    df['study_efficiency'] = df['avg_marks'] / (df['hours_studied'] + 1)
    df['attendance_score'] = df['attendance'] / 10
    df['assignment_score'] = df['assignments'] / 10
    
    features.extend(['avg_marks', 'total_marks', 'study_efficiency', 'attendance_score', 'assignment_score'])
    
    # Target variable (final grade)
    if 'final_grade' not in df.columns:
        # Calculate final grade if not present
        df['final_grade'] = (
            df['avg_marks'] * 0.40 +
            df['attendance'] * 0.20 +
            df['hours_studied'] * 2 +
            df['assignments'] * 0.15 +
            df['prev_gpa'] * 10
        ) / 1.5
        df['final_grade'] = df['final_grade'].clip(0, 100)
    
    X = df[features].fillna(0)
    y = df['final_grade']
    
    return X, y, features

def create_sample_data():
    """Create sample training data if none exists"""
    print("\n[ML ENGINE] Creating sample training data...")
    np.random.seed(42)
    n_samples = 1000
    
    # Generate realistic student data
    data = {
        'attendance': np.random.uniform(60, 100, n_samples),
        'math_marks': np.random.normal(70, 15, n_samples).clip(0, 100),
        'science_marks': np.random.normal(70, 15, n_samples).clip(0, 100),
        'english_marks': np.random.normal(70, 15, n_samples).clip(0, 100),
        'hours_studied': np.random.uniform(2, 12, n_samples),
        'assignments': np.random.uniform(50, 100, n_samples),
        'prev_gpa': np.random.uniform(2.0, 4.0, n_samples),
    }
    
    df = pd.DataFrame(data)
    
    # Calculate final grade based on features
    df['avg_marks'] = (df['math_marks'] + df['science_marks'] + df['english_marks']) / 3
    df['final_grade'] = (
        df['avg_marks'] * 0.40 +
        df['attendance'] * 0.25 +
        df['hours_studied'] * 1.5 +
        df['assignments'] * 0.20 +
        df['prev_gpa'] * 8
    ) / 1.3
    df['final_grade'] = df['final_grade'].clip(0, 100)
    
    # Add some noise to make it realistic
    df['final_grade'] += np.random.normal(0, 5, n_samples)
    df['final_grade'] = df['final_grade'].clip(0, 100)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(Config.DATA_FILE), exist_ok=True)
    df.to_csv(Config.DATA_FILE, index=False)
    print(f"[ML ENGINE] ✓ Created {n_samples} sample records at {Config.DATA_FILE}")
    return df

def train_models(force_retrain=False):
    """
    Train all ML models and save them
    Returns: dict with trained models and metadata
    """
    print("\n" + "=" * 60)
    print("[ML ENGINE] Starting Model Training")
    print("=" * 60)
    
    # Check if model file exists and load instead of training
    if os.path.exists(Config.MODEL_FILE) and not force_retrain:
        print(f"[ML ENGINE] Model file exists at {Config.MODEL_FILE}")
        models = load_models()
        if models:
            print("[ML ENGINE] ✓ Using existing models")
            return models
    
    # Check if data file exists
    if not os.path.exists(Config.DATA_FILE):
        print(f"[ML ENGINE] ⚠️ Data file not found at {Config.DATA_FILE}")
        df = create_sample_data()
    else:
        print(f"[ML ENGINE] Loading data from {Config.DATA_FILE}")
        df = pd.read_csv(Config.DATA_FILE)
    
    print(f"[ML ENGINE] Loaded {len(df)} student records")
    
    try:
        # Prepare features
        X, y, feature_names = prepare_features(df)
        print(f"[ML ENGINE] Using {len(feature_names)} features: {', '.join(feature_names[:5])}...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        print(f"[ML ENGINE] Training set: {len(X_train)} samples")
        print(f"[ML ENGINE] Test set: {len(X_test)} samples")
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        models = {}
        
        # 1. Random Forest
        print("\n[ML ENGINE] Training Random Forest...")
        rf = RandomForestRegressor(
            n_estimators=100, 
            max_depth=10,
            random_state=42, 
            n_jobs=-1
        )
        rf.fit(X_train_scaled, y_train)
        rf_pred = rf.predict(X_test_scaled)
        rf_mae = mean_absolute_error(y_test, rf_pred)
        rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
        rf_r2 = r2_score(y_test, rf_pred)
        
        models['Random Forest'] = {
            'model': rf,
            'scaler': scaler,
            'feature_names': feature_names,
            'accuracy': rf_r2 * 100,
            'mae': rf_mae,
            'rmse': rf_rmse
        }
        print(f"  ✓ Random Forest - R²: {rf_r2:.3f}, MAE: {rf_mae:.2f}, RMSE: {rf_rmse:.2f}")
        
        # 2. Gradient Boosting
        print("\n[ML ENGINE] Training Gradient Boosting...")
        gb = GradientBoostingRegressor(
            n_estimators=100, 
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        gb.fit(X_train_scaled, y_train)
        gb_pred = gb.predict(X_test_scaled)
        gb_mae = mean_absolute_error(y_test, gb_pred)
        gb_rmse = np.sqrt(mean_squared_error(y_test, gb_pred))
        gb_r2 = r2_score(y_test, gb_pred)
        
        models['Gradient Boosting'] = {
            'model': gb,
            'scaler': scaler,
            'feature_names': feature_names,
            'accuracy': gb_r2 * 100,
            'mae': gb_mae,
            'rmse': gb_rmse
        }
        print(f"  ✓ Gradient Boosting - R²: {gb_r2:.3f}, MAE: {gb_mae:.2f}, RMSE: {gb_rmse:.2f}")
        
        # 3. SVM
        print("\n[ML ENGINE] Training SVM...")
        svm = SVR(kernel='rbf', C=100, gamma='auto', epsilon=0.1)
        svm.fit(X_train_scaled, y_train)
        svm_pred = svm.predict(X_test_scaled)
        svm_mae = mean_absolute_error(y_test, svm_pred)
        svm_rmse = np.sqrt(mean_squared_error(y_test, svm_pred))
        svm_r2 = r2_score(y_test, svm_pred)
        
        models['SVM'] = {
            'model': svm,
            'scaler': scaler,
            'feature_names': feature_names,
            'accuracy': svm_r2 * 100,
            'mae': svm_mae,
            'rmse': svm_rmse
        }
        print(f"  ✓ SVM - R²: {svm_r2:.3f}, MAE: {svm_mae:.2f}, RMSE: {svm_rmse:.2f}")
        
        # Determine best model
        best_model_name = max(models.keys(), key=lambda x: models[x]['accuracy'])
        models['best_model_selected'] = best_model_name
        models['best_accuracy'] = models[best_model_name]['accuracy']
        
        print("\n" + "=" * 60)
        print(f"[ML ENGINE] ✓ Training Complete!")
        print(f"[ML ENGINE] Best Model: {best_model_name}")
        print(f"[ML ENGINE] Accuracy (R²): {models[best_model_name]['accuracy']:.1f}%")
        print(f"[ML ENGINE] MAE: {models[best_model_name]['mae']:.2f} points")
        print("=" * 60)
        
        # Save models
        save_models(models, Config.MODEL_FILE)
        
        return models
        
    except Exception as e:
        print(f"\n[ML ENGINE] ✗ Error training models: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def load_models():
    """Load trained models from file"""
    try:
        if not os.path.exists(Config.MODEL_FILE):
            print(f"[ML ENGINE] Model file not found at {Config.MODEL_FILE}")
            return None
        
        print(f"[ML ENGINE] Loading models from {Config.MODEL_FILE}")
        with open(Config.MODEL_FILE, 'rb') as f:
            models = pickle.load(f)
        
        # Validate models structure
        required_keys = ['Random Forest', 'Gradient Boosting', 'SVM']
        if not all(key in models for key in required_keys):
            print("[ML ENGINE] ✗ Model file is corrupted or incomplete")
            return None
        
        # Verify each model has required components
        for key in required_keys:
            if not all(k in models[key] for k in ['model', 'scaler', 'feature_names']):
                print(f"[ML ENGINE] ✗ Model {key} is missing required components")
                return None
        
        print(f"[ML ENGINE] ✓ Models loaded successfully")
        if 'best_model_selected' in models:
            print(f"[ML ENGINE] Best Model: {models['best_model_selected']} (Accuracy: {models.get('best_accuracy', 0):.1f}%)")
        
        return models
        
    except Exception as e:
        print(f"[ML ENGINE] ✗ Error loading models: {str(e)}")
        return None

def save_models(models, model_file):
    """Save trained models to file"""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(model_file), exist_ok=True)
        
        with open(model_file, 'wb') as f:
            pickle.dump(models, f)
        print(f"[ML ENGINE] ✓ Models saved to {model_file}")
        return True
    except Exception as e:
        print(f"[ML ENGINE] ✗ Error saving models: {str(e)}")
        return False

def predict_student(models, student_data):
    """
    Predict student performance using all models
    
    Args:
        models: Dictionary containing trained models
        student_data: Dict with features
    
    Returns:
        Dictionary with predictions from all models
    """
    # Check if models are available and valid
    if not models or len(models) == 0:
        print("[ML ENGINE] ⚠️ No models available, using default predictions")
        return {
            "Random Forest": {"result": 65.0, "confidence": 70.0},
            "Gradient Boosting": {"result": 65.0, "confidence": 70.0},
            "SVM": {"result": 65.0, "confidence": 70.0},
            "best_model": "Default (No ML Models)"
        }
    
    try:
        # Prepare feature vector
        avg_marks = (student_data['math_marks'] + student_data['science_marks'] + 
                    student_data['english_marks']) / 3
        total_marks = student_data['math_marks'] + student_data['science_marks'] + student_data['english_marks']
        study_efficiency = avg_marks / (student_data['hours_studied'] + 1)
        attendance_score = student_data['attendance'] / 10
        assignment_score = student_data['assignments'] / 10
        
        # Create features array (must match order from training)
        features = [
            student_data['attendance'],
            student_data['math_marks'],
            student_data['science_marks'],
            student_data['english_marks'],
            student_data['hours_studied'],
            student_data['assignments'],
            student_data['prev_gpa'],
            avg_marks,
            total_marks,
            study_efficiency,
            attendance_score,
            assignment_score
        ]
        
        predictions = {}
        best_confidence = 0
        best_model_name = None
        
        for model_name, model_info in models.items():
            # Skip metadata keys
            if model_name in ['best_model_selected', 'best_accuracy']:
                continue
                
            try:
                model = model_info['model']
                scaler = model_info['scaler']
                feature_names = model_info['feature_names']
                
                # Use only the features the model expects
                features_subset = features[:len(feature_names)]
                features_array = np.array(features_subset).reshape(1, -1)
                features_scaled = scaler.transform(features_array)
                
                # Predict
                prediction = model.predict(features_scaled)[0]
                prediction = np.clip(prediction, 0, 100)
                
                # Calculate confidence based on model accuracy
                accuracy = model_info.get('accuracy', 75.0)
                confidence = min(95, max(50, accuracy))
                
                predictions[model_name] = {
                    "result": round(prediction, 1),
                    "confidence": round(confidence, 1)
                }
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_model_name = model_name
                    
            except Exception as e:
                print(f"[ML ENGINE] Error predicting with {model_name}: {str(e)}")
                predictions[model_name] = {
                    "result": 65.0,
                    "confidence": 70.0
                }
        
        # Ensure we have predictions for all models
        for model_name in ['Random Forest', 'Gradient Boosting', 'SVM']:
            if model_name not in predictions:
                predictions[model_name] = {"result": 65.0, "confidence": 70.0}
        
        if not best_model_name:
            best_model_name = "Random Forest"
        
        predictions["best_model"] = best_model_name
        return predictions
        
    except Exception as e:
        print(f"[ML ENGINE] ✗ Prediction error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return default predictions
        return {
            "Random Forest": {"result": 65.0, "confidence": 70.0},
            "Gradient Boosting": {"result": 65.0, "confidence": 70.0},
            "SVM": {"result": 65.0, "confidence": 70.0},
            "best_model": "Default (Error Fallback)"
        }

# Function to check model status
def check_models_status():
    """Check if models are loaded and return status"""
    if os.path.exists(Config.MODEL_FILE):
        try:
            with open(Config.MODEL_FILE, 'rb') as f:
                models = pickle.load(f)
            if models and 'best_model_selected' in models:
                return True, models['best_model_selected'], models.get('best_accuracy', 0)
        except:
            pass
    return False, None, 0