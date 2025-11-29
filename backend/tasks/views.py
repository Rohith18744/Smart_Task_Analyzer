"""REST API endpoints for analyzing and suggesting tasks."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    TaskAnalysisRequestSerializer,
    ScoredTaskSerializer,
    TaskSuggestionSerializer
)
from .scoring import TaskScorer
from datetime import datetime, timedelta


@api_view(['POST'])
def analyze_tasks(request):
    """Validate tasks and return them sorted by computed priority."""
    try:
        # Validate incoming data
        serializer = TaskAnalysisRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                {
                    'error': 'Invalid request data',
                    'details': serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = serializer.validated_data
        tasks = validated_data['tasks']
        strategy = validated_data.get('strategy', 'smart_balance')
        
        # Handle empty task list
        if not tasks:
            return Response(
                {
                    'error': 'No tasks provided',
                    'sorted_tasks': [],
                    'strategy_used': strategy,
                    'total_tasks': 0
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize scorer with selected strategy
        scorer = TaskScorer(strategy=strategy)
        
        # Analyze and sort tasks
        sorted_tasks, error = scorer.analyze_tasks(tasks)
        
        if error:
            return Response(
                {
                    'error': error,
                    'sorted_tasks': [],
                    'strategy_used': strategy
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Serialize scored tasks
        result_serializer = ScoredTaskSerializer(sorted_tasks, many=True)
        
        return Response(
            {
                'sorted_tasks': result_serializer.data,
                'strategy_used': strategy,
                'total_tasks': len(sorted_tasks),
                'analysis_timestamp': datetime.now().isoformat(),
                'message': f'Successfully analyzed {len(sorted_tasks)} tasks using {strategy} strategy'
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {
                'error': 'Internal server error',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET', 'POST'])
def suggest_tasks(request):
    """Return the top N task suggestions with short explanations."""
    try:
        # Handle both GET and POST requests
        if request.method == 'POST':
            serializer = TaskAnalysisRequestSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        'error': 'Invalid request data',
                        'details': serializer.errors
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            validated_data = serializer.validated_data
            tasks = validated_data['tasks']
            strategy = validated_data.get('strategy', 'smart_balance')
        
        else:  # GET request
            import json
            
            strategy = request.GET.get('strategy', 'smart_balance')
            tasks_json = request.GET.get('tasks', '[]')
            
            try:
                tasks = json.loads(tasks_json)
            except json.JSONDecodeError:
                return Response(
                    {
                        'error': 'Invalid tasks JSON format'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate tasks if provided
            if tasks:
                task_serializer = TaskAnalysisRequestSerializer(
                    data={'tasks': tasks, 'strategy': strategy}
                )
                
                if not task_serializer.is_valid():
                    return Response(
                        {
                            'error': 'Invalid task data',
                            'details': task_serializer.errors
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                tasks = task_serializer.validated_data['tasks']
        
        # Handle empty task list
        if not tasks:
            return Response(
                {
                    'suggestions': [],
                    'strategy_used': strategy,
                    'suggestion_count': 0,
                    'message': 'No tasks available for suggestions'
                },
                status=status.HTTP_200_OK
            )
        
        # Initialize scorer
        scorer = TaskScorer(strategy=strategy)
        
        # Get top suggestions
        suggestions = scorer.get_top_suggestions(tasks, count=3)
        
        # Serialize suggestions
        result_serializer = TaskSuggestionSerializer(suggestions, many=True)
        
        return Response(
            {
                'suggestions': result_serializer.data,
                'strategy_used': strategy,
                'suggestion_count': len(suggestions),
                'generated_at': datetime.now().isoformat(),
                'message': f'Top {len(suggestions)} task recommendations for today'
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {
                'error': 'Internal server error',
                'details': str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def health_check(request):
    """Simple health check endpoint."""
    return Response(
        {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'message': 'Smart Task Analyzer API is running'
        },
        status=status.HTTP_200_OK
    )