# project_management/models.py
from django.db import models
from hr.models import Employee

class Project(models.Model):
    STATUS_CHOICES = [
        ('PLANNING', 'Planning'),
        ('IN_PROGRESS', 'In Progress'),
        ('ON_HOLD', 'On Hold'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    project_manager = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='managed_projects'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNING')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    budget = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    spent_budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    github_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', 'name']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

    def __str__(self):
        return f"[{self.code}] {self.name}"

    @property
    def completion_percentage(self):
        total = self.tasks.count()
        if total == 0:
            return 0
        done = self.tasks.filter(status='DONE').count()
        return round((done / total) * 100, 1)

    @property
    def remaining_budget(self):
        if self.budget is None:
            return None
        return self.budget - self.spent_budget


class ProjectMember(models.Model):
    ROLE_CHOICES = [
        ('MANAGER', 'Project Manager'),
        ('TECH_LEAD', 'Technical Lead'),
        ('DEVELOPER', 'Developer'),
        ('DESIGNER', 'Designer / UX'),
        ('QA', 'Quality Assurance'),
        ('ANALYST', 'Business Analyst'),
        ('STAKEHOLDER', 'Stakeholder'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='members')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='project_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='DEVELOPER')
    joined_at = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [['project', 'employee']]
        ordering = ['project', 'role']
        verbose_name = 'Project Member'
        verbose_name_plural = 'Project Members'

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_role_display()} on {self.project.code}"


class Task(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    STATUS_CHOICES = [
        ('BACKLOG', 'Backlog'),
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('IN_REVIEW', 'In Review'),
        ('DONE', 'Done'),
        ('BLOCKED', 'Blocked'),
    ]
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BACKLOG')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date', 'title']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __str__(self):
        return f"[{self.project.code}] {self.title} [{self.status}]"


class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='task_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Task Comment'

    def __str__(self):
        return f"Comment by {self.author.full_name} on {self.task.title}"