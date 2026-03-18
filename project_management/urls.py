# project_management/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ProjectMemberViewSet, TaskViewSet, TaskCommentViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet)                # has queryset → OK
router.register(r'project-members', ProjectMemberViewSet)   # has queryset → OK
router.register(r'tasks', TaskViewSet, basename='task')     # explicit basename
router.register(r'task-comments', TaskCommentViewSet)       # has queryset → OK

urlpatterns = [
    path('', include(router.urls)),
]