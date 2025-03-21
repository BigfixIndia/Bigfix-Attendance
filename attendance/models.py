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
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "attendance_attendance_data"  # ✅ Fix incorrect table name
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
            
            # Determine status based on working hours
            if hours < 4:
                self.status = 'half_day'
            elif self.check_in_time.time() > timezone.datetime(2000, 1, 1, 9, 15).time():  # If check-in after 9:15 AM
                self.status = 'late'
            else:
                self.status = 'present'
                
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

    
