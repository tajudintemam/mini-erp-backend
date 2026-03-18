# leave_management/models.py
from django.db import models
from django.utils import timezone
from hr.models import Employee

class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Display name, e.g. Annual Leave")
    code = models.CharField(max_length=20, unique=True, help_text="Short code, e.g. AL")
    max_days_per_year = models.PositiveIntegerField(help_text="Maximum days per year")
    requires_approval = models.BooleanField(default=True)
    is_paid = models.BooleanField(default=True)
    carry_forward = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Leave Type'
        verbose_name_plural = 'Leave Types'

    def __str__(self):
        return f"{self.code} - {self.name}"


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled by Employee'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name='requests')
    start_date = models.DateField()
    end_date = models.DateField()
    total_days = models.PositiveIntegerField(editable=False, default=0)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_leaves'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_comment = models.TextField(blank=True)
    attachment = models.FileField(upload_to='leave_attachments/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Leave Request'
        verbose_name_plural = 'Leave Requests'

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.code} ({self.start_date} to {self.end_date})"

    def save(self, *args, **kwargs):
        # Calculate total_days (simplified: count all days, including weekends)
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.total_days = delta.days + 1
        super().save(*args, **kwargs)

    def approve(self, reviewer: Employee, comment: str = ""):
        self.status = 'APPROVED'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_comment = comment
        self.save()
        # Deduct from leave balance
        self.employee.leave_balance = max(0, self.employee.leave_balance - self.total_days)
        self.employee.save(update_fields=['leave_balance'])

    def reject(self, reviewer: Employee, comment: str = ""):
        self.status = 'REJECTED'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_comment = comment
        self.save()