from datetime import datetime
from typing import List, Dict
import joblib

# Load model and features
try:
    model = joblib.load('task_priority_model.pkl')
    features = joblib.load('model_features.pkl')
except Exception as e:
    print(f"Model loading failed: {e}")
    model = None
    features = []

def extract_features(task: Dict, current_time: datetime) -> List[float]:
    try:
        deadline = datetime.strptime(task['deadline'], "%Y-%m-%d")
        days_left = (deadline - current_time).days
    except:
        days_left = 0
    return [
        days_left,
        task.get('urgency_score', 0),
        len(task.get('dependencies', [])),
        task.get('normalized_urgency', 0.0),
        1 if task.get('status', '').lower() == 'overdue' else 0
    ]

def validate_features(features: List[float]) -> bool:
    """Ensure the feature list matches the expected format."""
    return len(features) == len(features) and all(isinstance(x, (int, float)) for x in features)

def predict_task_priority(task: Dict, current_time: datetime) -> float:
    if model is None:
        raise ValueError("Model is not loaded.")
    task_features = extract_features(task, current_time)
    if not validate_features(task_features):
        raise ValueError("Feature mismatch.")
    return float(model.predict([task_features])[0])

def dependencies_met(task: Dict, completed_ids: List[int]) -> bool:
    """Check if all dependencies for a task are met."""
    return all(dep in completed_ids for dep in task.get('dependencies', []))

def prioritize_tasks(task_list: List[Dict], completed_ids: List[int] = []) -> List[Dict]:
    """Prioritize tasks based on urgency and dependencies."""
    current_time = datetime.now()
    for task in task_list:
        try:
            if dependencies_met(task, completed_ids):
                task['score'] = predict_task_priority(task, current_time)
                task['status'] = 'Ready'
            else:
                task['score'] = -1
                task['status'] = 'Blocked'
        except Exception as e:
            task['score'] = -1
            task['error'] = str(e)
    return sorted([t for t in task_list if t['score'] >= 0], key=lambda x: x['score'], reverse=True)
