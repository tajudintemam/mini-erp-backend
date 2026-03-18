# project_management/serializers.py
from rest_framework import serializers
from .models import Project, ProjectMember, Task, TaskComment

class ProjectSerializer(serializers.ModelSerializer):
    completion_percentage = serializers.ReadOnlyField()
    remaining_budget = serializers.ReadOnlyField()

    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ProjectMemberSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = ProjectMember
        fields = '__all__'
        read_only_fields = ['id', 'joined_at']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(source='assigned_to.full_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class TaskCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)

    class Meta:
        model = TaskComment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']