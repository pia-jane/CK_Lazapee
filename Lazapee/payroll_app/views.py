from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Employee, Payslip, Account
from django.contrib.auth.hashers import make_password, check_password

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
       overtime_hours = float(request.POST.get('overtime_hours', 0))
       overtime_pay = (employee.rate/160)*1.5*overtime_hours
       employee.overtime_pay += overtime_pay
       employee.save()
       messages.success(request, f"Overtime of {overtime_pay:.2f} added.")
   except (ValueError):
       messages.error(request, "Invalid overtime hours.")
   return redirect('payroll')

def add_employee(request):
    if request.method == "POST":
        name = request.POST.get('name')
        id_number = request.POST.get('id_number')
        rate =  request.POST.get('rate')
        allowance = request.POST.get('allowance')

        allowance = allowance if allowance else None
    
        Employee.objects.create(name=name, id_number=id_number, rate=rate, allowance=allowance)
        return redirect('payroll')
    
    return render(request, 'payroll_app/add_employee.html')