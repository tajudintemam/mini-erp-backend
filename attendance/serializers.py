# attendance/serializers.py
from rest_framework import serializers
from .models import AttendanceRecord

class AttendanceRecordSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = '__all__'
        read_only_fields = ['id', 'working_hours', 'overtime_hours', 'created_at', 'updated_at']