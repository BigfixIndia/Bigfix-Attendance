from datetime import datetime
from io import BytesIO
import json
import os
from urllib import request
from venv import logger
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
from .models import Attendance_LeaveRequest
from .models import Attendance_Log
from datetime import date
from django.utils.timezone import localtime
from .models import Holiday
from operator import itemgetter
from datetime import date, timedelta
from django.contrib.auth.decorators import user_passes_test
from calendar import monthrange
from dateutil.relativedelta import relativedelta




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

            # Get today's attendance for the current user
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
            pass  # Log error or redirect if needed

    all_employees = Attendance_Employee_data.objects.filter(user__isnull=False)

    for employee in all_employees:
        user_obj = employee.user
        record = Attendance_Attendance_data.objects.filter(employee=employee, date=today).first()
        leave = Attendance_LeaveRequest.objects.filter(
            employee=employee,
            from_date__lte=today,
            to_date__gte=today
        ).first()

        # Get shift type for the employee today
        shift_display = record.get_shift_type_display() if record and record.shift_type else "Not Set"

        status = {
            "name": f"{user_obj.first_name} {user_obj.last_name}",
            "check_in": None,
            "check_out": None,
            "color": "",
            "check_in_raw": None,
            "shift": shift_display
        }

        if leave:
            leave_list.append({"employee__name": status["name"]})
        elif record and record.check_in_time:
            check_in_ist = timezone.localtime(record.check_in_time)
            status["check_in"] = check_in_ist.strftime('%I:%M %p')
            status["check_in_raw"] = check_in_ist

            if record.check_out_time:
                check_out_ist = timezone.localtime(record.check_out_time)
                status["check_out"] = check_out_ist.strftime('%I:%M %p')

            if check_in_ist.time() > time(10, 30):
                status["color"] = "text-danger"
            else:
                status["color"] = "text-success"

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

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        employee_form = EmployeeRegistrationForm(request.POST, request.FILES)
        
        if user_form.is_valid() and employee_form.is_valid():
            user = user_form.save()
            employee = employee_form.save(commit=False)
            employee.user = user
            employee.save()
            
            username = user_form.cleaned_data.get('username')
            password = user_form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            user_login(request)
            
            messages.success(request, f"Account created for {username}. You are now logged in.")
            return redirect('dashboard')
    else:
        user_form = UserRegistrationForm()
        employee_form = EmployeeRegistrationForm()
    
    return render(request, 'attendance/register.html', {
        'user_form': user_form,
        'employee_form': employee_form
    })

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

    # ✅ Get today's attendance record
    mark_attendance = Attendance_Attendance_data.objects.filter(employee=employee, date=today).first()
    has_checked_in = bool(mark_attendance and mark_attendance.check_in_time)
    has_checked_out = bool(mark_attendance and mark_attendance.check_out_time)

    # ✅ Attendance logs
    today_logs = Attendance_Log.objects.filter(employee=employee, timestamp__date=today).order_by('timestamp')

    # ✅ Leave request handling
    leave_form = LeaveRequestForm()
    if request.method == 'POST' and 'leave_request' in request.POST:
        leave_form = LeaveRequestForm(request.POST)
        if leave_form.is_valid():
            leave = leave_form.save(commit=False)
            leave.employee = employee
            leave.save()
            messages.success(request, 'Leave request submitted successfully!')
            return redirect('dashboard')

    # ✅ Handle shift selection before check-in
    elif request.method == 'POST' and 'set_shift' in request.POST:
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

    # ✅ Working hours display
    working_hours_display = None
    if has_checked_in and has_checked_out:
        time_diff = (mark_attendance.check_out_time - mark_attendance.check_in_time).total_seconds() / 3600
        working_hours_display = calculate_working_hours(time_diff)

    # ✅ Monthly attendance summary
    selected_month = request.GET.get('month')
    today = date.today()
    selected_date = datetime.strptime(selected_month, "%Y-%m").date() if selected_month else today.replace(day=1)
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

    # ✅ Announcements
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]
    read_announcements = AnnouncementRead.objects.filter(user=request.user).values_list('announcement_id', flat=True)
    for ann in announcements:
        ann.is_read = ann.id in read_announcements
    unread_announcements = [ann for ann in announcements if not ann.is_read]
    for ann in unread_announcements:
        AnnouncementRead.objects.create(user=request.user, announcement=ann)

    # ✅ Month dropdown options
    month_options = [
        {"value": (today - relativedelta(months=i)).strftime("%Y-%m"),
         "label": (today - relativedelta(months=i)).strftime("%B %Y")}
        for i in range(3)
    ]

    # ✅ Shift display logic
    shift_display = mark_attendance.get_shift_type_display() if mark_attendance and mark_attendance.shift_type else "Not Set"

    # ✅ Context to template
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
        'selected_month': selected_month or today.strftime("%Y-%m"),
        'shift_display': shift_display,
    }

    return render(request, 'attendance/dashboard.html', context)

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

#@login_required
#def calendar_page(request):
    # Fetch all events (Holidays and Workdays) here and pass them to the template
 #   employee = Attendance_Employee_data.objects.get(user=request.user)
  #  events = []

    # Holidays
   # for holiday in Holiday.objects.all():
    #       'title': holiday.title,
     #       'start': str(holiday.date),
      #      'color': '#dc3545'  # Red for Holidays
      #  })

    # Workdays (if needed)
    #workdays = Attendance_Attendance_data.objects.filter(employee=employee, status='Present')
    #for day in workdays:
     #   events.append({
      #      'title': 'Work Day',
       #     'start': str(day.date),
        #    'color': '#198754'  # Green for Workdays
   #     })

    # Pass events to the calendar page template
    #context = {
     #   'events': events
    #}

    #return render(request, 'attendance/calendar.html', context) %

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

