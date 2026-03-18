# hr/models.py
from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="Full department name")
    code = models.CharField(max_length=10, unique=True, help_text="Short code, e.g. ENG")
    description = models.TextField(blank=True, null=True)
    manager = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return f"({self.code}) - {self.name}"

    @property
    def headcount(self):
        return self.employees.filter(status='ACTIVE').count()


class Position(models.Model):
    LEVEL_CHOICES = [
        ('JUNIOR', 'Junior'),
        ('MID', 'Mid-Level'),
        ('SENIOR', 'Senior'),
        ('LEAD', 'Lead / Principal'),
        ('MANAGER', 'Manager'),
        ('DIRECTOR', 'Director'),
    ]
    title = models.CharField(max_length=150, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='positions')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    min_salary = models.DecimalField(max_digits=10, decimal_places=2)
    max_salary = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['department', 'level', 'title']
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'

    def __str__(self):
        return f"{self.title} ({self.level}) - {self.department.code}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.min_salary and self.max_salary and self.min_salary > self.max_salary:
            raise ValidationError("Minimum salary cannot exceed maximum salary.")


class Employee(models.Model):
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
        ('PREFER_NOT_TO_SAY', 'Prefer not to say'),
    ]
    EMPLOYMENT_TYPE_CHOICES = [
        ('FULL_TIME', 'Full-Time'),
        ('PART_TIME', 'Part-Time'),
        ('CONTRACT', 'Contract'),
        ('INTERN', 'Intern'),
    ]
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('ON_LEAVE', 'On Leave'),
        ('SUSPENDED', 'Suspended'),
        ('TERMINATED', 'Terminated'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    national_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    profile_photo = models.ImageField(upload_to='employees/photos/', blank=True, null=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports'
    )
    hire_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='FULL_TIME')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bank_account = models.CharField(max_length=50, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    leave_balance = models.PositiveIntegerField(default=21)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['email']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def years_of_service(self):
        from datetime import date
        end = self.end_date or date.today()
        return (end - self.hire_date).days // 365

    def save(self, *args, **kwargs):
        if not self.employee_id:
            from datetime import date
            year = date.today().year
            last = Employee.objects.order_by('id').last()
            next_num = (last.id + 1) if last else 1
            self.employee_id = f"EMP-{year}-{next_num:04d}"
        super().save(*args, **kwargs)