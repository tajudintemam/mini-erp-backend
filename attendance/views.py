# attendance/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import date

from .models import AttendanceRecord
from .serializers import AttendanceRecordSerializer
from hr.models import Employee


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return AttendanceRecord.objects.all().select_related('employee')
        try:
            employee = user.employee_profile
            return AttendanceRecord.objects.filter(employee=employee)
        except Employee.DoesNotExist:
            return AttendanceRecord.objects.none()

    @action(detail=False, methods=['post'], url_path='check-in')
    def check_in(self, request):
        user = request.user
        try:
            employee = user.employee_profile
        except Employee.DoesNotExist:
            return Response({'error': 'User has no employee profile.'}, status=status.HTTP_400_BAD_REQUEST)

        today = date.today()
        record, created = AttendanceRecord.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'check_in': timezone.now()}
        )
        if not created:
            return Response({'error': 'Already checked in today.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], url_path='check-out')
    def check_out(self, request):
        user = request.user
        try:
            employee = user.employee_profile
        except Employee.DoesNotExist:
            return Response({'error': 'User has no employee profile.'}, status=status.HTTP_400_BAD_REQUEST)

        today = date.today()
        try:
            record = AttendanceRecord.objects.get(employee=employee, date=today)
        except AttendanceRecord.DoesNotExist:
            return Response({'error': 'No check-in record found for today.'}, status=status.HTTP_400_BAD_REQUEST)

        if record.check_out:
            return Response({'error': 'Already checked out.'}, status=status.HTTP_400_BAD_REQUEST)

        record.check_out = timezone.now()
        record.save()
        serializer = self.get_serializer(record)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        user = request.user
        try:
            employee = user.employee_profile
        except Employee.DoesNotExist:
            return Response({'error': 'No employee profile.'}, status=status.HTTP_400_BAD_REQUEST)

        month = request.query_params.get('month', date.today().month)
        year = request.query_params.get('year', date.today().year)
        records = AttendanceRecord.objects.filter(employee=employee, date__year=year, date__month=month)
        total_present = records.filter(status='PRESENT').count()
        total_late = records.filter(status='LATE').count()
        total_absent = records.filter(status='ABSENT').count()
        total_hours = records.aggregate(Sum('working_hours'))['working_hours__sum'] or 0
        return Response({
            'month': month,
            'year': year,
            'present': total_present,
            'late': total_late,
            'absent': total_absent,
            'total_working_hours': total_hours,
        })