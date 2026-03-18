from django.contrib import admin
from .models import LeaveRequest, LeaveType
# Register your models here.
admin.site.register(LeaveRequest)
admin.site.register(LeaveType)