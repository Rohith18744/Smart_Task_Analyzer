// Simple in-memory “session” state for the current page
const app = {
    tasks: [],
    nextId: 1,
    currentStrategy: 'smart_balance',
    // Align with Django router path `path('api/v1/', include('tasks.urls'))`
    apiBaseUrl: '/api/v1'
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
    // Form submission
    document.getElementById('task-form').addEventListener('submit', handleTaskSubmit);
    
    // JSON import
    document.getElementById('import-json-btn').addEventListener('click', handleJsonImport);
    
    // Action buttons
    document.getElementById('analyze-btn').addEventListener('click', handleAnalyze);
    document.getElementById('clear-btn').addEventListener('click', handleClearAll);
    
    // Strategy selector
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
    
    // Get form values
    const title = document.getElementById('task-title').value.trim();
    const dueDate = document.getElementById('task-due-date').value;
    const estimatedHours = parseFloat(document.getElementById('task-hours').value);
    const importance = parseInt(document.getElementById('task-importance').value);
    const dependenciesStr = document.getElementById('task-dependencies').value.trim();
    
    // Parse dependencies
    let dependencies = [];
    if (dependenciesStr) {
        dependencies = dependenciesStr
            .split(',')
            .map(id => parseInt(id.trim()))
            .filter(id => !isNaN(id));
    }
    
    // Validate form data
    if (!title) {
        showError('Please enter a task title');
        return;
    }
    
    if (!dueDate) {
        showError('Please select a due date');
        return;
    }
    
    if (estimatedHours <= 0) {
        showError('Estimated hours must be greater than 0');
        return;
    }
    
    if (importance < 1 || importance > 10) {
        showError('Importance must be between 1 and 10');
        return;
    }
    
    // Create task object
    const task = {
        id: app.nextId++,
        title: title,
        due_date: dueDate,
        estimated_hours: estimatedHours,
        importance: importance,
        dependencies: dependencies
    };
    
    // Add to tasks array
    app.tasks.push(task);
    
    // Update UI
    updateTaskList();
    
    // Reset form
    document.getElementById('task-form').reset();
    setDefaultDate();
    
    // Show success message
    showSuccess(`Task "${title}" added successfully!`);
}

/**
 * Handle JSON bulk import
 */
function handleJsonImport() {
    const jsonInput = document.getElementById('json-input').value.trim();
    
    if (!jsonInput) {
        showError('Please paste JSON task data');
        return;
    }
    
    try {
        const importedTasks = JSON.parse(jsonInput);
        
        // Validate it's an array
        if (!Array.isArray(importedTasks)) {
            throw new Error('JSON must be an array of tasks');
        }
        
        // Validate each task
        for (const task of importedTasks) {
            if (!task.title) {
                throw new Error('Each task must have a title');
            }
            
            // Set defaults if missing
            if (!task.id) {
                task.id = app.nextId++;
            }
            if (!task.due_date) {
                task.due_date = new Date().toISOString().split('T')[0];
            }
            if (!task.estimated_hours) {
                task.estimated_hours = 2;
            }
            if (!task.importance) {
                task.importance = 5;
            }
            if (!task.dependencies) {
                task.dependencies = [];
            }
        }
        
        // Add to tasks
        app.tasks = app.tasks.concat(importedTasks);
        
        // Update next ID
        const maxId = Math.max(...app.tasks.map(t => t.id || 0));
        app.nextId = maxId + 1;
        
        // Update UI
        updateTaskList();
        
        // Clear input
        document.getElementById('json-input').value = '';
        
        // Show success
        showSuccess(`Imported ${importedTasks.length} task(s) successfully!`);
        
    } catch (error) {
        showError(`JSON Import Error: ${error.message}`);
    }
}

/**
 * Update the current tasks display
 */
function updateTaskList() {
    const taskListContainer = document.getElementById('task-list');
    const taskCountSpan = document.getElementById('task-count');
    const currentTasksSection = document.getElementById('current-tasks-section');
    
    // Update count
    taskCountSpan.textContent = app.tasks.length;
    
    // Show/hide section
    if (app.tasks.length === 0) {
        currentTasksSection.style.display = 'none';
        return;
    }
    
    currentTasksSection.style.display = 'block';
    
    // Clear existing list
    taskListContainer.innerHTML = '';
    
    // Render each task
    app.tasks.forEach((task, index) => {
        const taskItem = document.createElement('div');
        taskItem.className = 'task-item';
        
        const taskInfo = document.createElement('div');
        taskInfo.className = 'task-item-info';
        
        const taskTitle = document.createElement('div');
        taskTitle.className = 'task-item-title';
        taskTitle.textContent = task.title;
        
        const taskDetails = document.createElement('div');
        taskDetails.className = 'task-item-details';
        taskDetails.textContent = `Due: ${task.due_date} | Hours: ${task.estimated_hours} | Importance: ${task.importance}/10`;
        
        if (task.dependencies.length > 0) {
            taskDetails.textContent += ` | Depends on: [${task.dependencies.join(', ')}]`;
        }
        
        taskInfo.appendChild(taskTitle);
        taskInfo.appendChild(taskDetails);
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'task-item-remove';
        removeBtn.textContent = 'Remove';
        removeBtn.addEventListener('click', () => removeTask(index));
        
        taskItem.appendChild(taskInfo);
        taskItem.appendChild(removeBtn);
        
        taskListContainer.appendChild(taskItem);
    });
}

/**
 * Remove a task from the list
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
    
    if (confirm('Are you sure you want to clear all tasks?')) {
        app.tasks = [];
        app.nextId = 1;
        updateTaskList();
        hideResults();
        showSuccess('All tasks cleared');
    }
}

/**
 * Handle strategy change
 */
function handleStrategyChange(event) {
    app.currentStrategy = event.target.value;
    const descriptionDiv = document.getElementById('strategy-description');
    descriptionDiv.textContent = strategyDescriptions[app.currentStrategy];
    
    // Re-analyze if results are showing
    if (app.tasks.length > 0 && document.getElementById('output-section').style.display !== 'none') {
        handleAnalyze();
    }
}

/**
 * Analyze tasks via API
 */
async function handleAnalyze() {
    if (app.tasks.length === 0) {
        showError('Please add at least one task to analyze');
        return;
    }
    
    // Show loading
    showLoading();
    hideMessages();
    hideResults();
    
    try {
        // Call analyze API
        const response = await fetch(`${app.apiBaseUrl}/tasks/analyze/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tasks: app.tasks,
                strategy: app.currentStrategy
            })
        });
        
        const data = await response.json();
        
        hideLoading();
        
        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed');
        }
        
        // Display results
        displayResults(data);
        
        // Get suggestions
        await getSuggestions(data.sorted_tasks);
        
    } catch (error) {
        hideLoading();
        showError(`Analysis Error: ${error.message}`);
    }
}

/**
 * Get task suggestions via API
 */
async function getSuggestions(sortedTasks) {
    try {
        const response = await fetch(`${app.apiBaseUrl}/tasks/suggest/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tasks: sortedTasks || app.tasks,
                strategy: app.currentStrategy
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displaySuggestions(data.suggestions);
        }
        
    } catch (error) {
        console.error('Error fetching suggestions:', error);
    }
}

/**
 * Display analysis results
 */
function displayResults(data) {
    const outputSection = document.getElementById('output-section');
    const resultsList = document.getElementById('results-list');
    
    // Clear existing results
    resultsList.innerHTML = '';
    
    // Show output section
    outputSection.style.display = 'block';
    
    // Render each task
    data.sorted_tasks.forEach((task, index) => {
        const card = createResultCard(task, index + 1);
        resultsList.appendChild(card);
    });
    
    // Scroll to results
    outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Create a result card element
 */
function createResultCard(task, rank) {
    const card = document.createElement('div');
    card.className = 'result-card';
    
    // Header
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
    
    // Scores
    const scoresContainer = document.createElement('div');
    scoresContainer.className = 'result-scores';
    
    const scores = [
        { label: 'Overall', value: task.priority_score },
        { label: 'Urgency', value: task.urgency_score },
        { label: 'Importance', value: task.importance_score },
        { label: 'Effort', value: task.effort_score },
        { label: 'Dependency', value: task.dependency_score }
    ];
    
    scores.forEach(score => {
        const scoreItem = document.createElement('div');
        scoreItem.className = 'score-item';
        
        const label = document.createElement('div');
        label.className = 'score-label';
        label.textContent = score.label;
        
        const value = document.createElement('div');
        value.className = 'score-value';
        value.textContent = score.value.toFixed(1);
        
        scoreItem.appendChild(label);
        scoreItem.appendChild(value);
        scoresContainer.appendChild(scoreItem);
    });
    
    card.appendChild(scoresContainer);
    
    // Explanation
    const explanation = document.createElement('div');
    explanation.className = 'result-explanation';
    explanation.textContent = task.explanation;
    card.appendChild(explanation);
    
    // Details
    const details = document.createElement('div');
    details.className = 'result-details';
    
    const detailItems = [
        `📅 Due: ${task.due_date} (${formatDaysUntilDue(task.days_until_due)})`,
        `⏱️ Effort: ${task.estimated_hours} hour(s)`,
        `⭐ Importance: ${task.importance}/10`
    ];
    
    if (task.dependencies && task.dependencies.length > 0) {
        detailItems.push(`🔗 Depends on: [${task.dependencies.join(', ')}]`);
    }
    
    detailItems.forEach(item => {
        const detailItem = document.createElement('div');
        detailItem.className = 'result-detail-item';
        detailItem.textContent = item;
        details.appendChild(detailItem);
    });
    
    card.appendChild(details);
    
    return card;
}

/**
 * Display task suggestions
 */
function displaySuggestions(suggestions) {
    const suggestionsList = document.getElementById('suggestions-list');
    
    // Clear existing
    suggestionsList.innerHTML = '';
    
    if (!suggestions || suggestions.length === 0) {
        return;
    }
    
    // Render each suggestion
    suggestions.forEach(suggestion => {
        const card = createSuggestionCard(suggestion);
        suggestionsList.appendChild(card);
    });
}

/**
 * Create a suggestion card element
 */
function createSuggestionCard(suggestion) {
    const card = document.createElement('div');
    card.className = 'suggestion-card';
    
    // Rank badge
    const rank = document.createElement('div');
    rank.className = 'suggestion-rank';
    rank.textContent = `#${suggestion.rank}`;
    card.appendChild(rank);
    
    // Title
    const title = document.createElement('div');
    title.className = 'suggestion-title';
    title.textContent = suggestion.task.title;
    card.appendChild(title);
    
    // Score
    const score = document.createElement('div');
    score.className = 'suggestion-score';
    score.textContent = `Priority Score: ${suggestion.score.toFixed(1)}`;
    card.appendChild(score);
    
    // Explanation
    const explanation = document.createElement('div');
    explanation.className = 'suggestion-explanation';
    explanation.textContent = suggestion.explanation;
    card.appendChild(explanation);
    
    // Details
    const details = document.createElement('div');
    details.className = 'suggestion-details';
    details.innerHTML = `
        📅 Due: ${suggestion.task.due_date} | 
        ⏱️ ${suggestion.task.estimated_hours}h | 
        ⭐ ${suggestion.task.importance}/10
    `;
    card.appendChild(details);
    
    return card;
}

/**
 * Format days until due in human-readable format
 */
function formatDaysUntilDue(days) {
    if (days < 0) {
        return `${Math.abs(days)} day(s) overdue`;
    } else if (days === 0) {
        return 'Due today';
    } else if (days === 1) {
        return 'Due tomorrow';
    } else {
        return `${days} days remaining`;
    }
}

/**
 * Show loading indicator
 */
function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

/**
 * Show error message
 */
function showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
    
    // Scroll to message
    errorDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

/**
 * Show success message
 */
function showSuccess(message) {
    const successDiv = document.getElementById('success-message');
    successDiv.textContent = message;
    successDiv.style.display = 'block';
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 3000);
}

/**
 * Hide all messages
 */
function hideMessages() {
    document.getElementById('error-message').style.display = 'none';
    document.getElementById('success-message').style.display = 'none';
}

/**
 * Hide results section
 */
function hideResults() {
    document.getElementById('output-section').style.display = 'none';
}