# hr/views.py
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Department, Position, Employee
from .serializers import DepartmentSerializer, PositionSerializer, EmployeeListSerializer, EmployeeDetailSerializer


@extend_schema_view(
    list=extend_schema(summary="List all departments"),
    create=extend_schema(summary="Create a new department"),
    retrieve=extend_schema(summary="Get department details"),
    update=extend_schema(summary="Update a department"),
    destroy=extend_schema(summary="Delete a department"),
)
class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().select_related('manager')
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all().select_related('department')
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['department', 'level', 'is_active']
    search_fields = ['title', 'description']


class EmployeeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['department', 'status', 'employment_type']
    search_fields = ['first_name', 'last_name', 'email', 'employee_id']
    ordering_fields = ['hire_date', 'last_name', 'salary']

    def get_queryset(self):
        return Employee.objects.all().select_related('user', 'department', 'position', 'manager')

    def get_serializer_class(self):
        if self.action == 'list':
            return EmployeeListSerializer
        return EmployeeDetailSerializer

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        employee = self.get_object()
        serializer = EmployeeDetailSerializer(employee, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def direct_reports(self, request, pk=None):
        employee = self.get_object()
        reports = employee.direct_reports.filter(status='ACTIVE')
        serializer = EmployeeListSerializer(reports, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        employee = self.get_object()
        from datetime import date
        employee.status = 'TERMINATED'
        employee.end_date = date.today()
        employee.save(update_fields=['status', 'end_date'])
        return Response({'detail': f'{employee.full_name} has been deactivated.'}, status=status.HTTP_200_OK)