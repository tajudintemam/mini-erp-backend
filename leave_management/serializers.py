from rest_framework import serializers
from .models import LeaveType, LeaveRequest

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class LeaveRequestSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.full_name', read_only=True)

    class Meta:
        model = LeaveRequest
        fields = '__all__'
        read_only_fields = [
            'id',
            'employee',           # Add this
            'total_days',
            'status',
            'reviewed_by',
            'reviewed_at',
            'created_at',
            'updated_at'
        ]