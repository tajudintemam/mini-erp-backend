# leave_management/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import LeaveType, LeaveRequest
from .serializers import LeaveTypeSerializer, LeaveRequestSerializer
from hr.models import Employee


class LeaveTypeViewSet(viewsets.ModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']


class LeaveRequestViewSet(viewsets.ModelViewSet):
    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'leave_type']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LeaveRequest.objects.all().select_related('employee', 'leave_type', 'reviewed_by')
        try:
            employee = user.employee_profile
            return LeaveRequest.objects.filter(employee=employee).select_related('leave_type')
        except Employee.DoesNotExist:
            return LeaveRequest.objects.none()

    def perform_create(self, serializer):
        try:
            employee = self.request.user.employee_profile
            serializer.save(employee=employee)
        except Employee.DoesNotExist:
            # Return a proper error response
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"detail": "User does not have an employee profile."})

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        leave = self.get_object()

        # Check if leave is in PENDING status
        if leave.status != 'PENDING':
            return Response(
                {'error': 'Only PENDING requests can be approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has employee_profile
        try:
            reviewer = request.user.employee_profile
        except Employee.DoesNotExist:
            return Response(
                {'error': 'User does not have an employee profile.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user is authorized (staff or manager)
        if not request.user.is_staff:
            # Add additional authorization logic here if needed
            pass

        comment = request.data.get('comment', '')
        leave.approve(reviewer=reviewer, comment=comment)

        return Response({'detail': 'Leave request approved successfully.'})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        leave = self.get_object()

        # Check if leave is in PENDING status
        if leave.status != 'PENDING':
            return Response(
                {'error': 'Only PENDING requests can be rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has employee_profile
        try:
            reviewer = request.user.employee_profile
        except Employee.DoesNotExist:
            return Response(
                {'error': 'User does not have an employee profile.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user is authorized (staff or manager)
        if not request.user.is_staff:
            # Add additional authorization logic here if needed
            pass

        comment = request.data.get('comment', '')
        leave.reject(reviewer=reviewer, comment=comment)

        return Response({'detail': 'Leave request rejected successfully.'})