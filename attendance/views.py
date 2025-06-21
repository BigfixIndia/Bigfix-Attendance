from datetime import datetime
from io import BytesIO
import json
import os
from urllib import request
from venv import logger 
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseNotAllowed, JsonResponse
from django.db import IntegrityError
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import get_object_or_404
import qrcode
from django.views.decorators.http import require_http_methods
from django.core.files.base import ContentFile  # ✅ Add this import
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
import pytz
from .models import Payroll_Payments
from .models import Attendance_Attendance_data, Payroll_Salary
from django.contrib.admin.views.decorators import staff_member_required
from datetime import date
from django.shortcuts import render
from datetime import timedelta
from datetime import datetime, time, date
from datetime import date, time
from datetime import timezone
from django.utils import timezone
from .models import Announcement
from .models import AnnouncementRead
from .forms import LeaveRequestForm 
# from .forms import DailyReportForm
from .models import Attendance_LeaveRequest
from .models import Attendance_Log
from datetime import date
from django.utils.timezone import localtime
from .models import Holiday
from operator import itemgetter
from datetime import date, timedelta
from django.contrib.auth.decorators import user_passes_test

from django.db.models import Prefetch
from calendar import monthrange
from dateutil.relativedelta import relativedelta

from .forms import DailyReportForm
from .models import DailyReport, ReportComment, ReportReaction
from django.db.models import Count, Q

from .forms import SectionReportForm, HourlyReportForm
from .models import SectionReport, HourlyReport
from .models import ReportComment, ReportReaction

from django.utils import timezone
from datetime import datetime
from django.core.paginator import Paginator

from .models import  Attendance_Employee_data, Attendance_Attendance_data, QR_Code
from .forms import UserRegistrationForm, EmployeeRegistrationForm
from .utils import generate_qr_code
from django.contrib.admin.views.decorators import staff_member_required
# Assuming you'll create a model for Tamil Nadu Holidays
try:
    from .models import TamilNaduPublicHoliday
except ImportError:
    class TamilNaduPublicHoliday:
        # Dummy class if the model doesn't exist yet
        objects = []

@login_required
def calendar_page(request):
    return render(request, 'attendance/calendar.html')

@login_required
def calendar_events(request):
    employee = Attendance_Employee_data.objects.get(user=request.user)
    events = []
    today = date.today()
    start_of_month = date(today.year, today.month, 1)
    end_of_month = date(today.year, today.month + 1, 1) - timedelta(days=1)

    # Tamil Nadu Public Holidays
    for holiday in TamilNaduPublicHoliday.objects.filter(date__gte=start_of_month, date__lte=end_of_month):
        events.append({
            'title': holiday.title,
            'start': str(holiday.date),
            'color': '#dc3545',  # Red for Holidays
            'allDay': True,
        })

    # General Holidays
    for holiday in Holiday.objects.filter(date__gte=start_of_month, date__lte=end_of_month):
        events.append({
            'title': holiday.title,
            'start': str(holiday.date),
            'color': '#ffc107',  # Yellow for general Holidays
            'allDay': True,
        })

    # Workdays (assuming 'Present' status in Attendance_Attendance_data)
    workdays = Attendance_Attendance_data.objects.filter(
        employee=employee,
        date__gte=start_of_month,
        date__lte=end_of_month,
        status='Present'
    )
    for day in workdays:
        events.append({
            'title': 'Work Day',
            'start': str(day.date),
            'color': '#198754',  # Green for Workdays
            'allDay': True,
        })

    # Leave Requests
    leave_requests = Attendance_LeaveRequest.objects.filter(
        employee=employee,
        #is_approved=True,
        from_date__lte=end_of_month,
        to_date__gte=start_of_month,
    )
    for leave in leave_requests:
        current_date = leave.from_date
        while current_date <= leave.to_date:
            if start_of_month <= current_date <= end_of_month:
                events.append({
                    'title': 'Leave',
                    'start': str(current_date),
                    'color': '#0d6efd',  # Blue for Leave
                    'allDay': True,
                })
            current_date += timedelta(days=1)

    return JsonResponse(events, safe=False)


def is_admin(user):
    return user.is_superuser or user.is_staff

@user_passes_test(is_admin)
@staff_member_required
def admin_dashboard(request):
    today = datetime.today().strftime('%Y-%m-%d')
    employees = Attendance_Employee_data.objects.all()
    attendance_records = Attendance_Attendance_data.objects.all()
    announcements = Announcement.objects.all().order_by('-created_at')[:5]

    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        file = request.FILES.get('attachment')  # <-- correct

        if title and message:
            Announcement.objects.create(
                title=title,
                message=message,
                created_by=request.user,
                attachment=file  # <-- file will be saved now
            )
            return redirect('admin_dashboard')

    context = {
        "employees": employees,
        "attendance_records": attendance_records,
        "today": today,
        "announcements": announcements
    }
    return render(request, "admin_dashboard.html", context)

from datetime import date, time
from django.utils import timezone
from django.shortcuts import render
from operator import itemgetter
from .models import Attendance_Employee_data, Attendance_Attendance_data, Attendance_LeaveRequest

# def dashboard_view(request):
#     today = date.today()
#     status_list = []
#     present_employees = []
#     leave_list = []
#     absent_list = []
#     today_attendance = None
#     has_checked_in = False
#     has_checked_out = False
#     working_hours_display = None
#     current_employee = None

#     user = request.user
#     if user.is_authenticated:
#         try:
#             current_employee = Attendance_Employee_data.objects.get(user=user)
#             today_attendance = Attendance_Attendance_data.objects.filter(
#                 employee=current_employee, date=today
#             ).first()

#             has_checked_in = today_attendance is not None and today_attendance.check_in_time is not None
#             has_checked_out = today_attendance is not None and today_attendance.check_out_time is not None

#             if has_checked_in and has_checked_out:
#                 time_diff = today_attendance.check_out_time - today_attendance.check_in_time
#                 total_seconds = time_diff.total_seconds()
#                 hours = int(total_seconds // 3600)
#                 minutes = int((total_seconds % 3600) // 60)
#                 working_hours_display = f"{hours:02d}:{minutes:02d}"
#         except Attendance_Employee_data.DoesNotExist:
#             pass

#     # Define shift-specific on-time and working hours requirements
#     shift_thresholds = {
#         'general': time(9, 45),
#         'morning': time(9, 45),
#         'evening': time(14, 15),
#         'both': time(10, 0),
#     }

#     shift_minimum_hours = {
#         'general': 8,
#         'morning': 4,
#         'evening': 4,
#         'both': 8,
#     }

#     all_employees = Attendance_Employee_data.objects.filter(user__isnull=False)

#     for employee in all_employees:
#         user_obj = employee.user
#         record = Attendance_Attendance_data.objects.filter(employee=employee, date=today).first()
#         leave = Attendance_LeaveRequest.objects.filter(
#             employee=employee,
#             from_date__lte=today,
#             to_date__gte=today
#         ).first()

#         shift_display = record.get_shift_type_display() if record and record.shift_type else "Not Set"
#         shift_key = record.shift_type if record and record.shift_type else None
#         on_time_threshold = shift_thresholds.get(shift_key)
#         required_hours = shift_minimum_hours.get(shift_key, 8)

#         status = {
#             "name": f"{user_obj.first_name} {user_obj.last_name}",
#             "check_in": None,
#             "check_out": None,
#             "color": "",
#             "check_in_raw": None,
#             "shift": shift_display,
#             "timing_status": "",
#             "early_checkout": False,
#         }

#         if leave:
#             leave_list.append({"employee__name": status["name"]})
#         elif record and record.check_in_time:
#             check_in_ist = timezone.localtime(record.check_in_time)
#             status["check_in"] = check_in_ist.strftime('%I:%M %p')
#             status["check_in_raw"] = check_in_ist

#             if record.check_out_time:
#                 check_out_ist = timezone.localtime(record.check_out_time)
#                 status["check_out"] = check_out_ist.strftime('%I:%M %p')

#                 total_duration = record.check_out_time - record.check_in_time
#                 total_hours = total_duration.total_seconds() / 3600

#                 if total_hours < required_hours:
#                     status["early_checkout"] = True

#             if on_time_threshold and check_in_ist.time() > on_time_threshold:
#                 status["color"] = "text-danger"
#                 status["timing_status"] = "Late"
#             else:
#                 status["color"] = "text-success"
#                 status["timing_status"] = "On Time"

#             present_employees.append(status)
#         else:
#             absent_list.append({"name": status["name"]})

#     present_employees.sort(key=itemgetter('check_in_raw'))
#     status_list = present_employees

#     return render(request, 'attendance/dashboard_view.html', {
#         "today": today,
#         "status_list": status_list,
#         "present_count": len(present_employees),
#         "leave_list": leave_list,
#         "absent_list": absent_list,
#         "today_attendance": today_attendance,
#         "has_checked_in": has_checked_in,
#         "has_checked_out": has_checked_out,
#         "working_hours_display": working_hours_display
#     })


def dashboard_view(request):
    today = date.today()
    status_list = []
    present_employees = []
    leave_list = []
    absent_list = []
    today_attendance = None
    has_checked_in = False
    has_checked_out = False
    working_hours_display = None
    current_employee = None

    user = request.user
    if user.is_authenticated:
        try:
            current_employee = Attendance_Employee_data.objects.get(user=user)
            today_attendance = Attendance_Attendance_data.objects.filter(
                employee=current_employee, date=today
            ).first()

            has_checked_in = today_attendance is not None and today_attendance.check_in_time is not None
            has_checked_out = today_attendance is not None and today_attendance.check_out_time is not None

            if has_checked_in and has_checked_out:
                time_diff = today_attendance.check_out_time - today_attendance.check_in_time
                total_seconds = time_diff.total_seconds()
                hours = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                working_hours_display = f"{hours:02d}:{minutes:02d}"
        except Attendance_Employee_data.DoesNotExist:
            pass

    # Shift-specific thresholds
    shift_thresholds = {
        'general': time(9, 45),
        'morning': time(9, 45),
        'evening': time(14, 15),
        'both': time(10, 0),
    }

    shift_minimum_hours = {
        'general': 8,
        'morning': 4,
        'evening': 4,
        'both': 8,
    }

    all_employees = Attendance_Employee_data.objects.filter(user__isnull=False, is_active=True)

    for employee in all_employees:
        user_obj = employee.user
        record = Attendance_Attendance_data.objects.filter(employee=employee, date=today).first()
        leave = Attendance_LeaveRequest.objects.filter(
            employee=employee,
            from_date__lte=today,
            to_date__gte=today,
            status='APPROVED'  # ✅ Only approved leaves
        ).first()

        shift_display = record.get_shift_type_display() if record and record.shift_type else "Not Set"
        shift_key = record.shift_type if record and record.shift_type else None
        on_time_threshold = shift_thresholds.get(shift_key)
        required_hours = shift_minimum_hours.get(shift_key, 8)

        status = {
            "name": f"{user_obj.first_name} {user_obj.last_name}",
            "check_in": None,
            "check_out": None,
            "color": "",
            "check_in_raw": None,
            "shift": shift_display,
            "timing_status": "",
            "early_checkout": False,
        }

        if leave:
            leave_list.append({"employee__name": status["name"]})  # ✅ Add only approved leave here
        elif record and record.check_in_time:
            check_in_ist = timezone.localtime(record.check_in_time)
            status["check_in"] = check_in_ist.strftime('%I:%M %p')
            status["check_in_raw"] = check_in_ist

            if record.check_out_time:
                check_out_ist = timezone.localtime(record.check_out_time)
                status["check_out"] = check_out_ist.strftime('%I:%M %p')

                total_duration = record.check_out_time - record.check_in_time
                total_hours = total_duration.total_seconds() / 3600

                if total_hours < required_hours:
                    status["early_checkout"] = True

            if on_time_threshold and check_in_ist.time() > on_time_threshold:
                status["color"] = "text-danger"
                status["timing_status"] = "Late"
            else:
                status["color"] = "text-success"
                status["timing_status"] = "On Time"

            present_employees.append(status)
        else:
            absent_list.append({"name": status["name"]})

    present_employees.sort(key=itemgetter('check_in_raw'))
    status_list = present_employees

    return render(request, 'attendance/dashboard_view.html', {
        "today": today,
        "status_list": status_list,
        "present_count": len(present_employees),
        "leave_list": leave_list,
        "absent_list": absent_list,
        "today_attendance": today_attendance,
        "has_checked_in": has_checked_in,
        "has_checked_out": has_checked_out,
        "working_hours_display": working_hours_display
    })


@staff_member_required
def fetch_attendance_data(request):
    selected_date = request.GET.get('date', datetime.today().strftime('%Y-%m-%d'))
    attendance_records = Attendance_Attendance_data.objects.filter(date=selected_date).select_related('user')

    data = [
        {
            "username": record.user.username,
            "check_in": record.check_in.strftime("%H:%M:%S") if record.check_in else "N/A",
            "check_out": record.check_out.strftime("%H:%M:%S") if record.check_out else "N/A"
        }
        for record in attendance_records
    ]

    return JsonResponse({"attendance": data})

@login_required
def admin_attendance_view(request):
    return render(request, 'admin_attendance.html')


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()  # Strip spaces
        password = request.POST.get("password", "").strip()

        if not username or not password:
            messages.error(request, "Both username and password are required.")
            return render(request, 'attendance/login.html') 

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")  # Success message
            return redirect("dashboard")  # Redirect to dashboard or home page
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, 'attendance/login.html') 

    return render(request, 'attendance/login.html') 


def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'attendance/login.html')


from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import UserRegistrationForm, EmployeeRegistrationForm

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        employee_form = EmployeeRegistrationForm(request.POST, request.FILES)  # <-- this handles profile_pic
        
        if user_form.is_valid() and employee_form.is_valid():
            user = user_form.save()

            # Save employee data and profile_pic
            employee = employee_form.save(commit=False)
            employee.user = user
            if 'profile_pic' in request.FILES:
                employee.profile_pic = request.FILES['profile_pic']  # <-- add this line
            employee.save()
            
            # Log in user
            username = user_form.cleaned_data.get('username')
            password = user_form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)

            messages.success(request, f"Account created for {username}. You are now logged in.")
            return redirect('dashboard')
        else:
            messages.error(request, "Registration failed. Please correct the errors below.")
    else:
        user_form = UserRegistrationForm()
        employee_form = EmployeeRegistrationForm()

    return render(request, 'attendance/register.html', {
        'user_form': user_form,
        'employee_form': employee_form
    })

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .forms import EmployeeRegistrationForm, ProfilePictureForm
from .models import Attendance_Employee_data
import magic
import base64
import os
import subprocess
import tempfile



# def dashboard(request):
#     try:
#         employee = Attendance_Employee_data.objects.get(user=request.user)
#     except Attendance_Employee_data.DoesNotExist:
#         employee = None
#     form = ProfilePictureForm(instance=employee)
#     return render(request, 'attendance/dashboard.html', {'employee': employee, 'form': form})


def dashboard(request):
    try:
        employee = Attendance_Employee_data.objects.get(user=request.user)
    except Attendance_Employee_data.DoesNotExist:
        employee = None
    form = ProfilePictureForm(instance=employee)
    return render(request, 'attendance/dashboard.html', {'employee': employee, 'form': form})

@login_required
def change_profile_picture(request):
    try:
        employee = Attendance_Employee_data.objects.get(user=request.user)
    except Attendance_Employee_data.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProfilePictureForm(request.POST, request.FILES, instance=employee)
        
        if 'profile_pic' not in request.FILES:
            messages.error(request, "No file selected. Please choose an image.")
            return redirect('dashboard')

        file = request.FILES['profile_pic']
        mime = magic.Magic(mime=True)
        file_type = mime.from_buffer(file.read(1024))
        file.seek(0)
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if file_type not in allowed_types:
            messages.error(request, f"Invalid file format. Only JPEG, PNG, or GIF allowed. Got: {file_type}")
            return redirect('dashboard')

        max_size = 5 * 1024 * 1024  # 5MB
        if file.size > max_size:
            messages.error(request, f"File too large. Maximum size is 5MB. Got: {file.size / 1024 / 1024:.2f}MB")
            return redirect('dashboard')

        if form.is_valid():
            employee.profile_pic = file
            employee.save()
            messages.success(request, "Profile picture updated successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error in {field}: {error}")
        return redirect('dashboard')
    else:
        return redirect('dashboard')


@login_required
def download_id_card(request):
    try:
        employee = Attendance_Employee_data.objects.get(user=request.user)
    except Attendance_Employee_data.DoesNotExist:
        messages.error(request, "Employee profile not found.")
        return redirect('dashboard')

    return render(request, 'print_idcard.html', {'employee': employee})

def calculate_working_hours(working_hours):
    if working_hours is None:
        return "0 hr 0 min"
    
    total_minutes = round(working_hours * 60)  # Convert float hours to total minutes
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours} hr {minutes} min"

@csrf_exempt
@login_required
def dashboard(request):
    today = timezone.now().date()
    employee = get_object_or_404(Attendance_Employee_data, user=request.user)

    mark_attendance = Attendance_Attendance_data.objects.filter(employee=employee, date=today).first()
    has_checked_in = bool(mark_attendance and mark_attendance.check_in_time)
    has_checked_out = bool(mark_attendance and mark_attendance.check_out_time)

    today_logs = Attendance_Attendance_data.objects.filter(employee=employee, date=today).order_by('date')

    # Leave Form
    leave_form = LeaveRequestForm()
    if request.method == 'POST' and 'leave_request' in request.POST:
        leave_form = LeaveRequestForm(request.POST)
        if leave_form.is_valid():
            leave = leave_form.save(commit=False)
            leave.employee = employee
            leave.save()
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('dashboard')

    # Shift Selection
    if request.method == 'POST' and 'set_shift' in request.POST:
        selected_shift = request.POST.get('shift_type')
        if selected_shift:
            attendance, created = Attendance_Attendance_data.objects.get_or_create(
                employee=employee,
                date=today,
                defaults={'check_in_time': None}
            )
            if not attendance.check_in_time:
                attendance.shift_type = selected_shift
                attendance.save()
                messages.success(request, f"Shift set to {attendance.get_shift_type_display()}")
            else:
                messages.warning(request, "Shift can't be changed after check-in.")
            return redirect('dashboard')

    # Working Hours Calculation
    working_hours_display = None
    if has_checked_in and has_checked_out:
        time_diff = (mark_attendance.check_out_time - mark_attendance.check_in_time).total_seconds() / 3600
        working_hours_display = calculate_working_hours(time_diff)

    # Monthly Attendance Summary
    selected_month = request.GET.get('month')
    today_obj = date.today()
    selected_date = datetime.strptime(selected_month, "%Y-%m").date() if selected_month else today_obj.replace(day=1)
    start_date = selected_date.replace(day=1)
    end_date = (start_date + relativedelta(months=1)) - relativedelta(days=1)

    recent_attendances = Attendance_Attendance_data.objects.filter(
        employee=employee, date__range=(start_date, end_date)
    ).order_by('-date')

    for record in recent_attendances:
        if record.check_in_time and record.check_out_time:
            diff_hours = (record.check_out_time - record.check_in_time).total_seconds() / 3600
            record.working_hours_display = calculate_working_hours(diff_hours)
        else:
            record.working_hours_display = "0 hr 0 min"

    # Announcements
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]
    read_announcements = AnnouncementRead.objects.filter(user=request.user).values_list('announcement_id', flat=True)
    for ann in announcements:
        ann.is_read = ann.id in read_announcements
    unread_announcements = [ann for ann in announcements if not ann.is_read]
    for ann in unread_announcements:
        AnnouncementRead.objects.create(user=request.user, announcement=ann)

    month_options = [
        {"value": (today_obj - relativedelta(months=i)).strftime("%Y-%m"),
         "label": (today_obj - relativedelta(months=i)).strftime("%B %Y")}
        for i in range(3)
    ]

    shift_display = mark_attendance.get_shift_type_display() if mark_attendance and mark_attendance.shift_type else "Not Set"

    # Section and Hourly Reports
    section_report_form = SectionReportForm()
    hourly_report_form = HourlyReportForm()

    if request.method == 'POST':
        if 'submit_section_report' in request.POST:
            section_report_form = SectionReportForm(request.POST)
            if section_report_form.is_valid() and mark_attendance:
                sr = section_report_form.save(commit=False)
                sr.attendance = mark_attendance
                sr.save()
                messages.success(request, "Section report submitted successfully!")
                return redirect('dashboard')
            else:
                messages.error(request, "Failed to submit section report. Please check the form.")

        elif 'submit_hourly_report' in request.POST:
            hourly_report_form = HourlyReportForm(request.POST)
            if hourly_report_form.is_valid() and mark_attendance:
                hr = hourly_report_form.save(commit=False)
                hr.attendance = mark_attendance
                hr.save()
                messages.success(request, "Hourly report submitted successfully!")
                return redirect('dashboard')
            else:
                messages.error(request, "Failed to submit hourly report. Please check the form.")

    # Fetch today's reports
    today_section_reports = SectionReport.objects.filter(attendance=mark_attendance) if mark_attendance else []
    today_hourly_reports = HourlyReport.objects.filter(attendance=mark_attendance) if mark_attendance else []

    # Fetch past reports
    past_section_reports = SectionReport.objects.filter(attendance__employee=employee).exclude(attendance=mark_attendance).order_by('-submitted_at')[:30]
    past_hourly_reports = HourlyReport.objects.filter(attendance__employee=employee).exclude(attendance=mark_attendance).order_by('-submitted_at')[:30]

    # Determine if report form should be shown
    show_report_form = has_checked_in and not has_checked_out

    # Context
    context = {
        'employee': employee,
        'mark_attendance': mark_attendance,
        'has_checked_in': has_checked_in,
        'has_checked_out': has_checked_out,
        'working_hours_display': working_hours_display,
        'recent_attendances': recent_attendances,
        'announcements': announcements,
        'unread_count': len(unread_announcements),
        'leave_form': leave_form,
        'today_logs': today_logs,
        'month_options': month_options,
        'selected_month': selected_month or today_obj.strftime("%Y-%m"),
        'shift_display': shift_display,
        'show_report_form': show_report_form,
        'section_report_form': section_report_form,
        'hourly_report_form': hourly_report_form,
        'today_section_reports': today_section_reports,
        'today_hourly_reports': today_hourly_reports,
        'past_section_reports': past_section_reports,
        'past_hourly_reports': past_hourly_reports,
    }

    return render(request, 'attendance/dashboard.html', context)

def calculate_working_hours(time_diff):
    hours = int(time_diff)
    minutes = int((time_diff - hours) * 60)
    return f"{hours} hr {minutes} min"


# def public_reports(request):
#     from_date = request.GET.get('from')
#     to_date = request.GET.get('to')

#     # Base queryset with related employee and reactions preloaded
#     reports = DailyReport.objects.select_related('attendance__employee') \
#                                  .prefetch_related('reactions') \
#                                  .order_by('-attendance__date')

#     # Apply date filtering if provided
#     if from_date and to_date:
#         reports = reports.filter(
#             attendance__date__range=[from_date, to_date]
#         )

#     # Add reaction counts for display
#     for report in reports:
#         report.employee_name = f"{report.attendance.employee.user.first_name} {report.attendance.employee.user.last_name}"
#         report.date = report.attendance.date
#         report.like_count = report.reactions.filter(reaction_type='like').count()
#         report.love_count = report.reactions.filter(reaction_type='love').count()
#         report.fire_count = report.reactions.filter(reaction_type='fire').count()

#     context = {
#         'reports': reports,
#         'from_date': from_date,
#         'to_date': to_date,
#     }
#     return render(request, 'attendance/public_reports.html', context)


from django.db.models import Count, Q, F, Value, CharField
from django.db.models.functions import Concat


def public_reports(request):
    from_date = request.GET.get('from')
    to_date = request.GET.get('to')
    report_type = request.GET.get('type', 'hourly')  # default to 'hourly' or change as needed

    reports = []
    model_name = ""

    if report_type == 'hourly':
        reports = HourlyReportForm.objects.select_related('attendance__employee__user') \
            .prefetch_related('reactions') \
            .annotate(
                employee_name=Concat(
                    F('attendance__employee__user__first_name'),
                    Value(' '),
                    F('attendance__employee__user__last_name'),
                    output_field=CharField()
                ),
                date=F('attendance__date'),
                like_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
                love_count=Count('reactions', filter=Q(reactions__reaction_type='love')),
                fire_count=Count('reactions', filter=Q(reactions__reaction_type='fire'))
            ).order_by('-submitted_at')
        model_name = "Hourly Report"

    elif report_type == 'section':
        reports = SectionReportForm.objects.select_related('attendance__employee__user') \
            .prefetch_related('reactions') \
            .annotate(
                employee_name=Concat(
                    F('attendance__employee__user__first_name'),
                    Value(' '),
                    F('attendance__employee__user__last_name'),
                    output_field=CharField()
                ),
                date=F('attendance__date'),
                like_count=Count('reactions', filter=Q(reactions__reaction_type='like')),
                love_count=Count('reactions', filter=Q(reactions__reaction_type='love')),
                fire_count=Count('reactions', filter=Q(reactions__reaction_type='fire'))
            ).order_by('-submitted_at')
        model_name = "Section Report"

    # Apply date filter
    if from_date and to_date:
        reports = reports.filter(attendance__date__range=[from_date, to_date])

    context = {
        'reports': reports,
        'from_date': from_date,
        'to_date': to_date,
        'report_type': report_type,
        'model_name': model_name,
    }
    return render(request, 'attendance/public_reports.html', context)

@csrf_exempt
def submit_comment(request, report_type, report_id):
    if request.method == 'POST':
        if report_type == 'hourly':
            report = get_object_or_404(HourlyReportForm, id=report_id)
        elif report_type == 'section':
            report = get_object_or_404(SectionReportForm, id=report_id)
        else:
            return redirect('public_reports')

        name = request.POST.get('name', 'Anonymous')
        comment = request.POST.get('comment')
        if comment:
            ReportComment.objects.create(report=report, name=name, comment=comment)

    return redirect('public_reports')

@csrf_exempt
def submit_reaction(request, report_type, report_id, reaction_type):
    if report_type == 'hourly':
        report = get_object_or_404(HourlyReportForm, id=report_id)
    elif report_type == 'section':
        report = get_object_or_404(SectionReportForm, id=report_id)
    else:
        return redirect('public_reports')

    ip = get_client_ip(request)
    if not ReportReaction.objects.filter(report=report, reaction_type=reaction_type, ip_address=ip).exists():
        ReportReaction.objects.create(report=report, reaction_type=reaction_type, ip_address=ip)

    return redirect('public_reports')

def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')


@login_required
def select_shift(request):
    today = timezone.now().date()
    employee = Attendance_Employee_data.objects.get(user=request.user)
    selected_shift = request.POST.get('shift_type')

    if selected_shift:
        attendance, created = Attendance_Attendance_data.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'check_in_time': None}
        )

        if attendance.check_in_time:
            messages.warning(request, "You cannot change the shift after check-in.")
        else:
            attendance.shift_type = selected_shift
            attendance.save()
            messages.success(request, f"Shift set to {attendance.get_shift_type_display()}")

    else:
        messages.error(request, "Please select a valid shift.")

    return redirect('dashboard')

def calculate_working_hours(diff_hours):
    hours = int(diff_hours)
    minutes = int((diff_hours - hours) * 60)
    return f"{hours} hr {minutes} min"

@login_required
def get_recent_attendance_data(request):
    try:
        employee = Attendance_Employee_data.objects.get(user=request.user)
    except Attendance_Employee_data.DoesNotExist:
        return render(request, 'attendance/error.html', {'message': 'Employee record not found.'})

    today = date.today()

    # Get selected month from GET params
    selected_month = request.GET.get('month')
    if selected_month:
        try:
            selected_date = datetime.strptime(selected_month, "%Y-%m").date()
        except ValueError:
            selected_date = today.replace(day=1)
    else:
        selected_date = today.replace(day=1)

    start_date = selected_date.replace(day=1)
    end_date = (start_date + relativedelta(months=1)) - relativedelta(days=1)

    # Fetch attendance for the selected month
    recent_attendances = Attendance_Attendance_data.objects.filter(
        employee=employee,
        date__range=(start_date, end_date)
    ).order_by('-date')

    for record in recent_attendances:
        if record.check_in_time and record.check_out_time:
            diff_hours = (record.check_out_time - record.check_in_time).total_seconds() / 3600
            record.working_hours_display = calculate_working_hours(diff_hours)
        else:
            record.working_hours_display = "0 hr 0 min"

    # Dropdown options for current + past 2 months
    month_options = []
    for i in range(3):
        dt = today - relativedelta(months=i)
        month_options.append({
            "value": dt.strftime("%Y-%m"),
            "label": dt.strftime("%B %Y")
        })

    context = {
        "recent_attendances": recent_attendances,
        "month_options": month_options,
        "selected_month": selected_date.strftime("%Y-%m"),
    }

    return render(request, 'attendance/attendance_history.html', context)

@login_required
def leave_request_view(request):
    employee = get_object_or_404(Attendance_Employee_data, user=request.user)
    leave_form = LeaveRequestForm()
    
    existing_leave = Attendance_LeaveRequest.objects.filter(employee=employee).order_by('-created_at')
    if request.method == 'POST' and 'leave_request' in request.POST:
        leave_form = LeaveRequestForm(request.POST)
        if leave_form.is_valid():
            leave = leave_form.save(commit=False)
            leave.employee = employee  # ✅ Correct assignment
            leave.save()
            messages.success(request, "Leave request submitted successfully!")
            return redirect('dashboard')  # or wherever you want to redirect

    return render(request, 'attendance/leave_request.html', {'leave_form': leave_form,'existing_leave': existing_leave,})

@login_required
@require_http_methods(["GET"])
def scan_qr_code(request):
    """
    Renders the QR scanner page where employees can scan the office QR code.
    """
    try:
        employee = get_object_or_404(Attendance_Employee_data, user=request.user)
        today = timezone.now().date()

        # Load the scanner instead of generating a QR Code
        qr_code_url = "/media/qr_codes/qr_code_6.png"  # Pre-existing QR Code (physically printed)

        # Check if attendance is already marked today
        try:
            mark_attendance = Attendance_Attendance_data.objects.get(employee=employee, date=today)
            has_checked_in = True
            has_checked_out = mark_attendance.check_out_time is not None
        except Attendance_Attendance_data.DoesNotExist:
            has_checked_in = False
            has_checked_out = False

        context = {
            'employee': employee,
            'has_checked_in': has_checked_in,
            'has_checked_out': has_checked_out,
            'qr_code_url': qr_code_url,  # No QR code generation, just scanner loading
        }
        return render(request, "attendance/qr_code.html", context)

    except Attendance_Employee_data.DoesNotExist:
        messages.error(request, "Employee profile not found. Please contact the administrator.")
        return redirect('logout')


@csrf_exempt
@login_required
@require_http_methods(["POST"])
def process_qr_scan(request):
    """
    Processes the scanned QR code and marks attendance.
    """
    try:
        data = json.loads(request.body)
        qr_data = data.get("qr_data")  # Extract scanned QR code data

        # Validate the QR code (ensure it matches the expected office QR)
        if qr_data != "qr_code_6.png":  # Change this to your actual QR code data
            return JsonResponse({"status": "error", "message": "Invalid QR Code scanned!"})

        employee = get_object_or_404(Attendance_Employee_data, user=request.user)
        today = timezone.now().date()

        # Check if the user has already checked in
        attendance, created = Attendance_Attendance_data.objects.get_or_create(
            employee=employee, date=today,
            defaults={'check_in_time': timezone.now()}
        )

        if not created:
            # If already checked in, mark as check-out
            if not attendance.check_out_time:
                attendance.check_out_time = timezone.now()
                attendance.save()
                send_mail(
                    "Check-Out Confirmation",
                    f"Hello {employee.user.username}, you have checked out at {attendance.check_out_time}.",
                    "admin@yourcompany.com",
                    [employee.user.email]
                )
                return JsonResponse({"status": "success", "message": "Check-out recorded."})
            else:
                return JsonResponse({"status": "error", "message": "Already checked out!"})

        # Send check-in email
        send_mail(
            "Check-In Confirmation",
            f"Hello {employee.user.username}, you have checked in {attendance.check_in_time}.",
            "admin@yourcompany.com",
            [employee.user.email]
        )
        return JsonResponse({"status": "success", "message": "Check-in recorded."})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

    
@csrf_exempt
@login_required
def mark_attendance(request):
    if request.method == "POST":
        try:
            employee = get_object_or_404(Attendance_Employee_data, user=request.user)
            today = timezone.now().date()
            data = request.POST if request.POST else request.json()
            scanned_qr = data.get("qr_data")

            expected_qr_code = f"attendance/{employee.id}/{today}"
            if scanned_qr != expected_qr_code:
                return JsonResponse({"error": "Invalid QR Code!"}, status=400)

            attendance, created = Attendance_Attendance_data.objects.get_or_create(
                employee=employee, date=today,
                defaults={"check_in_time": timezone.now()}
            )

            if created:
                # ✅ First-time check-in
                Attendance_Log.objects.create(employee=employee, action='IN')
                send_attendance_email(employee.user.email, "Check-In", attendance.check_in_time)
                return JsonResponse({"message": "Check-in successful!"})

            elif not attendance.check_out_time:
                # ✅ Check-out
                attendance.check_out_time = timezone.now()
                attendance.save()
                Attendance_Log.objects.create(employee=employee, action='OUT')
                send_attendance_email(employee.user.email, "Check-Out", attendance.check_out_time)
                return JsonResponse({"message": "Check-out successful!"})

            else:
                return JsonResponse({"message": "Attendance already marked!"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

def send_attendance_email(to_email, status, timestamp):
    """Send email notification for check-in/check-out"""
    subject = f"Attendance {status} Confirmation"
    message = f"Dear Employee,\n\nYour {status.lower()} has been recorded at {timestamp.strftime('%Y-%m-%d %H:%M:%S')}.\n\nThank you!"
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email])
        print(f"✅ {status} email sent to {to_email}")
    except Exception as e:
        print(f"⚠ Error sending {status} email: {e}")

def generate_qr_code(qr_data): 
    # Try to get an existing QR code or create a new one
    qr_code, created = QR_Code.objects.get_or_create(
        code=qr_data,
        defaults={"location": "Office"}
    )

    # If the QR code already exists and has an image, return it
    if not created and qr_code.image:
        print(f"✅ QR Code already exists: {qr_code.image.path}")
        return qr_code  

    # Generate a new QR Code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")

    # Save the QR Code image to a buffer
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Define the QR Code filename
    qr_filename = f"qr_code_{qr_code.id}.png"

    # ✅ Save image inside `media/qr_codes/`
    qr_code.image.save(f"qr_codes/{qr_filename}", ContentFile(buffer.getvalue()), save=True)

    print(f"✅ QR Code generated and saved at: {qr_code.image.path}")

    return qr_code

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')
@login_required
def manual_check_in(request):
    user = request.user

    try:
        employee = Attendance_Employee_data.objects.get(user=user)
    except Attendance_Employee_data.DoesNotExist:
        messages.error(request, "Employee record not found.")
        return redirect('dashboard')

    today = now().astimezone(IST).date()  # Ensure correct date in IST
    current_time = now().astimezone(IST)  # Get current IST time

    attendance, created = Attendance_Attendance_data.objects.get_or_create(
        employee=employee,
        date=today,
        defaults={'check_in_time': current_time}  # Set check-in time in IST
    )

    if not created and not attendance.check_in_time:
        attendance.check_in_time = current_time
        attendance.save()
        messages.success(request, "Check-in recorded successfully.")
    elif not created:
        messages.warning(request, "You have already checked in today.")

    return redirect('dashboard')

@login_required
def manual_check_out(request):
    user = request.user

    try:
        employee = Attendance_Employee_data.objects.get(user=user)
    except Attendance_Employee_data.DoesNotExist:
        messages.error(request, "Employee record not found.")
        return redirect('dashboard')

    try:
        today = now().astimezone(IST).date()  # Ensure correct date in IST
        current_time = now().astimezone(IST)  # Get current IST time

        attendance = Attendance_Attendance_data.objects.get(employee=employee, date=today)

        if not attendance.check_out_time:
            attendance.check_out_time = current_time
            attendance.save()
            messages.success(request, "Check-out recorded successfully.")
        else:
            messages.warning(request, "You have already checked out today.")
    except Attendance_Attendance_data.DoesNotExist:
        messages.error(request, "No check-in record found for today.")

    return redirect('dashboard')

@login_required
def employee_payroll_view(request):
    payroll = Payroll_Payments.objects.filter(employee=request.user.attendance_employeedata).order_by('-year', '-month')
    return render(request, "payroll/employee_payroll.html", {"payroll": payroll})

@staff_member_required
def admin_payroll_view(request):
    payrolls = Payroll_Payments.objects.all().order_by('-year', '-month')
    return render(request, "payroll/admin_payroll.html", {"payrolls": payrolls})

@login_required
def employee_dashboard(request):
    """Render the employee dashboard"""
    return render(request, "dashboard.html")

@login_required
def get_salary_details(request):
    try:
        employee = Attendance_Employee_data.objects.get(user=request.user)
    except Attendance_Employee_data.DoesNotExist:
        return render(request, "salarydetails.html", {
            "error": "No employee record found for this user"
        })

    today = date.today()
    start_of_month = today.replace(day=1)

    attendance_records = Attendance_Attendance_data.objects.filter(
        employee=employee, date__range=(start_of_month, today)
    )
    present_days = attendance_records.filter(status__iexact="present").count()

    salary_data = Payroll_Salary.objects.filter(employee=employee).first()
    if salary_data:
        per_day_salary = salary_data.base_salary / 26
        total_salary = round(present_days * per_day_salary, 2)
    else:
        total_salary = 0

    context = {
        "present_days": present_days,
        "total_salary": total_salary,
        "base_salary": salary_data.base_salary if salary_data else 0,
        "employee": employee
    }

    return render(request, "attendance/salarydetails.html", context)


@login_required
def monthly_attendance_view(request, year=None, month=None):
    user = request.user
    employee = Attendance_Employee_data.objects.get(user=user)

    # Defaults to current month/year if not provided
    today = datetime.today()
    if not year or not month:
        year = today.year
        month = today.month

    num_days = monthrange(year, month)[1]
    month_start = datetime(year, month, 1).date()
    month_end = datetime(year, month, num_days).date()

    daily_data = []

    for day in range(1, num_days + 1):
        current_date = datetime(year, month, day).date()
        weekday = current_date.strftime('%A')
        
        # Check for leave
        leave = Attendance_LeaveRequest.objects.filter(
            employee=employee,
            from_date__lte=current_date,
            to_date__gte=current_date,
            status='approved'
        ).first()

        # Check for attendance
        attendance = Attendance_Attendance_data.objects.filter(
            employee=employee,
            date=current_date
        ).first()

        status = "Absent"
        working_hours = None

        if leave:
            status = "Leave"
        elif current_date.weekday() == 6:  # Sunday
            status = "Holiday"
        elif attendance and attendance.check_in_time and attendance.check_out_time:
            duration = attendance.check_out_time - attendance.check_in_time
            total_seconds = duration.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            working_hours = f"{hours} hrs {minutes} mins"
            status = "Present"

        daily_data.append({
            "date": current_date,
            "day": weekday,
            "status": status,
            "working_hours": working_hours
        })

    context = {
        "daily_data": daily_data,
        "selected_month": datetime(year, month, 1).strftime('%B %Y')
    }
    return render(request, 'attendance/monthly_attendance.html', context)

def logout(request):
    request.session.flush()
    response = redirect('index')
    response.delete_cookie('adminid')
    return response


def custom_admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        # Only allow staff or superusers
        if user is not None and (user.is_staff or user.is_superuser):
            login(request, user)
            return redirect('custom_admin_dashboard')
        else:
            messages.error(request, 'Invalid credentials or not authorized.')

    return render(request, 'layouts/admin_login.html')


def admin_dashboard_view(request):
    return render(request, 'layouts/admin_dashboard.html')


@login_required
def employee_data_view(request):
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', 'all')  # Default to 'all'
    employees = Attendance_Employee_data.objects.select_related('user').all().order_by('user__first_name')
    if query:
        employees = employees.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    if status == 'active':
        employees = employees.filter(is_active=True)
    elif status == 'inactive':
        employees = employees.filter(is_active=False)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        employee_data = [{
            'name': employee.user.get_full_name(),
            'employee_id': employee.employee_id,  # Match frontend expectation
            'department': employee.department or 'Not set',
            'position': employee.position or 'Not set',
            'phone': employee.phone_number or 'Not set',
            'employment_type': employee.get_employment_type_display() or 'Not set',
            'is_active': employee.is_active,  # Match frontend 'is_active' for status badge
            'edit_url': reverse('edit_employees', args=[employee.id])  # Add edit_url for frontend
        } for employee in employees]
        return JsonResponse({'employees': employee_data})

    # Render the template for non-AJAX requests
    context = {
        'employees': employees,
        'query': query,
    }
    return render(request, 'layouts/employee_data.html', context)


@login_required
def edit_employee(request, pk):
    employee = get_object_or_404(Attendance_Employee_data, pk=pk)

    if request.method == 'POST':  # ✅ Fixed typo here
        # ✅ Use request.POST not request
        employee.user.first_name = request.POST.get('first_name')
        employee.user.last_name = request.POST.get('last_name')
        employee.user.save()

        employee.department = request.POST.get('department')
        employee.position = request.POST.get('position')
        employee.phone_number = request.POST.get('phone_number')
        employee.employment_type = request.POST.get('employment_type')
        employee.is_active = True if request.POST.get('is_active') == 'on' else False

        employee.save()
        return redirect('employee_data')

    return render(request, 'layouts/edit_employee_data.html', {'employee': employee})

@login_required
def delete_employee(request, pk):
    employee = get_object_or_404(Attendance_Employee_data, pk=pk)
    if request.method == 'POST':
        employee.delete()
        return redirect('employee_data')  # Redirect to the employee list or summary page
    return render(request, 'layouts/delete_employee.html', {'employee': employee})

import logging


@login_required
def edit_attendance(request, pk):
    attendance = get_object_or_404(Attendance_Attendance_data, pk=pk)

    if request.method == 'POST':
        # Parse and update date
        date_str = request.POST.get('date')
        if date_str:
            attendance.date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Parse check_in_time (datetime-local input to aware datetime)
        check_in = request.POST.get('check_in_time')
        if check_in:
            dt = datetime.fromisoformat(check_in)
            attendance.check_in_time = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        else:
            attendance.check_in_time = None

        # Parse check_out_time
        check_out = request.POST.get('check_out_time')
        if check_out:
            dt = datetime.fromisoformat(check_out)
            attendance.check_out_time = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
        else:
            attendance.check_out_time = None

        # Shift type and status
        attendance.shift_type = request.POST.get('shift_type', attendance.shift_type)
        attendance.status = request.POST.get('status', attendance.status)

        # Notes
        attendance.notes = request.POST.get('notes', '').strip()

        # Working hours (decimal)
        working_hours = request.POST.get('working_hours')
        if working_hours:
            try:
                attendance.working_hours = float(working_hours)
            except ValueError:
                attendance.working_hours = None
        else:
            attendance.working_hours = None

        # Overtime hours (decimal)
        overtime_hours = request.POST.get('overtime_hours')
        if overtime_hours:
            try:
                attendance.overtime_hours = float(overtime_hours)
            except ValueError:
                attendance.overtime_hours = 0
        else:
            attendance.overtime_hours = 0

        # Save updated attendance record
        attendance.save()

        return redirect('attendance_data')  # Adjust redirect URL name as per your URLs

    # GET request: provide choices for dropdowns
    shift_choices = Attendance_Attendance_data._meta.get_field('shift_type').choices
    status_choices = Attendance_Attendance_data._meta.get_field('status').choices

    return render(request, 'layouts/update_attendance.html', {
        'attendance': attendance,
        'shift_choices': shift_choices,
        'status_choices': status_choices,
    })




@login_required
def add_attendance(request):
    employees = Attendance_Employee_data.objects.all()
    shift_choices = Attendance_Attendance_data._meta.get_field('shift_type').choices
    status_choices = Attendance_Attendance_data._meta.get_field('status').choices

    if request.method == 'POST':
        employee_id = request.POST.get('employee')
        date_str = request.POST.get('date')
        check_in_str = request.POST.get('check_in_time')
        check_out_str = request.POST.get('check_out_time')
        shift_type = request.POST.get('shift_type')
        status = request.POST.get('status')
        working_hours = request.POST.get('working_hours')
        overtime_hours = request.POST.get('overtime_hours')

        try:
            employee = Attendance_Employee_data.objects.get(pk=employee_id)
            date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # ✅ Prevent duplicate attendance
            if Attendance_Attendance_data.objects.filter(employee=employee, date=date).exists():
                messages.error(request, f"Attendance already exists for {employee.user.get_full_name()} on {date}")
                return redirect('add_attendance')

            attendance = Attendance_Attendance_data(employee=employee, date=date)

            if check_in_str:
                dt = datetime.fromisoformat(check_in_str)
                attendance.check_in_time = timezone.make_aware(dt) if timezone.is_naive(dt) else dt

            if check_out_str:
                dt = datetime.fromisoformat(check_out_str)
                attendance.check_out_time = timezone.make_aware(dt) if timezone.is_naive(dt) else dt

            attendance.shift_type = shift_type
            attendance.status = status

            try:
                attendance.working_hours = float(working_hours) if working_hours else None
            except ValueError:
                attendance.working_hours = None

            try:
                attendance.overtime_hours = float(overtime_hours) if overtime_hours else 0
            except ValueError:
                attendance.overtime_hours = 0

            attendance.save()
            messages.success(request, "Attendance added successfully.")
            return redirect('attendance_data')

        except Attendance_Employee_data.DoesNotExist:
            messages.error(request, "Employee not found.")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")

    return render(request, 'layouts/add_attendance.html', {
        'employees': employees,
        'shift_choices': shift_choices,
        'status_choices': status_choices,
    })



@login_required
def display_leaverequest(request):
    leavereq = Attendance_LeaveRequest.objects.all().order_by('-created_at')
    
    # Search by employee name
    search_query = request.GET.get('q', '')
    if search_query:
        leavereq = leavereq.filter(
            Q(employee__user__first_name__icontains=search_query) |
            Q(employee__user__last_name__icontains=search_query)
        )
    
    # Filter by leave type and status
    leave_type = request.GET.get('leave_type', '')
    status = request.GET.get('status', '')
    
    if leave_type:
        leavereq = leavereq.filter(leave_type=leave_type)
    if status:
        leavereq = leavereq.filter(status=status)
    
    # Define choices for template
    LEAVE_TYPE_CHOICES = [
        ('SICK', 'Sick Leave'),
        ('CASUAL', 'Casual Leave'),
        ('EMERGENCY', 'Emergency Leave'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]
    
    context = {
        'leavereq': leavereq,
        'leave_type_choices': LEAVE_TYPE_CHOICES,
        'status_choices': STATUS_CHOICES,
    }
    
    return render(request, 'layouts/list_leaverequest.html', context)

@login_required
def individual_leave_requests(request, user_id):
    leavereq = Attendance_LeaveRequest.objects.filter(employee__user__id=user_id)
    employee_name = leavereq.first().employee.user.get_full_name() if leavereq.exists() else "Unknown"
    
    # Filter by leave type and status
    leave_type = request.GET.get('leave_type', '')
    status = request.GET.get('status', '')
    
    if leave_type:
        leavereq = leavereq.filter(leave_type=leave_type)
    if status:
        leavereq = leavereq.filter(status=status)
    
    # Define choices for template
    LEAVE_TYPE_CHOICES = [
        ('SICK', 'Sick Leave'),
        ('CASUAL', 'Casual Leave'),
        ('EMERGENCY', 'Emergency Leave'),
        ('OTHER', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DENIED', 'Denied'),
    ]
    
    context = {
        'leavereq': leavereq,
        'employee_name': employee_name,
        'leave_type_choices': LEAVE_TYPE_CHOICES,
        'status_choices': STATUS_CHOICES,
        'user_id': user_id,  # Pass user_id to template
    }
    
    return render(request, 'layouts/individual_leave_list.html', context)


def edit_leave_request(request,pk):
    leave=get_object_or_404(Attendance_LeaveRequest,pk=pk)
    if request.method=='POST':
        leave.status=request.POST.get('status')
        leave.admin_reply=request.POST.get('admin_reply')
        leave.save()  
        
        return redirect('display_leaverequest')
    STATUS_CHOICES=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Denied', 'Denied'),
    ]
    context={
        'leave':leave,
        'status_choices':STATUS_CHOICES
    }
    return render(request, 'layouts/edit_leaverequest.html', context)

def emp_count(requset):
    employee_count=Attendance_Employee_data.objects.count() 
    return render(request,'layouts/admin_dashboard.html',{'employee_count':employee_count})


def custom_admin_dashboard(request):
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('admin_login')

    employee_count = Attendance_Employee_data.objects.count()
    pending_leave_count = Attendance_LeaveRequest.objects.filter(status='Pending').count()

    today = timezone.now().date()
    six_days_ago = today - timedelta(days=5)

    recent_attendance = Attendance_Attendance_data.objects.select_related(
        'employee', 'employee__user'
    ).filter(
        date__range=(six_days_ago, today)
    ).order_by('-date')  # remove [:10] if you want *all* from last 6 days

    recent_leavereq = Attendance_LeaveRequest.objects.select_related(
        'employee', 'employee__user'
    ).filter(
        from_date__range=(six_days_ago, today)
    ).order_by('-from_date')

    return render(request, 'layouts/admin_dashboard.html', {
        'employee_count': employee_count,
        'pending_leave_count': pending_leave_count,
        'recent_attendance': recent_attendance,
        'recent_leavereq': recent_leavereq,
    })



logger = logging.getLogger(__name__)
@login_required
def employee_attendance(request):
    today = timezone.now().date()

    # Get filter parameters
    filter_type = request.GET.get('filter_type', 'month')
    custom_date = request.GET.get('custom_date')
    selected_month = request.GET.get('selected_month')
    selected_year = request.GET.get('selected_year')

    # Initialize date range
    start_date = today
    end_date = today

    # Define months for dropdown
    months = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]

    # Define years for dropdown
    current_year = today.year
    years = list(range(current_year - 5, current_year + 1))

    # Determine filtering range
    if filter_type == 'today':
        start_date = today
        end_date = today
    elif filter_type == 'past_7_days':
        start_date = today - timezone.timedelta(days=7)
        end_date = today
    elif filter_type == 'month':
        try:
            month = int(selected_month) if selected_month else today.month
            year = int(selected_year) if selected_year else today.year
            start_date = date(year, month, 1)
            end_date = date(year, month, monthrange(year, month)[1])
        except (ValueError, TypeError):
            start_date = date(today.year, today.month, 1)
            end_date = date(today.year, today.month, monthrange(today.year, today.month)[1])
    elif filter_type == 'year':
        start_date = date(today.year, 1, 1)
        end_date = date(today.year, 12, 31)
    elif filter_type == 'custom' and custom_date:
        try:
            custom_date = date.fromisoformat(custom_date)
            start_date = custom_date
            end_date = custom_date
        except ValueError:
            start_date = date(today.year, today.month, 1)
            end_date = date(today.year, today.month, monthrange(today.year, today.month)[1])
    else:
        start_date = date(today.year, today.month, 1)
        end_date = date(today.year, today.month, monthrange(today.year, today.month)[1])

    logger.debug(f"Filter type: {filter_type}, Start date: {start_date}, End date: {end_date}")

    # Fetch attendance records ordered by date and check-in time
    attendance_qs = Attendance_Attendance_data.objects.select_related('employee', 'employee__user').filter(
        date__range=(start_date, end_date)
    ).order_by('date', 'check_in_time')  # fixed field name

    logger.debug(f"Attendance records found: {attendance_qs.count()}")

    paginator = Paginator(attendance_qs, 25)
    page_number = request.GET.get('page')
    employees = paginator.get_page(page_number)

    return render(request, 'layouts/attendance_data.html', {
        'employees': employees,
        'month_label': start_date.strftime('%B %Y'),
        'filter_type': filter_type,
        'custom_date': custom_date,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'months': months,
        'years': years,
        'start_date': start_date,
        'end_date': end_date,
    })


@login_required
def employee_attendance_detail(request, user_id):
    try:
        employee = Attendance_Employee_data.objects.get(user__id=user_id)
    except Attendance_Employee_data.DoesNotExist:
        return render(request, 'layouts/hh.html', {
            'error_message': f"No employee found for user ID {user_id}. Please check the ID or contact the administrator.",
            'employee': None,
            'attendance_data': [],
            'attendance_records': None,
            'filter_type': 'today',
            'custom_date': '',
            'selected_month': '',
            'selected_year': '',
            'start_date': timezone.now().date(),
            'month_label': 'Today',
            'months': [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)],
            'years': range(2020, timezone.now().year + 1),
        })

    # Get filter parameters from GET request
    filter_type = request.GET.get('filter_type', 'today')
    custom_date = request.GET.get('custom_date', '')
    selected_month = request.GET.get('selected_month', '')
    selected_year = request.GET.get('selected_year', '')

    # Initialize queryset with base filter
    attendance_data = Attendance_Attendance_data.objects.filter(employee=employee)

    # Apply filters based on filter_type
    today = timezone.now().date()
    
    if filter_type == 'today':
        attendance_data = attendance_data.filter(date=today)
        start_date = today
        month_label = "Today"
        attendance_data = attendance_data.order_by('-date')  # Newest first
    elif filter_type == 'past_7_days':
        start_date = today - timedelta(days=6)
        attendance_data = attendance_data.filter(date__range=[start_date, today])
        month_label = "Past 7 Days"
        attendance_data = attendance_data.order_by('date')  # Newest first
    elif filter_type == 'month' and selected_month and selected_year:
        try:
            start_date = datetime(int(selected_year), int(selected_month), 1).date()
            end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(days=1)
            attendance_data = attendance_data.filter(date__range=[start_date, end_date])
            month_label = start_date.strftime("%B %Y")
            attendance_data = attendance_data.order_by('date')  # Oldest first for month
        except ValueError:
            month_label = "Invalid Month/Year"
            attendance_data = attendance_data.none()
    elif filter_type == 'year':
        start_date = today.replace(month=1, day=1)
        attendance_data = attendance_data.filter(date__year=today.year)
        month_label = today.strftime("%Y")
        attendance_data = attendance_data.order_by('-date')  # Newest first
    elif filter_type == 'custom' and custom_date:
        try:
            start_date = datetime.strptime(custom_date, '%Y-%m-%d').date()
            attendance_data = attendance_data.filter(date=start_date)
            month_label = start_date.strftime("%B %d, %Y")
            attendance_data = attendance_data.order_by('-date')  # Newest first
        except ValueError:
            month_label = "Invalid Date"
            attendance_data = attendance_data.none()
    else:
        # Default to today
        attendance_data = attendance_data.filter(date=today)
        start_date = today
        month_label = "Today"
        attendance_data = attendance_data.order_by('-date')  # Newest first

    # Pagination
    paginator = Paginator(attendance_data, 10)  # 10 records per page
    page_number = request.GET.get('page')
    attendance_records = paginator.get_page(page_number)

    # Prepare context
    months = [(i, datetime(2000, i, 1).strftime('%B')) for i in range(1, 13)]
    years = range(2020, today.year + 1)

    context = {
        'employee': employee,
        'attendance_data': attendance_data,
        'attendance_records': attendance_records,
        'filter_type': filter_type,
        'custom_date': custom_date,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'start_date': start_date,
        'month_label': month_label,
        'months': months,
        'years': years,
    }
    return render(request, 'layouts/attendance _individual_employee_data.html', context)


#Announcement


def announcement(request):
    if request.method=='POST':
        tit=request.POST.get('title')
        mes=request.POST.get('message')
        att=request.POST.get('attachment')
        Announcement.objects.create(title=tit,message=mes,attachment=att)
        return HttpResponse("done")
    return render(request,'layouts/admin_announcement.html')