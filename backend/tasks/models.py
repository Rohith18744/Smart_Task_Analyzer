from django.db import models
from django.utils import timezone
from .scoring import TaskScorer

class Task(models.Model):
    """
    Represents a unit of work to be analyzed and tracked.
    """
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ]

    title = models.CharField(
        max_length=200,
        help_text="A concise summary of the task."
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed instructions and context."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='TODO'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # This field is computed, not set directly by users.
    complexity_score = models.IntegerField(
        default=0,
        editable=False,
        help_text="Auto-calculated score from 1-100 indicating task difficulty."
    )

    def save(self, *args, **kwargs):
        """
        Override save method to calculate complexity score before persisting.
        Uses TaskScorer to derive a score from the task's data.
        """
        scorer = TaskScorer()
        # Build a minimal task representation for scoring
        task_data = {
            "id": self.id or 0,
            "title": self.title,
            "description": self.description,
            # Fallbacks for required scoring fields
            "due_date": getattr(self, "due_date", None) or timezone.now().date(),
            "importance": getattr(self, "importance", 5),
            "estimated_hours": getattr(self, "estimated_hours", 2.0),
            "dependencies": [],
        }
        scored_task = scorer.score_task(task_data, [task_data])
        self.complexity_score = int(scored_task["priority_score"])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (Score: {self.complexity_score})"