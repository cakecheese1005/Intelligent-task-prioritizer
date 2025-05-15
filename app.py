from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import joblib
from task_logic import extract_features, dependencies_met

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
db = SQLAlchemy(app)

# Load model
try:
    model = joblib.load('task_priority_model.pkl')
    features = joblib.load('model_features.pkl')
except Exception as e:
    print(f"Model loading failed: {e}")
    model = None
    features = []

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    deadline = db.Column(db.String(10))
    urgency_score = db.Column(db.Integer)
    normalized_urgency = db.Column(db.Float)
    status = db.Column(db.String(20), default='Pending')
    dependencies = db.Column(db.PickleType)

@app.route('/')
def home():
    return "Flask server is running!"

@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([
        {
            'id': task.id,
            'name': task.name,
            'deadline': task.deadline,
            'urgency_score': task.urgency_score,
            'normalized_urgency': task.normalized_urgency,
            'status': task.status,
            'dependencies': task.dependencies or []
        } for task in tasks
    ])

@app.route('/tasks', methods=['POST'])
def create_task():
    data = request.json
    if not all(key in data for key in ['name', 'deadline', 'urgency_score', 'normalized_urgency']):
        return jsonify({"error": "Missing required fields"}), 400

    task = Task(
        name=data['name'],
        deadline=data['deadline'],
        urgency_score=data['urgency_score'],
        normalized_urgency=data['normalized_urgency'],
        status=data.get('status', 'Pending'),
        dependencies=data.get('dependencies', [])
    )
    db.session.add(task)
    db.session.commit()
    return jsonify({"message": "Task created", "id": task.id}), 201

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    task = Task.query.get_or_404(task_id)
    task.name = data.get('name', task.name)
    task.deadline = data.get('deadline', task.deadline)
    task.urgency_score = data.get('urgency_score', task.urgency_score)
    task.normalized_urgency = data.get('normalized_urgency', task.normalized_urgency)
    task.dependencies = data.get('dependencies', task.dependencies or [])
    # Do not manually override status here
    db.session.commit()
    return jsonify({"message": "Task updated"})

@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"})

@app.route('/tasks/prioritize', methods=['POST'])
def prioritize_tasks():
    if model is None:
        return jsonify({"error": "ML model not loaded"}), 500

    tasks = Task.query.all()
    completed_ids = request.json.get('completed_ids', [])
    current_time = datetime.now()

    prioritized_tasks = []
    for task in tasks:
        task_data = {
            'id': task.id,
            'name': task.name,
            'deadline': task.deadline,
            'urgency_score': task.urgency_score,
            'normalized_urgency': task.normalized_urgency,
            'dependencies': task.dependencies if isinstance(task.dependencies, list) else [],
            'status': task.status,
        }

        try:
            feature_values = extract_features(task_data, current_time)
            task_data['score'] = float(model.predict([feature_values])[0])  # Ensure it's a native float
            task_data['status'] = 'Ready' if dependencies_met(task_data, completed_ids) else 'Blocked'
        except Exception as e:
            task_data['error'] = str(e)

        prioritized_tasks.append(task_data)

    # Optionally, you could also update the DB with new statuses here if needed.

    return jsonify(sorted(prioritized_tasks, key=lambda x: x.get('score', 0), reverse=True))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
