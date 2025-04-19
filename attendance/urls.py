from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth import login, authenticate
from . import views 
from django.conf import settings
from django.conf.urls.static import static
 

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('scan-qr/', views.scan_qr_code, name='scan_qr_code'),
    path("process_qr/", views.process_qr_scan, name="process_qr_scan"),  
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('generate_qr_code/', views.generate_qr_code, name='generate_qr_code'),
    path('admin_attendance_view/', views.admin_attendance_view, name='admin_attendance'),
    path('fetch_attendance_data/', views.fetch_attendance_data, name='fetch_attendance_data'),
    path('manual-checkin/', views.manual_check_in, name='manual_checkin'),
    path('manual-checkout/', views.manual_check_out, name='manual_checkout'),
    path("payroll/employee/", views.employee_payroll_view, name="employee_payroll"),
    path("payroll/admin/", views.admin_payroll_view, name="admin_payroll"),
    path("employee_dashboard/", views.employee_dashboard, name="employee_dashboard"),
    path('dashboard_view/', views.dashboard_view, name='dashboard_view'),
    path("get_salary_details/", views.get_salary_details, name="get_salary_details"),  # New API endpoint
    path('dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('admin/announcements/', views.admin_dashboard, name='admin_announcements'),
    path('leave_request_view/', views.leave_request_view, name='leave_request_view'),
    path('calendar_page/', views.calendar_page, name='calendar_page'),

    #path("admin/download-salary-slip/<int:salary_id>/", views.download_salary_slip, name="download_salary_slip"),
    #path('logout/', views.logout, name='logout'),

    # Authentication URLs
    path('accounts/', include('django.contrib.auth.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='attendance/login.html'), name='login'),
    path('user_login/', auth_views.LoginView.as_view(template_name='attendance/login.html'), name='user_login'),
    path('admin-login/', auth_views.LoginView.as_view(template_name='admin_login.html'), name='admin_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]

# ✅ Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)