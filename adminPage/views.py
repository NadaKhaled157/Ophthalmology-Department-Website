from urllib import request
from django.shortcuts import render, HttpResponse, redirect
from django.db import connection

# Create your views here.

def admin_profile(request):
    order = request.GET.get('group', 'eid')
    with connection.cursor() as cursor:
        cursor.execute("""SELECT eid, fname, lname, role, salary
                        FROM staff
                        ORDER BY """ + order)
        data = cursor.fetchall()
    with connection.cursor() as cursor:
        cursor.execute("""SELECT username 
                        FROM admin""")
        admin = cursor.fetchone()
    return render(request, 'adminPage/admin_profile.html', {'name': admin,
                                                            'staff': data})

def hire(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('number')
        address = request.POST.get('address')
        email = request.POST.get('email')
        password = request.POST.get('password')
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        role = request.POST.get('role')
        salary = request.POST.get('salary')
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO staff (role, fname, lname, sex, age, salary, address)
            VALUES(%s,%s,%s,%s,%s,%s,%s)""",
            [role, first_name, last_name, gender, age, salary, address])
        return redirect("admin_profile")
    return render(request, 'adminPage/add_emp.html')

def edit_emp(request, id):
    if request.method == "POST":
        role = request.POST.get('role')
        salary = request.POST.get('salary')
        with connection.cursor() as cursor:
            cursor.execute("""UPDATE staff
                           set role = %s, salary = %s
                           WHERE eid = %s""", [role, salary, id])
        return redirect("admin_profile")
    return render(request, 'adminPage/edit_emp.html', {'id':id})

def fire(request, id):
    with connection.cursor() as cursor:
        cursor.execute("""DELETE FROM staff
                        WHERE eid = %s""", [id])
    return redirect('admin_profile')

