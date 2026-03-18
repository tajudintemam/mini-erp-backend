from django.contrib import admin
from .models import Task, TaskComment, Project, ProjectMember
# Register your models here.
admin.site.register(Task)
admin.site.register(TaskComment)
admin.site.register(Project)
admin.site.register(ProjectMember)
