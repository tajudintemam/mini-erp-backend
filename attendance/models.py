# attendance/models.py
from django.db import models
from decimal import Decimal
from hr.models import Employee

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Late Arrival'),
        ('HALF_DAY', 'Half Day'),
        ('ON_LEAVE', 'On Approved Leave'),
    ]
    LOCATION_CHOICES = [
        ('OFFICE', 'Office'),
        ('REMOTE', 'Remote / Work From Home'),
        ('FIELD', 'Field / On-Site'),
    ]
    STANDARD_HOURS = Decimal('8.00')

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, editable=False)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PRESENT')
    location = models.CharField(max_length=20, choices=LOCATION_CHOICES, blank=True, null=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', 'employee']
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        unique_together = [['employee', 'date']]
        indexes = [
            models.Index(fields=['employee', 'date']),
            models.Index(fields=['date', 'status']),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.date} [{self.get_status_display()}]"

    def save(self, *args, **kwargs):
        if self.check_in and self.check_out:
            if self.check_out > self.check_in:
                duration = self.check_out - self.check_in
                total = Decimal(str(round(duration.total_seconds() / 3600, 2)))
                self.working_hours = total
                overtime = total - self.STANDARD_HOURS
                self.overtime_hours = max(Decimal('0'), overtime)
        # Auto-set LATE if check-in after 9 AM
        if self.check_in and self.check_in.hour >= 9 and self.status == 'PRESENT':
            self.status = 'LATE'
        super().save(*args, **kwargs)

    @property
    def is_complete(self):
        return self.check_in is not None and self.check_out is not None