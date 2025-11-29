// Simple in-memory “session” state for the current page
const app = {
    tasks: [],
    nextId: 1,
    currentStrategy: 'smart_balance',
    // Updated to use Render backend base URL
    apiBaseUrl: 'https://smart-task-analyzer-14.onrender.com/api/v1'
};

const strategyDescriptions = {
    smart_balance: 'Balances urgency, importance, effort, and dependencies for optimal task selection.',
    fastest_wins: 'Prioritizes low-effort tasks to maximize quick wins and momentum.',
    high_impact: 'Focuses on tasks with highest importance ratings regardless of other factors.',
    deadline_driven: 'Heavily weights tasks approaching their due dates to avoid missed deadlines.'
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    setDefaultDate();
});

/**
 * Set up all event listeners
 */
function initializeEventListeners() {
    document.getElementById('task-form').addEventListener('submit', handleTaskSubmit);
    document.getElementById('import-json-btn').addEventListener('click', handleJsonImport);
    document.getElementById('analyze-btn').addEventListener('click', handleAnalyze);
    document.getElementById('clear-btn').addEventListener('click', handleClearAll);
    document.getElementById('strategy-select').addEventListener('change', handleStrategyChange);
}

/**
 * Set default due date to tomorrow
 */
function setDefaultDate() {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const dateString = tomorrow.toISOString().split('T')[0];
    document.getElementById('task-due-date').value = dateString;
}

/**
 * Handle individual task form submission
 */
function handleTaskSubmit(event) {
    event.preventDefault();
    
    const title = document.getElementById('task-title').value.trim();
    const dueDate = document.getElementById('task-due-date').value;
    const estimatedHours = parseFloat(document.getElementById('task-hours').value);
    const importance = parseInt(document.getElementById('task-importance').value);
    const dependenciesStr = document.getElementById('task-dependencies').value.trim();
    
    let dependencies = [];
    if (dependenciesStr) {
        dependencies = dependenciesStr
            .split(',')
            .map(id => parseInt(id.trim()))
            .filter(id => !isNaN(id));
    }
    
    if (!title) return showError('Please enter a task title');
    if (!dueDate) return showError('Please select a due date');
    if (estimatedHours <= 0) return showError('Estimated hours must be greater than 0');
    if (importance < 1 || importance > 10) return showError('Importance must be between 1 and 10');
    
    const task = {
        id: app.nextId++,
        title,
        due_date: dueDate,
        estimated_hours: estimatedHours,
        importance,
        dependencies
    };
    
    app.tasks.push(task);
    updateTaskList();
    document.getElementById('task-form').reset();
    setDefaultDate();
    showSuccess(`Task "${title}" added successfully!`);
}

/**
 * Handle JSON bulk import
 */
function handleJsonImport() {
    const jsonInput = document.getElementById('json-input').value.trim();
    if (!jsonInput) return showError('Please paste JSON task data');
    
    try {
        const importedTasks = JSON.parse(jsonInput);
        if (!Array.isArray(importedTasks)) throw new Error('JSON must be an array of tasks');
        
        for (const task of importedTasks) {
            if (!task.title) throw new Error('Each task must have a title');
            if (!task.id) task.id = app.nextId++;
            if (!task.due_date) task.due_date = new Date().toISOString().split('T')[0];
            if (!task.estimated_hours) task.estimated_hours = 2;
            if (!task.importance) task.importance = 5;
            if (!task.dependencies) task.dependencies = [];
        }
        
        app.tasks = app.tasks.concat(importedTasks);
        const maxId = Math.max(...app.tasks.map(t => t.id || 0));
        app.nextId = maxId + 1;
        updateTaskList();
        document.getElementById('json-input').value = '';
        
        showSuccess(`Imported ${importedTasks.length} task(s) successfully!`);
    } catch (error) {
        showError(`JSON Import Error: ${error.message}`);
    }
}

/**
 * Update task list display
 */
function updateTaskList() {
    const taskListContainer = document.getElementById('task-list');
    const taskCountSpan = document.getElementById('task-count');
    const currentTasksSection = document.getElementById('current-tasks-section');
    
    taskCountSpan.textContent = app.tasks.length;
    
    if (app.tasks.length === 0) {
        currentTasksSection.style.display = 'none';
        return;
    }
    
    currentTasksSection.style.display = 'block';
    taskListContainer.innerHTML = '';
    
    app.tasks.forEach((task, index) => {
        const taskItem = document.createElement('div');
        taskItem.className = 'task-item';
        
        const info = document.createElement('div');
        info.className = 'task-item-info';
        
        const title = document.createElement('div');
        title.className = 'task-item-title';
        title.textContent = task.title;
        
        const details = document.createElement('div');
        details.className = 'task-item-details';
        details.textContent = `Due: ${task.due_date} | Hours: ${task.estimated_hours} | Importance: ${task.importance}`;
        
        if (task.dependencies.length > 0) {
            details.textContent += ` | Depends on: [${task.dependencies.join(', ')}]`;
        }
        
        info.appendChild(title);
        info.appendChild(details);
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'task-item-remove';
        removeBtn.textContent = 'Remove';
        removeBtn.onclick = () => removeTask(index);
        
        taskItem.appendChild(info);
        taskItem.appendChild(removeBtn);
        taskListContainer.appendChild(taskItem);
    });
}

/**
 * Remove a task
 */
function removeTask(index) {
    const task = app.tasks[index];
    app.tasks.splice(index, 1);
    updateTaskList();
    showSuccess(`Task "${task.title}" removed`);
}

/**
 * Clear all tasks
 */
function handleClearAll() {
    if (app.tasks.length === 0) return;
    if (!confirm('Are you sure you want to clear all tasks?')) return;
    
    app.tasks = [];
    app.nextId = 1;
    updateTaskList();
    hideResults();
    showSuccess('All tasks cleared');
}

/**
 * Handle strategy change
 */
function handleStrategyChange(event) {
    app.currentStrategy = event.target.value;
    document.getElementById('strategy-description').textContent =
        strategyDescriptions[app.currentStrategy];
    
    if (app.tasks.length > 0 &&
        document.getElementById('output-section').style.display !== 'none') {
        handleAnalyze();
    }
}

/**
 * Analyze tasks (POST to backend)
 */
async function handleAnalyze() {
    if (app.tasks.length === 0) return showError('Please add at least one task');
    
    showLoading();
    hideMessages();
    hideResults();
    
    try {
        const response = await fetch(`${app.apiBaseUrl}/tasks/analyze/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tasks: app.tasks, strategy: app.currentStrategy })
        });
        
        const data = await response.json();
        hideLoading();
        
        if (!response.ok) throw new Error(data.error || 'Analysis failed');
        
        displayResults(data);
        await getSuggestions(data.sorted_tasks);
    } catch (error) {
        hideLoading();
        showError(`Analysis Error: ${error.message}`);
    }
}

/**
 * Request suggestions
 */
async function getSuggestions(sortedTasks) {
    try {
        const response = await fetch(`${app.apiBaseUrl}/tasks/suggest/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tasks: sortedTasks || app.tasks,
                strategy: app.currentStrategy
            })
        });
        
        const data = await response.json();
        if (response.ok) displaySuggestions(data.suggestions);
    } catch (error) {
        console.error('Error fetching suggestions:', error);
    }
}

/**
 * Render analysis results
 */
function displayResults(data) {
    const outputSection = document.getElementById('output-section');
    const resultsList = document.getElementById('results-list');
    
    resultsList.innerHTML = '';
    outputSection.style.display = 'block';
    
    data.sorted_tasks.forEach((task, index) => {
        resultsList.appendChild(createResultCard(task, index + 1));
    });
    
    outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Create a result card UI
 */
function createResultCard(task, rank) {
    const card = document.createElement('div');
    card.className = 'result-card';
    
    const header = document.createElement('div');
    header.className = 'result-header';
    
    const title = document.createElement('div');
    title.className = 'result-title';
    title.textContent = `${rank}. ${task.title}`;
    
    const badge = document.createElement('span');
    badge.className = `priority-badge priority-${task.priority_level.toLowerCase()}`;
    badge.textContent = `${task.priority_level} Priority`;
    
    header.appendChild(title);
    header.appendChild(badge);
    card.appendChild(header);
    
    const scores = document.createElement('div');
    scores.className = 'result-scores';
    
    [
        ['Overall', task.priority_score],
        ['Urgency', task.urgency_score],
        ['Importance', task.importance_score],
        ['Effort', task.effort_score],
        ['Dependency', task.dependency_score]
    ].forEach(([label, value]) => {
        const item = document.createElement('div');
        item.className = 'score-item';
        
        const l = document.createElement('div');
        l.className = 'score-label';
        l.textContent = label;
        
        const v = document.createElement('div');
        v.className = 'score-value';
        v.textContent = value.toFixed(1);
        
        item.appendChild(l);
        item.appendChild(v);
        scores.appendChild(item);
    });
    
    card.appendChild(scores);
    
    const explanation = document.createElement('div');
    explanation.className = 'result-explanation';
    explanation.textContent = task.explanation;
    card.appendChild(explanation);
    
    const details = document.createElement('div');
    details.className = 'result-details';
    const detailItems = [
        `📅 Due: ${task.due_date} (${formatDaysUntilDue(task.days_until_due)})`,
        `⏱️ Effort: ${task.estimated_hours} hour(s)`,
        `⭐ Importance: ${task.importance}/10`
    ];
    
    if (task.dependencies && task.dependencies.length)
        detailItems.push(`🔗 Depends on: [${task.dependencies.join(', ')}]`);
    
    detailItems.forEach(item => {
        const d = document.createElement('div');
        d.className = 'result-detail-item';
        d.textContent = item;
        details.appendChild(d);
    });
    
    card.appendChild(details);
    return card;
}

/**
 * Show suggestions
 */
function displaySuggestions(suggestions) {
    const suggestionsList = document.getElementById('suggestions-list');
    suggestionsList.innerHTML = '';
    if (!suggestions?.length) return;
    
    suggestions.forEach(suggestion => {
        suggestionsList.appendChild(createSuggestionCard(suggestion));
    });
}

/**
 * Suggestion card UI
 */
function createSuggestionCard(s) {
    const card = document.createElement('div');
    card.className = 'suggestion-card';
    
    const rank = document.createElement('div');
    rank.className = 'suggestion-rank';
    rank.textContent = `#${s.rank}`;
    
    card.appendChild(rank);
    
    const title = document.createElement('div');
    title.className = 'suggestion-title';
    title.textContent = s.task.title;
    card.appendChild(title);
    
    const score = document.createElement('div');
    score.className = 'suggestion-score';
    score.textContent = `Priority Score: ${s.score.toFixed(1)}`;
    card.appendChild(score);
    
    const explanation = document.createElement('div');
    explanation.className = 'suggestion-explanation';
    explanation.textContent = s.explanation;
    card.appendChild(explanation);
    
    const details = document.createElement('div');
    details.className = 'suggestion-details';
    details.textContent =
        `📅 Due: ${s.task.due_date} | ⏱️ ${s.task.estimated_hours}h | ⭐ ${s.task.importance}/10`;
    
    card.appendChild(details);
    return card;
}

/**
 * Format due date
 */
function formatDaysUntilDue(days) {
    if (days < 0) return `${Math.abs(days)} day(s) overdue`;
    if (days === 0) return 'Due today';
    if (days === 1) return 'Due tomorrow';
    return `${days} days remaining`;
}

/**
 * UI helpers
 */
function showLoading() {
    document.getElementById('loading').style.display = 'block';
}
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}
function showError(message) {
    const e = document.getElementById('error-message');
    e.textContent = message;
    e.style.display = 'block';
    setTimeout(() => e.style.display = 'none', 5000);
    e.scrollIntoView({ behavior: 'smooth' });
}
function showSuccess(message) {
    const s = document.getElementById('success-message');
    s.textContent = message;
    s.style.display = 'block';
    setTimeout(() => s.style.display = 'none', 3000);
}
function hideMessages() {
    document.getElementById('error-message').style.display = 'none';
    document.getElementById('success-message').style.display = 'none';
}
function hideResults() {
    document.getElementById('output-section').style.display = 'none';
}
