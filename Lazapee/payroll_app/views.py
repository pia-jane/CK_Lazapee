from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Employee, Payslip, Account
from django.contrib.auth.hashers import make_password, check_password
from django import forms
from decimal import Decimal

# Create your views here.

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        
        try:
            account = Account.objects.get(username=username)
            if check_password(password1, account.password1):
                request.session['user.id'] = account.pk
                return redirect('payroll')
            else:
                messages.error(request, "Invalid login. Username does not match Password.")
        except Account.DoesNotExist:
            messages.error(request, "Invalid login. Account does not exist.")
    
    return render(request, 'payroll_app/login.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        if Account.objects.filter(username=username).exists():
            messages.error(request, "Account already exists.")
        elif password1 != password2:
            messages.error(request, "Passwords do not match.")
        else:
            hashed_pw = make_password(password1)
            Account.objects.create(username=username, password1=hashed_pw)
            messages.success(request, "Account created successfully.")
            return redirect('login')
    
    return render(request, 'payroll_app/signup.html')

def payroll(request):
   user_id = request.session.get('user.id')
   if not user_id:
        return redirect('login')
   
   user = get_object_or_404(Account, pk=user_id)
   employee = Employee.objects.all()
   return render(request, 'payroll_app/payroll.html', {'employee': employee})

def delete_employee(request, pk):
    if request.session.get('user.id'):
        Employee.objects.filter(pk=pk).delete()
    return redirect('payroll')

def add_overtime(request, pk):
   user_id = request.session.get('user.id')
   if not user_id:
        return redirect('login')
   
   employee = get_object_or_404(Employee, pk=pk)
   
   try:
    overtime_hours = Decimal(request.POST.get('overtime_hours', '0'))
    overtime_pay = (employee.rate / Decimal('160')) * Decimal('1.5') * overtime_hours
    existing_overtime_pay = employee.overtime_pay or Decimal('0')
    if not isinstance(existing_overtime_pay, Decimal):
        existing_overtime_pay = Decimal(str(existing_overtime_pay))
    employee.overtime_pay = existing_overtime_pay + overtime_pay
    employee.save()
    messages.success(request, f"Overtime of {overtime_pay:.2f} added for {employee.name}.")
   except (ValueError):
       messages.error(request, "Invalid overtime hours.")
   return redirect('payroll')

def add_employee(request):
    user_id = request.session.get('user.id')
    if not user_id:
        return redirect('login')
    
    account = get_object_or_404(Account, pk=user_id)

    if request.method == "POST":
        name = request.POST.get('name')
        id_number = request.POST.get('id_number')
        rate =  request.POST.get('rate')
        allowance = request.POST.get('allowance')

        allowance = allowance if allowance else None

        if Employee.objects.filter(account=account, id_number=id_number).exists():
            messages.error(request, f"Employee with ID number '{id_number}' already exists.")
            return render(request, 'payroll_app/add_employee.html')
    
        Employee.objects.create(account=account, name=name, id_number=id_number, rate=rate, allowance=allowance)
        return redirect('payroll')
    
    return render(request, 'payroll_app/add_employee.html')

def update_employee(request, pk):
    user_id = request.session.get('user.id')
    if not user_id:
        return redirect('login')
    
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == "POST":
        employee.name = request.POST.get('name')
        employee.id_number = request.POST.get('id_number')
        employee.rate = request.POST.get('rate')
        allowance = request.POST.get('allowance')
        employee.allowance = allowance if allowance else None
        employee.save()
        return redirect('payroll')
    
    return render(request, 'payroll_app/update_employee.html', {'employee': employee})

def logout(request):
    request.session.flush()
    return redirect("login")

def payslip(request):
    employees = Employee.objects.all()
    payslips = Payslip.objects.all()

    if request.method == 'POST':
        selected = request.POST.get('payslip_name')
        month = int(request.POST.get('month'))
        year = request.POST.get('year')
        cycle  = request.POST.get('pay_cycle')

        date_range='1-15' if cycle == '1' else '16-30'

        if selected == 'all':
            payslip_for = employees
        else:
            try:
                selected_employee = Employee.objects.get(id=selected)
                payslip_for = [selected_employee]
            except Employee.DoesNotExist:
                messages.error(request, "Selected employee does not exist.")
                return redirect('payslip')

        for employee in payslip_for:
            if Payslip.objects.filter(id_number=employee, month=month, year=year, pay_cycle=cycle).exists():
                messages.warning(request, f"Payslip already exists for {employee.name} - {month}/{year}, Cycle {cycle}")
                continue
            
            emp_rate = Decimal(employee.rate)
            allowance = Decimal(employee.allowance if employee.allowance is not None else 0)
            overtime = Decimal(employee.overtime_pay if employee.overtime_pay is not None else 0)
            
            base_rate = emp_rate / Decimal(2)
            temp_pay = base_rate + allowance + overtime

            
            if cycle == "1":
                pag_ibig = Decimal(100)
                philhealth = Decimal(0)
                sss = Decimal(0)
            elif cycle == "2":
                pag_ibig = Decimal(0)
                philhealth = emp_rate * Decimal(0.04)
                sss = emp_rate * Decimal(0.045)
            else:
                pag_ibig = philhealth = sss = Decimal(0)

            deductions = pag_ibig + philhealth + sss
            tax = (base_rate + allowance + overtime - deductions) * Decimal(0.2)
            
            total_pay = (base_rate + allowance + overtime) - deductions - tax

            Payslip.objects.create(
                id_number=employee,
                month=month,
                date_range=date_range,
                year=year,
                pay_cycle=cycle,
                rate=emp_rate,
                earnings_allowance=allowance,
                deductions_tax=tax,
                deductions_health=philhealth,
                pag_ibig=pag_ibig,
                sss=sss,
                overtime=overtime,
                total_pay=total_pay
            )

            employee.overtime_pay = Decimal(0)
            employee.save()

            messages.success(request, "Payslip(s) created successfully.")
        return redirect('payslip')

    return render(request, 'payroll_app/payslip.html', {
        'employee': employees,
        'payslip': payslips,
    })

def view_payslip(request, pk):
    payslip = get_object_or_404(Payslip, pk=pk)
    return render(request, 'payroll_app/view_payslip.html', {'payslip': payslip})

def manage_account(request):
   user_id = request.session.get('user.id')
   if not user_id:
        return redirect('login')
   
   user = get_object_or_404(Account, pk=user_id)
   return render(request, 'payroll_app/manage_account.html', {'user':user})

def change_password(request):
    user_id = request.session.get('user.id')
    if not user_id:
        return redirect("login")

    user = get_object_or_404(Account, pk=user_id)

    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")
        confirm_password = request.POST.get("confirm_password")

        if not check_password(current_password, user.password1):
            messages.error(request, "Incorrect current password.")
            return redirect("change_password")

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
            return redirect("change_password")

        user.password1 = make_password(new_password)
        user.save()
        messages.success(request, "Password changed successfully!")
        return redirect("manage_account")

    return render(request, "payroll_app/change_password.html", {'user': user})

def delete_account(request, pk):
    user = get_object_or_404(Account, pk=pk)
    user.delete()
    messages.success(request, "Account deleted successfully")
    return redirect('login')