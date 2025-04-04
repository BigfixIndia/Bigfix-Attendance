from datetime import datetime
from io import BytesIO
import json
import os
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

from .models import  Attendance_Employee_data, Attendance_Attendance_data, QR_Code
from .forms import UserRegistrationForm, EmployeeRegistrationForm
from .utils import generate_qr_code
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def admin_dashboard(request):
    today = datetime.today().strftime('%Y-%m-%d')
    employees = Attendance_Employee_data.objects.all()
    attendance_records = Attendance_Attendance_data.objects.all()
    context = {
        "employees": employees,
        "attendance_records": attendance_records,
        "today": today
    }
    return render(request, "admin_dashboard.html", context)

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

@csrf_exempt
@login_required
def dashboard(request):
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])  # Return a 405 response if not GET
    # Check if the employee profile exists
    if not Attendance_Employee_data.objects.filter(user=request.user).exists():
        messages.error(request, "No employee profile found. Please contact HR.")
        return redirect('home')  # Redirect to a safe page instead of logout
    
    # Get employee object
    employee = get_object_or_404(Attendance_Employee_data, user=request.user)
    
    # Get today's date
    today = timezone.now().date()

    # Check today's attendance
    today_attendance = Attendance_Attendance_data.objects.filter(employee=employee, date=today).first()
    has_checked_in = today_attendance is not None
    has_checked_out = today_attendance.check_out_time is not None if today_attendance else False

    # Get recent attendance records
    recent_attendances = Attendance_Attendance_data.objects.filter(employee=employee).order_by('-date')[:7]

    # Prepare context
    context = {
        'employee': employee,
        'today_attendance': today_attendance,
        'has_checked_in': has_checked_in,
        'has_checked_out': has_checked_out,
        'recent_attendances': recent_attendances,
    }

    return render(request, 'attendance/dashboard.html', context)

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
            today_attendance = Attendance_Attendance_data.objects.get(employee=employee, date=today)
            has_checked_in = True
            has_checked_out = today_attendance.check_out_time is not None
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
            f"Hello {employee.user.username}, you have checked in at {attendance.check_in_time}.",
            "admin@yourcompany.com",
            [employee.user.email]
        )
        return JsonResponse({"status": "success", "message": "Check-in recorded."})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})

    
@csrf_exempt
@login_required
def mark_attendance(request):
    """
    API to mark employee attendance when QR code is scanned and send email confirmation.
    """
    if request.method == "POST":
        try:
            employee = get_object_or_404(Attendance_Employee_data, user=request.user)
            today = timezone.now().date()
            data = request.POST if request.POST else request.json()
            scanned_qr = data.get("qr_data")

            # Get the correct office QR code
            expected_qr_code = f"attendance/{employee.id}/{today}"

            if scanned_qr != expected_qr_code:
                return JsonResponse({"error": "Invalid QR Code!"}, status=400)

            # Get or create attendance record
            attendance, created = Attendance_Attendance_data.objects.get_or_create(
                employee=employee, date=today,
                defaults={"check_in_time": timezone.now()}
            )

            if created:
                # ✅ Check-in
                send_attendance_email(employee.user.email, "Check-In", attendance.check_in_time)
                return JsonResponse({"message": "Check-in successful!"})

            elif not attendance.check_out_time:
                # ✅ Check-out
                attendance.check_out_time = timezone.now()
                attendance.save()
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
    """Fetch employee salary dynamically when button is clicked"""
    from django.http import JsonResponse
    from datetime import date
    from .models import Attendance_Attendance_data, Payroll_Salary, Attendance_Employee_data

    try:
        employee = Attendance_Employee_data.objects.get(user=request.user)  # Fetch employee instance
    except Attendance_Employee_data.DoesNotExist:
        return JsonResponse({"error": "No employee record found for this user"}, status=400)

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

    return JsonResponse({"present_days": present_days, "total_salary": total_salary})


def logout(request):
    request.session.flush()
    response = redirect('index')
    response.delete_cookie('adminid')
    return response

