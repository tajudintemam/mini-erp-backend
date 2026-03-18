# hr/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DepartmentViewSet, PositionViewSet, EmployeeViewSet

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet)      # has queryset → OK
router.register(r'positions', PositionViewSet)          # has queryset → OK
router.register(r'employees', EmployeeViewSet, basename='employee')   # explicit basename

urlpatterns = [
    path('', include(router.urls)),
]