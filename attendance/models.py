from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Attendance_Employee_data(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "attendance_employee_data"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.employee_id})"

class Attendance_Attendance_data(models.Model):
    employee = models.ForeignKey(Attendance_Employee_data, on_delete=models.CASCADE)
    check_in_time = models.DateTimeField()
    check_out_time = models.DateTimeField(null=True, blank=True)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('half_day', 'Half Day'),
    ], default='present')
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # ✅ New Field
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "attendance_attendance_data"
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee.user.first_name} - {self.date}"

    def save(self, *args, **kwargs):
      if not self.date:
        self.date = timezone.now().date()

      if self.check_in_time and self.check_out_time:
        # Calculate working hours
        time_diff = self.check_out_time - self.check_in_time
        hours = time_diff.total_seconds() / 3600
        self.working_hours = round(hours, 2)

        # Check late first (before working hours)
        checkin_time_only = self.check_in_time.astimezone(timezone.get_current_timezone()).time()
        late_time = timezone.datetime(2000, 1, 1, 10, 15).time()

        if checkin_time_only > late_time:
            self.status = 'late'
        elif hours < 4:
            self.status = 'half_day'
        else:
            self.status = 'present'

        # Overtime
        if self.working_hours > 8:
            self.overtime_hours = self.working_hours - 8
        else:
            self.overtime_hours = 0

      super().save(*args, **kwargs)


class QR_Code(models.Model):
    location = models.CharField(max_length=100, default="Office", unique=True)
    code = models.CharField(max_length=200, unique=True)
    image = models.ImageField(upload_to='qr_codes/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "qr_code"

    def __str__(self):
        return f"QR Code - {self.location}"

    
class Payroll_Salary(models.Model):
    employee = models.OneToOneField(Attendance_Employee_data, on_delete=models.CASCADE)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)  # Monthly Salary
    overtime_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Per hour
    bonus = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        db_table = "payroll_salary"
    
    def __str__(self):
        return f"{self.employee.user.first_name} - Salary Details"

class Payroll_Payments(models.Model):
    employee = models.ForeignKey(Attendance_Employee_data, on_delete=models.CASCADE)
    month = models.IntegerField()  # Example: April = 4
    year = models.IntegerField()
    total_working_days = models.IntegerField()
    total_present_days = models.IntegerField()
    total_overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "payroll_payments"
        unique_together = ('employee', 'month', 'year')

    def __str__(self):
        return f"{self.employee.user.first_name} - Payroll {self.month}/{self.year}"
