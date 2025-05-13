from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Employee, Payslip, Account
from django.contrib.auth.hashers import make_password, check_password
from django import forms

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
   employee = Employee.objects.filter(account=user)
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
       overtime_hours = float(request.POST.get('overtime_hours', 0))
       overtime_pay = (employee.rate/160)*1.5*overtime_hours
       employee.overtime_pay = (employee.overtime_pay or 0.0) + overtime_pay
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
    # Check if user is logged in
    user_id = request.session.get('user.id')
    if not user_id:
        return redirect('login')

    user = get_object_or_404(Account, pk=user_id)
    employee = Employee.objects.filter(account=user).first()  # Assuming one employee per account

    if request.method == 'POST':
        # Get data from the form (using the same method as add_employee)
        month = request.POST.get('month')
        date_range = request.POST.get('date_range')
        year = request.POST.get('year')
        pay_cycle = request.POST.get('pay_cycle')

        # Retrieve employee rate and other info
        rate = employee.rate
        allowance = employee.allowance if employee.allowance else 0
        overtime_hours = employee.overtime_pay if employee.overtime_pay else 0

        # Calculations for deductions and total pay
        overtime = overtime_hours
        earnings_allowance = allowance
        deductions_tax = rate * 0.10  # 10% tax
        deductions_health = rate * 0.03  # 3% health
        pag_ibig = rate * 0.01  # 1% pag-ibig
        sss = rate * 0.04  # 4% sss

        total_pay = (rate / 2) + earnings_allowance + overtime - deductions_tax - deductions_health - pag_ibig - sss

        # Save the payslip in the database
        Payslip.objects.create(
            id_number=employee,
            month=month,
            date_range=date_range,
            year=year,
            pay_cycle=pay_cycle,
            rate=rate,
            earnings_allowance=earnings_allowance,
            deductions_tax=deductions_tax,
            deductions_health=deductions_health,
            pag_ibig=pag_ibig,
            sss=sss,
            overtime=overtime,
            total_pay=total_pay
        )

        # Reset overtime
        employee.overtime_pay = 0
        employee.save()

        messages.success(request, f"Payslip generated successfully for {employee.name}.")
        return redirect('payslip')  # Redirect to the same page or another one

    # GET request: Display payslip form and all payslips
    payslips = Payslip.objects.all()  # Retrieve all payslips for display
    return render(request, 'payroll_app/payslip.html', {
        'employee': employee,
        'payslips': payslips
    })