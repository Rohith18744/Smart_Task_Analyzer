"""Priority scoring helpers for tasks."""
import math
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Set, Tuple


class TaskScorer:
    """Score and sort tasks using different weighting strategies."""

    STRATEGIES = {
        'smart_balance': {
            'urgency': 0.35,
            'importance': 0.30,
            'effort': 0.20,
            'dependency': 0.15
        },
        'fastest_wins': {
            'urgency': 0.20,
            'importance': 0.15,
            'effort': 0.50,
            'dependency': 0.15
        },
        'high_impact': {
            'urgency': 0.20,
            'importance': 0.60,
            'effort': 0.10,
            'dependency': 0.10
        },
        'deadline_driven': {
            'urgency': 0.70,
            'importance': 0.20,
            'effort': 0.05,
            'dependency': 0.05
        }
    }

    def __init__(self, strategy: str = 'smart_balance'):
        """
        Initialize scorer with a specific strategy.
        
        Args:
            strategy: One of 'smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'
        """
        self.strategy = strategy
        self.weights = self.STRATEGIES.get(strategy, self.STRATEGIES['smart_balance'])

    def calculate_urgency_score(self, due_date: date) -> Tuple[float, int]:
        """
        Calculate urgency based on days until due date.
        Uses exponential scaling for overdue tasks and sigmoid decay for future tasks.
        
        Args:
            due_date: Task due date
            
        Returns:
            Tuple of (urgency_score, days_until_due)
        """
        today = datetime.now().date()
        days_until_due = (due_date - today).days
        
        if days_until_due < 0:
            # Overdue: linear boost starting high and capping at 100
            overdue_days = abs(days_until_due)
            score = min(100, 80 + overdue_days * 4)
            return score, days_until_due
        
        elif days_until_due == 0:
            # Due today: maximum urgency
            return 95.0, days_until_due
        
        elif days_until_due <= 3:
            # Very soon: high urgency with slight decay
            score = 90 - (days_until_due * 5)
            return score, days_until_due
        
        elif days_until_due <= 7:
            # This week: moderate-high urgency
            score = 70 - ((days_until_due - 3) * 5)
            return score, days_until_due
        
        elif days_until_due <= 14:
            # Next two weeks: moderate urgency
            score = 50 - ((days_until_due - 7) * 2)
            return score, days_until_due
        
        elif days_until_due <= 30:
            # This month: declining urgency
            score = 30 - ((days_until_due - 14) * 1)
            return max(10, score), days_until_due
        
        else:
            # Far future: minimal urgency
            score = max(5, 20 - (days_until_due / 10))
            return score, days_until_due

    def calculate_importance_score(self, importance: int) -> float:
        """
        Convert importance rating to normalized score.
        
        Args:
            importance: User rating (1-10)
            
        Returns:
            Normalized importance score (0-100)
        """
        # Direct mapping with slight non-linear boost for high importance
        base_score = (importance / 10) * 100
        
        # Boost very important tasks slightly
        if importance >= 8:
            base_score = min(100, base_score * 1.1)
        
        return base_score

    def calculate_effort_score(self, estimated_hours: float) -> float:
        """
        Calculate effort score - lower effort gets higher score (quick wins).
        
        Args:
            estimated_hours: Estimated time to complete
            
        Returns:
            Effort score (0-100), higher for lower effort
        """
        # Inverse relationship: quick tasks are valuable
        if estimated_hours <= 0.5:
            return 95.0
        
        if estimated_hours <= 1:
            return 85.0
        
        if estimated_hours <= 2:
            return 75.0
        
        if estimated_hours <= 4:
            return 60.0
        
        if estimated_hours <= 8:
            return 40.0
        
        # Long tasks get lower scores
        score = max(10, 100 - (estimated_hours * 8))
        return score

    def detect_circular_dependencies(
        self, 
        tasks: List[Dict[str, Any]]
    ) -> Tuple[bool, List[int]]:
        """
        Detect circular dependencies using depth-first search.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Tuple of (has_cycle, cycle_path)
        """
        # Build adjacency list
        task_map = {task.get('id', i): task for i, task in enumerate(tasks)}
        graph = {
            task_id: task.get('dependencies', [])
            for task_id, task in task_map.items()
        }
        
        visited = set()
        rec_stack = set()
        cycle_path = []
        
        def dfs(node: int, path: List[int]) -> bool:
            """
            Depth-first search to detect cycles.
            """
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle_path.extend(path[cycle_start:])
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        for task_id in graph:
            if task_id not in visited:
                if dfs(task_id, []):
                    return True, cycle_path
        
        return False, []

    def calculate_dependency_score(
        self, 
        task_id: int, 
        tasks: List[Dict[str, Any]]
    ) -> Tuple[float, int]:
        """
        Calculate dependency score based on how many tasks depend on this one.
        Tasks that block others should be prioritized.
        
        Args:
            task_id: ID of the task to score
            tasks: List of all tasks
            
        Returns:
            Tuple of (dependency_score, dependent_count)
        """
        # Count how many tasks depend on this one
        dependent_count = 0
        
        for task in tasks:
            dependencies = task.get('dependencies', [])
            if task_id in dependencies:
                dependent_count += 1
        
        # Score based on number of dependents
        if dependent_count == 0:
            return 10.0, 0
        elif dependent_count == 1:
            return 40.0, 1
        elif dependent_count == 2:
            return 70.0, 2
        else:
            # Multiple dependencies: high priority
            return min(100, 70 + (dependent_count - 2) * 15), dependent_count

    def score_task(
        self, 
        task: Dict[str, Any], 
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive priority score for a task.
        
        Args:
            task: Task dictionary to score
            tasks: All tasks (for dependency analysis)
            
        Returns:
            Task dictionary with added scoring metadata
        """
        # Extract task data with defaults
        task_id = task.get('id') or hash(task.get('title', ''))
        due_date = task.get('due_date')

        # Normalize due date input
        if isinstance(due_date, str):
            try:
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            except ValueError:
                # Accept ISO strings with time component
                try:
                    due_date = datetime.fromisoformat(due_date).date()
                except ValueError:
                    due_date = None
        elif isinstance(due_date, datetime):
            due_date = due_date.date()
        elif isinstance(due_date, date):
            pass
        else:
            due_date = None

        if due_date is None:
            from datetime import timedelta
            due_date = datetime.now().date() + timedelta(days=7)

        importance = task.get('importance', 5) or 5
        estimated_hours = task.get('estimated_hours', 2.0) or 2.0
        dependencies = task.get('dependencies') or []

        # Calculate individual factor scores
        urgency_score, days_until_due = self.calculate_urgency_score(due_date)
        importance_score = self.calculate_importance_score(importance)
        effort_score = self.calculate_effort_score(estimated_hours)
        dependency_score, dependent_count = self.calculate_dependency_score(
            task_id, tasks
        )
        
        # Calculate weighted total score
        priority_score = (
            self.weights['urgency'] * urgency_score +
            self.weights['importance'] * importance_score +
            self.weights['effort'] * effort_score +
            self.weights['dependency'] * dependency_score
        )
        
        # Generate explanation
        explanation = self._generate_explanation(
            urgency_score, 
            importance_score, 
            effort_score, 
            dependency_score,
            days_until_due,
            dependent_count,
            estimated_hours
        )
        
        # Determine priority level
        if priority_score >= 75:
            priority_level = "High"
        elif priority_score >= 50:
            priority_level = "Medium"
        else:
            priority_level = "Low"
        
        # Return enriched task data
        return {
            **task,
            'id': task_id,
            'priority_score': round(priority_score, 2),
            'urgency_score': round(urgency_score, 2),
            'importance_score': round(importance_score, 2),
            'effort_score': round(effort_score, 2),
            'dependency_score': round(dependency_score, 2),
            'explanation': explanation,
            'priority_level': priority_level,
            'days_until_due': days_until_due,
            'due_date': due_date,
            'estimated_hours': estimated_hours,
            'importance': importance,
            'dependencies': dependencies,
        }

    def _generate_explanation(
        self,
        urgency_score: float,
        importance_score: float,
        effort_score: float,
        dependency_score: float,
        days_until_due: int,
        dependent_count: int,
        estimated_hours: float
    ) -> str:
        """
        Generate human-readable explanation for the score.
        """
        reasons = []
        
        # Urgency reasoning
        if days_until_due < 0:
            reasons.append(f"overdue by {abs(days_until_due)} day(s)")
        elif days_until_due == 0:
            reasons.append("due today")
        elif days_until_due <= 3:
            reasons.append(f"due in {days_until_due} day(s)")
        elif urgency_score > 50:
            reasons.append("approaching deadline")
        
        # Importance reasoning
        if importance_score >= 80:
            reasons.append("high importance rating")
        elif importance_score >= 60:
            reasons.append("moderate importance")
        
        # Effort reasoning
        if estimated_hours <= 1:
            reasons.append("quick win (<1 hour)")
        elif estimated_hours <= 2:
            reasons.append("short task")
        elif estimated_hours >= 8:
            reasons.append("substantial effort required")
        
        # Dependency reasoning
        if dependent_count > 0:
            reasons.append(f"blocks {dependent_count} other task(s)")
        
        if not reasons:
            return "Standard priority task"
        
        return "Priority due to: " + ", ".join(reasons) + "."

    def analyze_tasks(
        self, 
        tasks: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Analyze and sort tasks by priority.
        
        Args:
            tasks: List of task dictionaries
            
        Returns:
            Tuple of (sorted_tasks, error_message)
        """
        if not tasks:
            return [], "No tasks provided"
        
        # Check for circular dependencies
        has_cycle, cycle_path = self.detect_circular_dependencies(tasks)
        if has_cycle:
            return [], f"Circular dependency detected: {' -> '.join(map(str, cycle_path))}"
        
        # Score all tasks
        scored_tasks = [self.score_task(task, tasks) for task in tasks]
        
        # Sort by priority score (descending)
        sorted_tasks = sorted(
            scored_tasks, 
            key=lambda x: x['priority_score'], 
            reverse=True
        )
        
        return sorted_tasks, None

    def get_top_suggestions(
        self, 
        tasks: List[Dict[str, Any]], 
        count: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get top N task suggestions with detailed reasoning.
        
        Args:
            tasks: List of tasks
            count: Number of suggestions to return
            
        Returns:
            List of suggestion dictionaries
        """
        sorted_tasks, error = self.analyze_tasks(tasks)
        
        if error:
            return []
        
        top_tasks = sorted_tasks[:count]
        
        suggestions = []
        for rank, task in enumerate(top_tasks, 1):
            suggestion = {
                'task': task,
                'score': task['priority_score'],
                'explanation': self._generate_detailed_suggestion(task, rank),
                'rank': rank
            }
            suggestions.append(suggestion)
        
        return suggestions

    def _generate_detailed_suggestion(
        self, 
        task: Dict[str, Any], 
        rank: int
    ) -> str:
        """
        Generate detailed suggestion explanation.
        """
        base = f"Suggestion #{rank}: "
        
        if task['days_until_due'] < 0:
            return base + f"This task is overdue and should be addressed immediately. {task['explanation']}"
        
        if task['days_until_due'] == 0:
            return base + f"This task is due today. {task['explanation']}"
        
        if task['priority_score'] >= 75:
            return base + f"High priority task. {task['explanation']}"
        
        return base + f"Recommended based on balanced factors. {task['explanation']}"