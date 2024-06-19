from urllib import request
from django.shortcuts import render, HttpResponse, redirect
from django.db import connection
from django.contrib import messages

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
        cursor.execute("""SELECT username 
                        FROM admin""")
        admin = cursor.fetchone()

    # Getting patients number
        cursor.execute("""SELECT count(*)
                       FROM patient""")
        patients = cursor.fetchone()

    # Getting doctors number
        cursor.execute("""SELECT count(*)
                       FROM doctor""")
        doctors = cursor.fetchone()

    # Getting Nurses number
        cursor.execute("""SELECT count(*)
                       FROM nurse""")
        nurses = cursor.fetchone()

    # Getting Technicians number
        cursor.execute("""SELECT count(*)
                       FROM technician""")
        tech = cursor.fetchone()

    # Getting Staff number
        cursor.execute("""SELECT count(*)
                       FROM staff""")
        staff = cursor.fetchone()

    # Getting Appointments number
        cursor.execute("""SELECT count(*)
                       FROM appointment""")
        app = cursor.fetchone()

    if request.method == 'POST':
        view = request.POST.get('view')
        request.session['role'] = view

    view = request.session.get("role")
    if request.session.get("role") == 'patient':
        viewed = patient_view('pid')
    elif request.session.get("role") == 'doctor':
        viewed = doctor_view('did')
    elif request.session.get("role") == 'nurse':
        viewed = nurse_view('nid')
    elif request.session.get("role") == 'technician':
        viewed = tech_view('tid')
    elif request.session.get("role") == 'appointment':
        viewed = app_view()
    elif request.session.get("role") == 'remove':
        view, viewed = None, None
        # Clear the session
        request.session.flush()
        request.session.modified = True
    else:
        view, viewed = None, None

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
                       FROM doctor d LEFT JOIN staff s ON d.eid = s.eid
                       ORDER BY """ + order)
        doctors = cursor.fetchall()
    return doctors

def nurse_view(order):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT t1.nid, t1.fname, t1.lname, t1.age, t1.salary, t1.n_specialization, t2.fname, t2.lname
                       FROM (SELECT nid, did, n_specialization, age, fname, lname, salary
                            FROM nurse n JOIN staff s ON n.eid = s.eid) AS t1
                       JOIN (SELECT did, fname, lname
                            FROM doctor d JOIN staff s ON d.eid = s.eid) AS t2
                       ON t1.did = t2.did 
                       ORDER BY """ + order)
        nurses = cursor.fetchall()
    return nurses

def tech_view(order):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT t1.tid, t1.fname, t1.lname, t1.age, t1.salary, t2.fname, t2.lname
                       FROM (SELECT tid, did, age, fname, lname, salary
                            FROM technician t JOIN staff s ON t.eid = s.eid) AS t1
                       JOIN (SELECT did, fname, lname
                            FROM doctor d JOIN staff s ON d.eid = s.eid) AS t2
                       ON t1.did = t2.did
                       ORDER BY """ + order)
        tech = cursor.fetchall()
    return tech

def app_view():
    with connection.cursor() as cursor:
        cursor.execute("""SELECT t3.aid, t3.p_fname, t3.p_lname, t3.fname, t3.lname, t3.app_date, t3.app_time, t3.rnum, t3.app_type, b.amount
                        FROM (SELECT t1.aid, t1.app_date, t1.app_time, t1.app_type, t1.bid, t1.rnum, t1.p_fname, t1.p_lname, t2.fname, t2.lname
                            FROM (SELECT aid, app_date, app_time, app_type, bid, a.did, rnum, p_fname, p_lname
                                FROM appointment a JOIN patient p ON a.pid = p.pid) AS t1
                            JOIN (SELECT fname, lname, did
                                FROM doctor d JOIN staff s ON d.eid = s.eid) AS t2
                            ON t1.did = t2.did) AS t3
                        JOIN billing b ON t3.bid = b.bid""")
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
            # Inserting new dr to staff table
            cursor.execute("""INSERT INTO staff (role, fname, lname, sex, age, salary, address)
            VALUES('Doctor' ,%s,%s,%s,%s,%s,%s)""",
            [first_name, last_name, gender, age, salary, address])

            # Selecting dr id
            cursor.execute("""SELECT eid
                               FROM staff
                               WHERE fname = %s AND lname = %s""", [first_name, last_name])
            eid = cursor.fetchone()

            # Inserting new dr to dr table
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
            # Inserting new nurse to staff table
            cursor.execute("""INSERT INTO staff (role, fname, lname, sex, age, salary, address)
            VALUES('Nurse',%s,%s,%s,%s,%s,%s)""",
            [first_name, last_name, gender, age, salary, address])
            
            # Selecting nurse id
            cursor.execute("""SELECT eid
                           FROM staff
                           WHERE fname = %s and lname = %s""", [first_name, last_name])
            eid = cursor.fetchone()

            # Inserting nurse to nurse table
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
            # Inserting new tech to staff table
            cursor.execute("""INSERT INTO staff (role, fname, lname, sex, age, salary, address)
            VALUES('Technician',%s,%s,%s,%s,%s,%s)""",
            [first_name, last_name, gender, age, salary, address])

            # Selecting tech id
            cursor.execute("""SELECT eid
                           FROM staff
                           WHERE fname = %s and lname = %s""", [first_name, last_name])
            eid = cursor.fetchone()
        
            # Inserting tech to tech table
            cursor.execute("""INSERT INTO technician (eid, did)
                            VALUES(%s, %s)""", [eid, did])
        return redirect('admin_profile')
    return render(request, 'adminPage/add_tech.html')

def edit_doc(request, id):
    # Getting nurse data
    with connection.cursor() as cursor:
        cursor.execute("""SELECT d.eid, fname, lname, address, s.age, d_specialization, salary, email, password, d_phone
                       From doctor d JOIN staff s ON d.eid = s.eid
                       WHERE did = %s""", [id])
        data = cursor.fetchone()
        
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        age = request.POST.get('age')
        phone = request.POST.get('phone')
        salary = request.POST.get('salary')
        special = request.POST.get('speicalization')
        email = request.POST.get('email')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            # Updating doctor in staff table
            cursor.execute("""UPDATE staff 
                            SET fname = %s, lname = %s, age = %s, salary = %s, address = %s
                            WHERE eid = %s""",
                            [first_name, last_name, age, salary, address, data[0]])
            
            # Updating doctor in dotcor table
            cursor.execute("""UPDATE doctor
                           SET d_specialization = %s, d_phone = %s, email = %s, password = %s
                           WHERE did = %s""", [special, phone, email, password, id])

        return redirect('admin_profile')
    return render(request, 'adminPage/edit_doc.html', {'did': id,
                                                       'doc': data})

def edit_nur(request, id):
    # Getting nurse data
    with connection.cursor() as cursor:
        cursor.execute("""SELECT n.eid, fname, lname, address, s.age, n_specialization, n.did, salary
                       From nurse n JOIN staff s ON n.eid = s.eid
                       WHERE nid = %s""", [id])
        data = cursor.fetchone()
        
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        age = request.POST.get('age')
        salary = request.POST.get('salary')
        did = request.POST.get('did')
        special = request.POST.get('speicalization')

        with connection.cursor() as cursor:
            # Updating nurse in staff table
            cursor.execute("""UPDATE staff 
                            SET fname = %s, lname = %s, age = %s, salary = %s, address = %s
                            WHERE eid = %s""",
                            [first_name, last_name, age, salary, address, data[0]])
            
            # Updating nurse in nurse table
            cursor.execute("""UPDATE nurse
                           SET did = %s, n_specialization = %s
                           WHERE nid = %s""", [did, special, id])

        return redirect('admin_profile')
    return render(request, 'adminPage/edit_nur.html', {'nur': data,
                                                       'nid': id})


def edit_tech(request, id):
    # Getting nurse data
    with connection.cursor() as cursor:
        cursor.execute("""SELECT t.eid, fname, lname, address, s.age, t.did, salary
                       From technician t JOIN staff s ON t.eid = s.eid
                       WHERE tid = %s""", [id])
        data = cursor.fetchone()
        
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        age = request.POST.get('age')
        salary = request.POST.get('salary')
        did = request.POST.get('did')

        with connection.cursor() as cursor:
            # Updating techinican in staff table
            cursor.execute("""UPDATE staff 
                            SET fname = %s, lname = %s, age = %s, salary = %s, address = %s
                            WHERE eid = %s""",
                            [first_name, last_name, age, salary, address, data[0]])
            
            # Updating tech in tech table
            cursor.execute("""UPDATE technician
                           SET did = %s
                           WHERE tid = %s""", [did, id])

        return redirect('admin_profile')
    return render(request, 'adminPage/edit_tech.html', {'tid': id,
                                                        'tech':data})
def available(request, id):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT s.fname, s.lname, a.day, a.shift_start, a.shift_end
                       FROM availability a JOIN doctor d ON a.did = d.did
                       JOIN staff s ON s.eid = d.eid
                       WHERE a.did = %s""", [id])
        time = cursor.fetchall()
    return render(request, 'adminPage/available.html', {'time': time})

def rmv_doc(request, id):
    with connection.cursor() as cursor:
        # Selecting dr eid
        cursor.execute("""SELECT eid
                       FROM doctor
                       WHERE did = %s""", [id])
        eid = cursor.fetchone()

        # Deleting dr from dr table
        cursor.execute("""DELETE FROM doctor
                        WHERE did = %s""", [id])
        
        # Deleting dr from staff table
        cursor.execute("""DELETE FROM staff
                        WHERE eid = %s""", [eid])
    return redirect('admin_profile')

def rmv_nur(request, id):
    with connection.cursor() as cursor:
        # Selecting nurse eid
        cursor.execute("""SELECT eid
                       FROM nurse
                       WHERE did = %s""", [id])
        eid = cursor.fetchone()

        # Deleting nurse from nurse table
        cursor.execute("""DELETE FROM nurse
                        WHERE nid = %s""", [id])
        
        # Deleting nurse from staff table
        cursor.execute("""DELETE FROM staff
                        WHERE eid = %s""", [eid])
    return redirect('admin_profile')

def rmv_tech(request, id):
    with connection.cursor() as cursor:
        # Selecting tech eid
        cursor.execute("""SELECT eid
                       FROM technician
                       WHERE tid = %s""", [id])
        eid = cursor.fetchone()

        # Deleting tech from tech table
        cursor.execute("""DELETE FROM technician
                        WHERE tid = %s""", [id])

        # Deleting tech from staff table
        cursor.execute("""DELETE FROM staff
                        WHERE eid = %s""", [eid])
    return redirect('admin_profile')

def cancel(request):
    return redirect('admin_profile')