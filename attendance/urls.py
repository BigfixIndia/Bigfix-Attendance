from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth import login, authenticate
from . import views 
from django.conf import settings
from django.conf.urls.static import static
 

urlpatterns = [
    path('index/', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('change-profile-picture/', views.change_profile_picture, name='change_profile_picture'),
    path('download-id-card/', views.download_id_card, name='download_id_card'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('select-shift/', views.select_shift, name='select_shift'),
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
    path('calendar/', views.calendar_page, name='calendar_page'),
    path('calendar_events/', views.calendar_events, name='calendar_events'),
    path('get_recent_attendance_data/', views.get_recent_attendance_data, name='get_recent_attendance_data'),
    path('monthly_attendance/<int:year>/<int:month>/', views.monthly_attendance_view, name='monthly_attendance'),

    path('admin_login/', views.custom_admin_login, name='custom_admin_login'),   # admin login
    path('admin_dashboard/', views.custom_admin_dashboard, name='custom_admin_dashboard'),


    path('admin_dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('employee_data/', views.employee_data_view, name='employee_data'),
    path('edit_employees/<str:pk>/', views.edit_employee, name='edit_employees'),
    path('delete_employees/<int:pk>/', views.delete_employee, name='delete_employees'),
    path('attendance_data/', views.employee_attendance, name='attendance_data'),
    path('attendance/edit/<int:pk>/', views.edit_attendance, name='edit_attendance'),
    path('attendance/add/', views.add_attendance, name='add_attendance'),
    path('display_leaverequest/', views.display_leaverequest, name='display_leaverequest'),
    path('employee-leave-requests/<int:user_id>/', views.individual_leave_requests, name='employee_leave_requests'), 
    path('edit_leave_request/<int:pk>/', views.edit_leave_request, name='edit_leave_request'),
    path('employee_attendance/<int:user_id>/', views.employee_attendance_detail, name='employee_attendance_detail'),

    #path("admin/download-salary-slip/<int:salary_id>/", views.download_salary_slip, name="download_salary_slip"),
    #path('logout/', views.logout, name='logout'),

    # Authentication URLs
    path('accounts/', include('django.contrib.auth.urls')),
    path('', auth_views.LoginView.as_view(template_name='attendance/login.html'), name='login'),
    path('user_login/', auth_views.LoginView.as_view(template_name='attendance/login.html'), name='user_login'),

    path('public-reports/', views.public_reports, name='public_reports'),
    path('admin-login/', auth_views.LoginView.as_view(template_name='admin_login.html'), name='admin_login'),
    path('publicreports/', views.public_reports, name='public_reports'),
    path('submit-comment/<int:report_id>/', views.submit_comment, name='submit_comment'),
    path('submit-reaction/<int:report_id>/<str:reaction_type>/', views.submit_reaction, name='submit_reaction'),
    path('admin-login/', auth_views.LoginView.as_view(template_name='admin_login.html'), name='admin_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

]

# ✅ Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)