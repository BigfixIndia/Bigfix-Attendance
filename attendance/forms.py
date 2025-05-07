from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import  Attendance_Employee_data, Attendance_Attendance_data
from .models import Attendance_LeaveRequest

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class EmployeeRegistrationForm(forms.ModelForm):
    class Meta:
        model =  Attendance_Employee_data
        fields = ['employee_id', 'department', 'position', 'phone_number']

class AttendanceForm(forms.ModelForm):
    qr_code = forms.CharField(widget=forms.HiddenInput())
    
    class Meta:
        model = Attendance_Attendance_data
        fields = ['qr_code']

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = Attendance_LeaveRequest
        fields = ['from_date', 'to_date', 'leave_type', 'message'] 
        widgets = {
            'from_date': forms.SelectDateWidget(),
            'to_date': forms.SelectDateWidget(),
            'message': forms.Textarea(attrs={'rows': 3}),
        }