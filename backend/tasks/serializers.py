"""Serializers for validating task input and API payloads."""
from rest_framework import serializers
from datetime import datetime


class TaskSerializer(serializers.Serializer):
    """Validate and normalize a single task payload."""
    id = serializers.IntegerField(required=False)
    title = serializers.CharField(max_length=200)
    due_date = serializers.DateField(
        required=False,
        input_formats=['%Y-%m-%d', 'iso-8601'],
        help_text="Format: YYYY-MM-DD"
    )
    estimated_hours = serializers.FloatField(
        required=False,
        default=2.0,
        min_value=0.1,
        max_value=1000.0
    )
    importance = serializers.IntegerField(
        required=False,
        default=5,
        min_value=1,
        max_value=10
    )
    dependencies = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        allow_empty=True
    )

    def validate_due_date(self, value):
        """
        Validate due date is a valid date.
        """
        if value is None:
            # Default to 7 days from now if not provided
            from datetime import timedelta
            return datetime.now().date() + timedelta(days=7)
        return value

    def validate_importance(self, value):
        """
        Ensure importance is within valid range.
        """
        if value is None:
            return 5
        if value < 1:
            return 1
        if value > 10:
            return 10
        return value

    def validate_estimated_hours(self, value):
        """
        Ensure estimated hours is positive.
        """
        if value is None or value <= 0:
            return 2.0
        return value


class TaskAnalysisRequestSerializer(serializers.Serializer):
    """Request body for analysis/suggestion endpoints."""
    tasks = TaskSerializer(many=True)
    strategy = serializers.ChoiceField(
        choices=[
            'smart_balance',
            'fastest_wins',
            'high_impact',
            'deadline_driven'
        ],
        default='smart_balance',
        required=False
    )


class ScoredTaskSerializer(serializers.Serializer):
    """A scored task with all intermediate factors exposed."""
    id = serializers.IntegerField(required=False)
    title = serializers.CharField()
    due_date = serializers.DateField()
    estimated_hours = serializers.FloatField()
    importance = serializers.IntegerField()
    dependencies = serializers.ListField(child=serializers.IntegerField())
    priority_score = serializers.FloatField()
    urgency_score = serializers.FloatField()
    importance_score = serializers.FloatField()
    effort_score = serializers.FloatField()
    dependency_score = serializers.FloatField()
    explanation = serializers.CharField()
    priority_level = serializers.CharField()
    days_until_due = serializers.IntegerField()


class TaskSuggestionSerializer(serializers.Serializer):
    """One suggested task plus explanation and rank."""
    task = ScoredTaskSerializer()
    score = serializers.FloatField()
    explanation = serializers.CharField()
    rank = serializers.IntegerField()