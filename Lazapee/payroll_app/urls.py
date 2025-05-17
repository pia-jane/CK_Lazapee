"""
URL configuration for Lazapee project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    path("admin/", admin.site.urls), 
    path('', views.login, name='login'),
    path('signup', views.signup, name='signup'),
    path('payroll', views.payroll, name='payroll'),
    path('delete_employee/<int:pk>/', views.delete_employee, name='delete_employee'),
    path('add_overtime/<int:pk>', views.add_overtime, name='add_overtime'),
    path('add_employee', views.add_employee, name='add_employee'),
    path('update_employee/<int:pk>/', views.update_employee, name='update_employee'),
    path('logout', views.logout, name='logout'),
    path('payslip', views.payslip, name='payslip'),
    path('payslip/<int:pk>/', views.view_payslip, name='view_payslip'),
    path('manage_account', views.manage_account, name='manage_account'),
    path('change_password', views.change_password, name='change_password'),
    path('delete_account/<int:pk>', views.delete_account, name='delete_account')


]
