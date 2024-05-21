from urllib import request
from django.shortcuts import render, HttpResponse, redirect
from django.db import connection

# Create your views here.

def admin_profile(request):
    # Ordering and viewing the staff
    order = request.GET.get('group', 'eid')
    with connection.cursor() as cursor:
        cursor.execute("""SELECT eid, fname, lname, role, salary
                        FROM staff
                        ORDER BY eid""")
        data = cursor.fetchall()

    # Admin name
    with connection.cursor() as cursor:
        cursor.execute("""SELECT username 
                        FROM admin""")
        admin = cursor.fetchone()

    # Getting patients number
    with connection.cursor() as cursor:
        cursor.execute("""SELECT count(*)
                       FROM patient""")
        patients = cursor.fetchone()

    # Getting doctors number
    with connection.cursor() as cursor:
        cursor.execute("""SELECT count(*)
                       FROM doctor""")
        doctors = cursor.fetchone()

    # Getting Nurses number
    with connection.cursor() as cursor:
        cursor.execute("""SELECT count(*)
                       FROM nurse""")
        nurses = cursor.fetchone()

    # Getting Technicians number
    with connection.cursor() as cursor:
        cursor.execute("""SELECT count(*)
                       FROM technician""")
        tech = cursor.fetchone()

    # Getting Staff number
    with connection.cursor() as cursor:
        cursor.execute("""SELECT count(*)
                       FROM staff""")
        staff = cursor.fetchone()

    # Getting Appointments number
    with connection.cursor() as cursor:
        cursor.execute("""SELECT count(*)
                       FROM appointment""")
        app = cursor.fetchone()

    view, viewed = None, None
    if request.method == 'POST':
        view = request.POST.get('view')
        if view == 'patient':
            viewed = patient_view('pid')
        elif view == 'doctor':
            viewed = doctor_view('did')
        elif view == 'nurse':
            viewed = nurse_view('nid')
        elif view == 'technician':
            viewed = tech_view('tid')
        elif view == 'appointment':
            viewed = app_view()

    return render(request, 'adminPage/admin_profile.html', {'name': admin,
                                                            'patient':patients,
                                                            'doctorn':doctors,
                                                            'nurse':nurses,
                                                            'tech':tech,
                                                            'staffn':staff,
                                                            'app':app,
                                                            'viewed': viewed,
                                                            'person':view})

def patient_view(order):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT p.pid, p_fname, p_lname, phone_number, p_age, s.fname, s.lname, diagnosis
                       FROM patient p JOIN staff s ON p.did = s.eid
                       LEFT JOIN medical_history m ON p.pid = m.pid
                       ORDER BY """ + order)
        patients = cursor.fetchall()
    return patients

def doctor_view(order):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT d.did, fname, lname, age, d_specialization, d.email, s.salary
                       FROM doctor d LEFT JOIN staff s ON d.did = s.eid
                       ORDER BY """ + order)
        doctors = cursor.fetchall()
    return doctors

def nurse_view(order):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT t1.nid, t1.fname, t1.lname, t1.age, t1.n_specialization, t1.salary, t2.fname, t2.lname
                       FROM (SELECT nid, fname, lname, age, n_specialization, s.salary, n.did FROM nurse n
                            LEFT JOIN staff s ON n.nid = s.eid) AS t1
                        JOIN (SELECT fname, lname, d.did FROM doctor d
                            JOIN staff s ON d.did = s.eid) AS t2
                       ON t1.did = t2.did
                       ORDER BY """ + order)
        nurses = cursor.fetchall()
    return nurses

def tech_view(order):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT t1.tid, t1.fname, t1.lname, t1.age, t1.salary, t2.fname, t2.lname
                       FROM (SELECT tid, fname, lname, age, s.salary, t.did FROM technician t
                            LEFT JOIN staff s ON t.tid = s.eid) AS t1
                        JOIN (SELECT fname, lname, d.did FROM doctor d
                            JOIN staff s ON d.did = s.eid) AS t2
                       ON t1.did = t2.did
                       ORDER BY """ + order)
        tech = cursor.fetchall()
    return tech

def app_view():
    with connection.cursor() as cursor:
        cursor.execute("""SELECT t1.pid, t1.p_fname, t1.p_lname, t3.fname, t3.lname
                       FROM (SELECT a.pid, p_fname, p_lname, app_date, app_time, app_type, rnum, a.aid FROM appointment a
                            JOIN patient p ON a.pid = p.pid) AS t1
                        JOIN (SELECT fname, lname, a.did, a.aid FROM appointment a
                            JOIN (SELECT s.fname, s.lname, d.did
                                FROM doctor d JOIN staff s ON d.did = s.eid) AS t2 ON a.did = t2.did) AS t3
                       ON t1.aid = t3.aid""")
        apps = cursor.fetchall()
    return apps

def role(request):
    return render(request, 'adminPage/hire.html')

def add_doc(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('number')
        address = request.POST.get('address')
        email = request.POST.get('email')
        password = request.POST.get('password')
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        salary = request.POST.get('salary')
        special = request.POST.get('speicalization')
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO staff (role, fname, lname, sex, age, salary, address)
            VALUES('Doctor' ,%s,%s,%s,%s,%s,%s)""",
            [first_name, last_name, gender, age, salary, address])
        with connection.cursor() as cursor:
            cursor.execute("""SELECT eid
                               FROM staff
                               WHERE fname = %s AND lname = %s""", [first_name, last_name])
            eid = cursor.fetchone()
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO doctor (d_phone, email, password, d_specialization, eid)
                        VALUES(%s, %s, %s, %s, %s)""", [phone_number, email, password, special, eid])
        return redirect('admin_profile')
    return render(request, 'adminPage/add_doc.html')

def add_nur(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        salary = request.POST.get('salary')
        did = request.POST.get('did')
        special = request.POST.get('speicalization')
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO staff (role, fname, lname, sex, age, salary, address)
            VALUES('Nurse',%s,%s,%s,%s,%s,%s)""",
            [first_name, last_name, gender, age, salary, address])
        with connection.cursor() as cursor:
            cursor.execute("""SELECT eid
                           FROM staff
                           WHERE fname = %s and lname = %s""", [first_name, last_name])
            eid = cursor.fetchone()
        with connection.cursor() as cursor:
                cursor.execute("""INSERT INTO nurse (eid, did, n_specialization)
                            VALUES(%s, %s, %s)""", [eid, did, special])
        return redirect('admin_profile')
    return render(request, 'adminPage/add_nur.html')

def add_tech(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        age = request.POST.get('age')
        salary = request.POST.get('salary')
        did = request.POST.get('did')
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO staff (role, fname, lname, sex, age, salary, address)
            VALUES('Technician',%s,%s,%s,%s,%s,%s)""",
            [first_name, last_name, gender, age, salary, address])
        with connection.cursor() as cursor:
            cursor.execute("""SELECT eid
                           FROM staff
                           WHERE fname = %s and lname = %s""", [first_name, last_name])
            eid = cursor.fetchone()
        with connection.cursor() as cursor:
                cursor.execute("""INSERT INTO technician (eid, did)
                            VALUES(%s, %s)""", [eid, did])
        return redirect('admin_profile')
    return render(request, 'adminPage/add_tech.html')

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

def cancel(request):
    return redirect('admin_profile')