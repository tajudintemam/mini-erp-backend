# project_management/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Project, ProjectMember, Task, TaskComment
from .serializers import ProjectSerializer, ProjectMemberSerializer, TaskSerializer, TaskCommentSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().prefetch_related('members', 'tasks')
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'priority', 'is_active']

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        project = self.get_object()
        members = project.members.filter(is_active=True).select_related('employee')
        serializer = ProjectMemberSerializer(members, many=True)
        return Response(serializer.data)


class ProjectMemberViewSet(viewsets.ModelViewSet):
    queryset = ProjectMember.objects.all().select_related('project', 'employee')
    serializer_class = ProjectMemberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'role', 'is_active']


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'status', 'priority', 'assigned_to']

    def get_queryset(self):
        return Task.objects.all().select_related('project', 'assigned_to', 'created_by')

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        if task.status == 'DONE':
            return Response({'error': 'Task already completed.'}, status=status.HTTP_400_BAD_REQUEST)
        task.status = 'DONE'
        task.completed_at = timezone.now()
        task.save()
        return Response({'detail': 'Task marked as done.'})


class TaskCommentViewSet(viewsets.ModelViewSet):
    queryset = TaskComment.objects.all().select_related('task', 'author')
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['task']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.employee_profile)