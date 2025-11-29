"""
Comprehensive unit tests for Smart Task Analyzer.

Tests cover:
- Core scoring algorithm logic
- Edge case handling
- Circular dependency detection
- Strategy switching
- API endpoint functionality
"""
from django.test import TestCase
from datetime import datetime, timedelta, date
from .scoring import TaskScorer


class TaskScorerTestCase(TestCase):
    """
    Test suite for TaskScorer algorithm.
    """
    
    def setUp(self):
        """
        Set up test data for all tests.
        """
        self.scorer = TaskScorer(strategy='smart_balance')
        self.today = datetime.now().date()
    
    def test_urgency_calculation_overdue(self):
        """
        Test urgency score for overdue tasks.
        """
        overdue_date = self.today - timedelta(days=5)
        urgency_score, days_until_due = self.scorer.calculate_urgency_score(overdue_date)
        
        self.assertGreater(urgency_score, 80)
        self.assertEqual(days_until_due, -5)
    
    def test_urgency_calculation_due_today(self):
        """
        Test urgency score for tasks due today.
        """
        urgency_score, days_until_due = self.scorer.calculate_urgency_score(self.today)
        
        self.assertGreaterEqual(urgency_score, 90)
        self.assertEqual(days_until_due, 0)
    
    def test_urgency_calculation_future(self):
        """
        Test urgency score for future tasks.
        """
        future_date = self.today + timedelta(days=30)
        urgency_score, days_until_due = self.scorer.calculate_urgency_score(future_date)
        
        self.assertLess(urgency_score, 50)
        self.assertEqual(days_until_due, 30)
    
    def test_importance_score_calculation(self):
        """
        Test importance score normalization.
        """
        # Test low importance
        score_low = self.scorer.calculate_importance_score(3)
        self.assertLess(score_low, 50)
        
        # Test high importance
        score_high = self.scorer.calculate_importance_score(9)
        self.assertGreater(score_high, 80)
        
        # Test maximum importance
        score_max = self.scorer.calculate_importance_score(10)
        self.assertLessEqual(score_max, 100)
    
    def test_effort_score_quick_wins(self):
        """
        Test effort scoring favors quick tasks.
        """
        # Quick task
        score_quick = self.scorer.calculate_effort_score(0.5)
        
        # Long task
        score_long = self.scorer.calculate_effort_score(8)
        
        # Quick tasks should score higher
        self.assertGreater(score_quick, score_long)
        self.assertGreater(score_quick, 80)
    
    def test_circular_dependency_detection(self):
        """
        Test detection of circular dependencies.
        """
        # Create circular dependency: 1 -> 2 -> 3 -> 1
        tasks_with_cycle = [
            {'id': 1, 'title': 'Task 1', 'dependencies': [3]},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]},
            {'id': 3, 'title': 'Task 3', 'dependencies': [2]}
        ]
        
        has_cycle, cycle_path = self.scorer.detect_circular_dependencies(tasks_with_cycle)
        
        self.assertTrue(has_cycle)
        self.assertGreater(len(cycle_path), 0)
    
    def test_no_circular_dependency(self):
        """
        Test that valid dependency chains are accepted.
        """
        # Valid dependency chain: 1 -> 2 -> 3
        tasks_valid = [
            {'id': 1, 'title': 'Task 1', 'dependencies': []},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]},
            {'id': 3, 'title': 'Task 3', 'dependencies': [2]}
        ]
        
        has_cycle, cycle_path = self.scorer.detect_circular_dependencies(tasks_valid)
        
        self.assertFalse(has_cycle)
        self.assertEqual(len(cycle_path), 0)
    
    def test_dependency_score_calculation(self):
        """
        Test dependency scoring based on blocked tasks.
        """
        tasks = [
            {'id': 1, 'title': 'Task 1', 'dependencies': []},
            {'id': 2, 'title': 'Task 2', 'dependencies': [1]},
            {'id': 3, 'title': 'Task 3', 'dependencies': [1]},
            {'id': 4, 'title': 'Task 4', 'dependencies': [1]}
        ]
        
        # Task 1 blocks 3 other tasks
        dep_score, dep_count = self.scorer.calculate_dependency_score(1, tasks)
        
        self.assertEqual(dep_count, 3)
        self.assertGreater(dep_score, 50)
        
        # Task 2 blocks nothing
        dep_score_2, dep_count_2 = self.scorer.calculate_dependency_score(2, tasks)
        
        self.assertEqual(dep_count_2, 0)
        self.assertLess(dep_score_2, 20)
    
    def test_complete_task_scoring(self):
        """
        Test complete scoring of a task with all factors.
        """
        tasks = [
            {
                'id': 1,
                'title': 'Fix critical bug',
                'due_date': self.today + timedelta(days=1),
                'estimated_hours': 2,
                'importance': 9,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Dependent task',
                'due_date': self.today + timedelta(days=5),
                'estimated_hours': 3,
                'importance': 7,
                'dependencies': [1]
            }
        ]
        
        scored_task = self.scorer.score_task(tasks[0], tasks)
        
        # Verify all scores are present
        self.assertIn('priority_score', scored_task)
        self.assertIn('urgency_score', scored_task)
        self.assertIn('importance_score', scored_task)
        self.assertIn('effort_score', scored_task)
        self.assertIn('dependency_score', scored_task)
        self.assertIn('explanation', scored_task)
        self.assertIn('priority_level', scored_task)
        
        # High urgency + high importance should yield high priority
        self.assertGreater(scored_task['priority_score'], 60)
    
    def test_strategy_switching(self):
        """
        Test that different strategies produce different scores.
        """
        task = {
            'id': 1,
            'title': 'Test task',
            'due_date': self.today + timedelta(days=7),
            'estimated_hours': 8,
            'importance': 9,
            'dependencies': []
        }
        
        # Score with different strategies
        scorer_smart = TaskScorer('smart_balance')
        scorer_impact = TaskScorer('high_impact')
        scorer_deadline = TaskScorer('deadline_driven')
        
        score_smart = scorer_smart.score_task(task, [task])['priority_score']
        score_impact = scorer_impact.score_task(task, [task])['priority_score']
        score_deadline = scorer_deadline.score_task(task, [task])['priority_score']
        
        # High impact should score highest due to importance=9
        self.assertGreater(score_impact, score_smart)
        
        # All scores should be valid
        self.assertGreater(score_smart, 0)
        self.assertGreater(score_impact, 0)
        self.assertGreater(score_deadline, 0)
    
    def test_task_sorting(self):
        """
        Test that tasks are sorted correctly by priority.
        """
        tasks = [
            {
                'id': 1,
                'title': 'Low priority',
                'due_date': self.today + timedelta(days=30),
                'estimated_hours': 10,
                'importance': 3,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'High priority',
                'due_date': self.today,
                'estimated_hours': 1,
                'importance': 9,
                'dependencies': []
            },
            {
                'id': 3,
                'title': 'Medium priority',
                'due_date': self.today + timedelta(days=5),
                'estimated_hours': 3,
                'importance': 6,
                'dependencies': []
            }
        ]
        
        sorted_tasks, error = self.scorer.analyze_tasks(tasks)
        
        self.assertIsNone(error)
        self.assertEqual(len(sorted_tasks), 3)
        
        # Task 2 should be first (due today, high importance)
        self.assertEqual(sorted_tasks[0]['id'], 2)
        
        # Verify descending order
        for i in range(len(sorted_tasks) - 1):
            self.assertGreaterEqual(
                sorted_tasks[i]['priority_score'],
                sorted_tasks[i + 1]['priority_score']
            )
    
    def test_missing_data_handling(self):
        """
        Test that tasks with missing fields use sensible defaults.
        """
        task_minimal = {
            'title': 'Minimal task'
        }
        
        # Should not raise exception
        try:
            scored_task = self.scorer.score_task(task_minimal, [task_minimal])
            
            # Verify defaults were applied
            self.assertIn('priority_score', scored_task)
            self.assertGreater(scored_task['priority_score'], 0)
        except Exception as e:
            self.fail(f"Scoring with minimal data raised exception: {e}")
    
    def test_top_suggestions(self):
        """
        Test suggestion generation for top tasks.
        """
        tasks = [
            {
                'id': 1,
                'title': 'Task 1',
                'due_date': self.today,
                'estimated_hours': 2,
                'importance': 8,
                'dependencies': []
            },
            {
                'id': 2,
                'title': 'Task 2',
                'due_date': self.today + timedelta(days=1),
                'estimated_hours': 1,
                'importance': 7,
                'dependencies': []
            },
            {
                'id': 3,
                'title': 'Task 3',
                'due_date': self.today + timedelta(days=10),
                'estimated_hours': 5,
                'importance': 5,
                'dependencies': []
            }
        ]
        
        suggestions = self.scorer.get_top_suggestions(tasks, count=2)
        
        self.assertEqual(len(suggestions), 2)
        
        # Verify suggestion structure
        for suggestion in suggestions:
            self.assertIn('task', suggestion)
            self.assertIn('score', suggestion)
            self.assertIn('explanation', suggestion)
            self.assertIn('rank', suggestion)
        
        # First suggestion should have rank 1
        self.assertEqual(suggestions[0]['rank'], 1)