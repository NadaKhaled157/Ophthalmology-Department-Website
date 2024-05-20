from django.shortcuts import render, HttpResponse, redirect
from django.db import connection
from django.http import JsonResponse

# Create your views here.

def admin_profile(request):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT username 
                        FROM admin""")
        admin = cursor.fetchone()
    return render(request, 'adminPage/admin_profile.html', {'name': admin,
                                                            'staff': view_staff(request)})

def view_staff(request):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT eid, fname, lname, role, salary
                        FROM staff""")
        data = cursor.fetchall()
    return data

def hire(request):
    if request.method == 'POST':
        # return HttpResponse("in post")
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

def remove_staff(request, id):
    if request.method == "POST":
        with connection.cursor() as cursor:
            cursor.execute("""DELETE FROM staff
                            WHERE eid = %s""", [id])
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})