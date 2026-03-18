from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token
from datetime import date, timedelta
from hr.models import Department, Position, Employee
from leave_management.models import LeaveType, LeaveRequest
from attendance.models import AttendanceRecord
from project_management.models import Project, Task


class AuthTestCase(APITestCase):
    def test_registration(self):
        url = '/api/auth/register/'
        data = {
            'username': 'testuser',
            'password': 'testpass123',
            'password2': 'testpass123',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(User.objects.count(), 1)

    def test_login(self):
        User.objects.create_user(username='testuser', password='testpass123')
        url = '/api/auth/login/'
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_protected_endpoint_requires_auth(self):
        response = self.client.get('/api/employees/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EmployeeTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='admin',
            password='admin123',
            is_staff=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        self.dept = Department.objects.create(name='Engineering', code='ENG')
        self.position = Position.objects.create(
            title='Backend Developer',
            department=self.dept,
            level='MID',
            min_salary=3000,
            max_salary=6000,
        )

    def test_create_employee(self):
        emp_user = User.objects.create_user(
            username='emp1',
            email='emp1@co.com',
            password='pass'
        )
        payload = {
            'user': emp_user.pk,
            'first_name': 'Alice',
            'last_name': 'Smith',
            'email': 'alice@company.com',
            'department': self.dept.pk,
            'position': self.position.pk,
            'hire_date': str(date.today()),
            'employment_type': 'FULL_TIME'
        }
        response = self.client.post('/api/employees/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Employee.objects.count(), 1)


class LeaveTestCase(APITestCase):
    def setUp(self):
        # Create regular employee user
        self.user = User.objects.create_user(
            username='emp',
            password='pass'
        )
        self.token = Token.objects.create(user=self.user)

        # Create department and position
        self.dept = Department.objects.create(name='Engineering', code='ENG')
        self.position = Position.objects.create(
            title='Developer',
            department=self.dept,
            level='JUNIOR',
            min_salary=2000,
            max_salary=4000
        )

        # Create employee profile for regular user
        self.employee = Employee.objects.create(
            user=self.user,
            first_name='John',
            last_name='Doe',
            email='john@co.com',
            department=self.dept,
            position=self.position,
            hire_date=date.today()
        )

        # Create leave type
        self.leave_type = LeaveType.objects.create(
            name='Annual Leave',
            code='AL',
            max_days_per_year=20
        )

        # Create manager user with employee profile
        self.manager_user = User.objects.create_user(
            username='manager',
            password='manager123',
            is_staff=True
        )
        self.manager_token = Token.objects.create(user=self.manager_user)

        # Create employee profile for manager
        self.manager_employee = Employee.objects.create(
            user=self.manager_user,
            first_name='Manager',
            last_name='User',
            email='manager@co.com',
            department=self.dept,
            position=self.position,
            hire_date=date.today()
        )

    def test_apply_for_leave(self):
        """Test applying for leave"""
        # Set credentials to regular employee
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        payload = {
            'leave_type': self.leave_type.pk,
            'start_date': (date.today() + timedelta(days=7)).isoformat(),
            'end_date': (date.today() + timedelta(days=10)).isoformat(),
            'reason': 'Family vacation.',
        }

        response = self.client.post('/api/leaves/', payload, format='json')

        # Debug output if test fails
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LeaveRequest.objects.count(), 1)

        leave_request = LeaveRequest.objects.first()
        self.assertEqual(leave_request.status, 'PENDING')
        self.assertEqual(leave_request.employee, self.employee)

    def test_approve_leave(self):
        """Test approving a leave request (as manager)"""
        # First create a leave request as regular employee
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=date.today() + timedelta(days=14),
            end_date=date.today() + timedelta(days=16),
            reason='Rest and relaxation',
            status='PENDING',
        )

        # Switch to manager credentials
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.manager_token.key)

        response = self.client.post(
            f'/api/leaves/{leave.pk}/approve/',
            {'comment': 'Approved. Enjoy your leave!'},
            format='json'
        )

        # Debug output if test fails
        if response.status_code != status.HTTP_200_OK:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh leave from database
        leave.refresh_from_db()
        self.assertEqual(leave.status, 'APPROVED')
        self.assertEqual(leave.reviewed_by, self.manager_employee)
        self.assertEqual(leave.review_comment, 'Approved. Enjoy your leave!')

    def test_reject_leave(self):
        """Test rejecting a leave request (as manager)"""
        # First create a leave request as regular employee
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=date.today() + timedelta(days=21),
            end_date=date.today() + timedelta(days=23),
            reason='Personal time off',
            status='PENDING',
        )

        # Switch to manager credentials
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.manager_token.key)

        response = self.client.post(
            f'/api/leaves/{leave.pk}/reject/',
            {'comment': 'Rejected due to project deadline.'},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Refresh leave from database
        leave.refresh_from_db()
        self.assertEqual(leave.status, 'REJECTED')
        self.assertEqual(leave.reviewed_by, self.manager_employee)
        self.assertEqual(leave.review_comment, 'Rejected due to project deadline.')


class AttendanceTestCase(APITestCase):
    def setUp(self):
        user = User.objects.create_user(
            username='att_user',
            password='pass'
        )
        self.token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        dept = Department.objects.create(name='Operations', code='OPS')
        pos = Position.objects.create(
            title='Operator',
            department=dept,
            level='JUNIOR',
            min_salary=1500,
            max_salary=2500
        )

        self.employee = Employee.objects.create(
            user=user,
            first_name='Carol',
            last_name='White',
            email='carol@co.com',
            department=dept,
            position=pos,
            hire_date=date.today()
        )

    def test_check_in(self):
        response = self.client.post('/api/attendance/check-in/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AttendanceRecord.objects.count(), 1)

    def test_check_out(self):
        # First check in
        self.client.post('/api/attendance/check-in/')

        # Then check out
        response = self.client.post('/api/attendance/check-out/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        record = AttendanceRecord.objects.first()
        self.assertIsNotNone(record.check_out)


class ProjectManagementTestCase(APITestCase):
    def setUp(self):
        user = User.objects.create_user(
            username='pm_user',
            password='pass',
            is_staff=True
        )
        self.token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

        dept = Department.objects.create(name='Development', code='DEV')
        pos = Position.objects.create(
            title='Project Manager',
            department=dept,
            level='MANAGER',
            min_salary=5000,
            max_salary=8000
        )

        self.employee = Employee.objects.create(
            user=user,
            first_name='Project',
            last_name='Manager',
            email='pm@co.com',
            department=dept,
            position=pos,
            hire_date=date.today()
        )

        self.project = Project.objects.create(
            name='New ERP System',
            code='NERP',
            description='Build a new ERP system',
            project_manager=self.employee,
            start_date=date.today()
        )

    def test_create_task(self):
        payload = {
            'project': self.project.pk,
            'title': 'Design Database Schema',
            'description': 'Design the database schema for the ERP system',
            'assigned_to': self.employee.pk,
            'created_by': self.employee.pk,
            'status': 'TODO',
            'priority': 'HIGH',
            'due_date': (date.today() + timedelta(days=7)).isoformat()
        }

        response = self.client.post('/api/tasks/', payload, format='json')

        # Debug output if test fails
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.count(), 1)

        task = Task.objects.first()
        self.assertEqual(task.title, 'Design Database Schema')
        self.assertEqual(task.project, self.project)