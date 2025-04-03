from django.contrib import admin
from django.utils.timezone import localtime
from django.utils.html import format_html
from .models import Attendance_Attendance_data, Payroll_Salary, Payroll_Payments  # Ensure correct imports


@admin.register(Attendance_Attendance_data)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'formatted_checkin', 'formatted_checkout', 'date', 'status', 'working_hours', 'overtime_hours')
    ordering = ('date', 'check_in_time')  
    list_filter = ('date', 'status')

    def formatted_checkin(self, obj):
        return localtime(obj.check_in_time).strftime('%Y-%m-%d %H:%M:%S') if obj.check_in_time else "Not Checked In"
    formatted_checkin.short_description = "Check-in Time"

    def formatted_checkout(self, obj):
        return localtime(obj.check_out_time).strftime('%Y-%m-%d %H:%M:%S') if obj.check_out_time else "Not Checked Out"
    formatted_checkout.short_description = "Check-out Time"

    def colored_status(self, obj):
        """ Display colored status for better visibility """
        if obj.check_in_time and obj.check_out_time:
            return format_html('<span style="color:green;">Present</span>')
        elif obj.check_in_time:
            return format_html('<span style="color:orange;">Checked In</span>')
        return format_html('<span style="color:red;">Absent</span>')
    colored_status.short_description = "Status"

# Register Payroll Salary Admin
@admin.register(Payroll_Salary)
class PayrollSalaryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'base_salary', 'overtime_rate', 'bonus', 'deductions', 'calculate_net_salary')
    search_fields = ('employee__user__first_name', 'employee__user__last_name')
    list_filter = ('employee',)

    def calculate_net_salary(self, obj):
        """ Compute Net Salary """
        return obj.base_salary + obj.bonus - obj.deductions

    calculate_net_salary.short_description = "Net Salary"

# Register Payroll Payments Admin
@admin.register(Payroll_Payments)
class PayrollPaymentsAdmin(admin.ModelAdmin):
    list_display = ('employee', 'month', 'year', 'net_salary', 'get_payment_status')  # ✅ Use correct fields
    search_fields = ('employee__user__first_name', 'employee__user__last_name')
    list_filter = ('month', 'year')

    def get_payment_status(self, obj):
        """ Custom method to determine if salary is paid """
        return "Paid" if obj.net_salary > 0 else "Unpaid"
    
    get_payment_status.short_description = "Payment Status"