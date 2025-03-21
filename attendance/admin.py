from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import localtime
from .models import Attendance_Attendance_data

class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'check_in_time', 'check_out_time', 'date', 'status', 'working_hours')
    ordering = ('date', 'check_in_time')  # ✅ Use 'date' instead of 'attendance_date'
    list_filter = ('date', 'status')  # ✅ Use 'date' instead of 'attendance_date'



    def formatted_checkin(self, obj):
        """ Display check-in time in a readable format """
        return localtime(obj.checkin_time).strftime('%Y-%m-%d %H:%M:%S') if obj.checkin_time else "Not Checked In"
    formatted_checkin.short_description = "Check-in Time"

    def formatted_checkout(self, obj):
        """ Display check-out time in a readable format """
        return localtime(obj.checkout_time).strftime('%Y-%m-%d %H:%M:%S') if obj.checkout_time else "Not Checked Out"
    formatted_checkout.short_description = "Check-out Time"

    def status(self, obj):
        """ Display status based on check-in and check-out """
        if obj.checkin_time and obj.checkout_time:
            return format_html('<span style="color:green;">Present</span>')
        elif obj.checkin_time:
            return format_html('<span style="color:orange;">Checked In</span>')
        return format_html('<span style="color:red;">Absent</span>')
    status.short_description = "Status"

admin.site.register(Attendance_Attendance_data, AttendanceAdmin)

