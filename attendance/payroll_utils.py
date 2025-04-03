from .models import Payroll_Salary, Payroll_Payments, Attendance_Attendance_data
from django.db.models import Sum

def calculate_payroll(employee, month, year):
    attendance_records = Attendance_Attendance_data.objects.filter(
        employee=employee, date__month=month, date__year=year
    )
    
    total_present_days = attendance_records.filter(status='present').count()
    total_overtime_hours = attendance_records.aggregate(Sum('overtime_hours'))['overtime_hours__sum'] or 0
    
    salary_details = Payroll_Salary.objects.get(employee=employee)
    
    net_salary = (salary_details.base_salary / 30 * total_present_days)  # Daily rate
    net_salary += total_overtime_hours * salary_details.overtime_rate  # Overtime
    net_salary += salary_details.bonus
    net_salary -= salary_details.deductions
    
    # Save payroll details
    Payroll_Payments.objects.update_or_create(
        employee=employee,
        month=month,
        year=year,
        defaults={
            "total_working_days": 30,  # Assume 30 for now
            "total_present_days": total_present_days,
            "total_overtime_hours": total_overtime_hours,
            "net_salary": net_salary
        }
    )
