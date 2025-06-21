from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import  Attendance_Employee_data, Attendance_Attendance_data
from .models import Attendance_LeaveRequest
from .models import SectionReport, HourlyReport
from django.core.exceptions import ValidationError

class SectionReportForm(forms.ModelForm):
    class Meta:
        model = SectionReport
        fields = ['section_title', 'report_text']
        widgets = {
            'section_title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Section Title'}),
            'report_text': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write section-wise report...'}),
        }

class HourlyReportForm(forms.ModelForm):
    class Meta:
        model = HourlyReport
        fields = ['hour_slot', 'task_summary']
        widgets = {
            'hour_slot': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2:00 - 3:00'}),
            'task_summary': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Write hourly task summary...'}),
        }



# def clean_report_text(self):
#         text = self.cleaned_data.get('report_text', '')
#         word_count = len(text.strip().split())

#         if word_count > 400:
#             raise ValidationError(f'Your report contains {word_count} words. Maximum allowed is 400.')

#         return text        

class UserRegistrationForm(UserCreationForm):
    profile_pic=forms.ImageField(required=False)
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'profile_pic']

class EmployeeRegistrationForm(forms.ModelForm):
    class Meta:
        model =  Attendance_Employee_data
        fields = ['employee_id', 'department', 'position', 'phone_number', 'profile_pic']

class ProfilePictureForm(forms.ModelForm):
    class Meta:
        model = Attendance_Employee_data
        fields = ['profile_pic']

        
class AttendanceForm(forms.ModelForm):
    qr_code = forms.CharField(widget=forms.HiddenInput())
    
    class Meta:
        model = Attendance_Attendance_data
        fields = ['qr_code']

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = Attendance_LeaveRequest
        fields = ['from_date', 'to_date', 'leave_type', 'message']  # Correct field names
        widgets = {
            'from_date': forms.SelectDateWidget(),
            'to_date': forms.SelectDateWidget(),
            'message': forms.Textarea(attrs={'rows': 3}),
        }