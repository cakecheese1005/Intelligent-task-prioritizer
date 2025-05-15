// Task creation form submission
document.getElementById('taskForm').addEventListener('submit', function(e) {
    e.preventDefault();

    const taskData = {
        name: document.getElementById('name').value,
        deadline: document.getElementById('deadline').value,
        urgency_score: parseInt(document.getElementById('urgency').value),
        normalized_urgency: parseFloat(document.getElementById('normalized_urgency').value),
        dependencies: document.getElementById('dependencies').value.split(',').map(id => parseInt(id.trim()))
    };

    fetch('http://127.0.0.1:5000/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            Swal.fire({
                title: 'Task Added!',
                text: 'Your task was added successfully.',
                icon: 'success',
                confirmButtonText: 'Cool'
            });
            document.getElementById('taskForm').reset();  // Clear the form
        }
    })
    .catch(error => {
        Swal.fire({
            title: 'Error!',
            text: 'Something went wrong.',
            icon: 'error',
            confirmButtonText: 'Try Again'
        });
        console.error('Error:', error);
    });
});

// Prioritize tasks button click
function prioritizeTasks() {
    fetch('http://127.0.0.1:5000/tasks/prioritize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ completed_ids: [] })
    })
    .then(response => response.json())
    .then(data => {
        const taskList = document.getElementById('taskList');
        taskList.innerHTML = '';  // Clear the existing list
        data.forEach(task => {
            const taskItem = document.createElement('div');
            taskItem.classList.add('task-card');
            taskItem.innerHTML = `
                <h4>${task.name}</h4>
                <p>Priority Score: ${task.score}</p>
                <p>Status: ${task.status}</p>
            `;
            taskList.appendChild(taskItem);
        });
    })
    .catch(error => console.error('Error:', error));
}
