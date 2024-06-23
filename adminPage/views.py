from datetime import datetime
from urllib import request
from django.shortcuts import render, HttpResponse, redirect
from django.db import connection
from django.urls import reverse
from dateutil import parser
from django.contrib.auth.hashers import make_password

def login(request):
    if request.method == 'POST':
        user = request.POST.get('user')
        password = request.POST.get('password')

        with connection.cursor() as cursor:
            cursor.execute("""SELECT username
                           FROM admin""")
            usernames = cursor.fetchall()
        if any(user in tup for tup in usernames):
            request.session['user'] = user
            with connection.cursor() as cursor:
                cursor.execute("""SELECT password
                               FROM admin
                               WHERE username = %s""",[user])
                password_old = cursor.fetchone()
            
            if password == password_old[0]:
                return redirect('admin_profile')
            else:
                wrong = 'Password is incorrect!' 
                return render(request, 'adminPage/login.html', {'wrong':wrong})
        else:
            wrong = 'Username is not found!'
            return render(request, 'adminPage/login.html', {'wrong':wrong})
    return render(request, 'adminPage/login.html')

def admin_profile(request):        
    admin = request.session.get('user')

    # Ordering and viewing the staff
    with connection.cursor() as cursor:

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
                       FROM appointment
                       WHERE bid IS NOT NULL""")
        app = cursor.fetchone()

    # Getting total income 
        cursor.execute("""SELECT sum(amount)
                       FROM billing
                       WHERE payment_status = 'Paid' """)
        amount = cursor.fetchone()

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
                                                            'amount': amount,
                                                            'viewed': viewed,
                                                            'person':view})

def patient_view(order):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT p.pid, p_fname, p_lname, phone_number, p_age, s.fname, s.lname, count(mid)
                       FROM patient p JOIN doctor d ON p.did = d.did
                       JOIN staff s ON s.eid = d.eid
                       LEFT JOIN medical_history m ON m.pid = p.pid
                       GROUP BY p.pid, s.eid
                       ORDER BY """ + order)
        patients = cursor.fetchall()
    return patients

def doctor_view(order):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT d_photo, d.did, fname, lname, age, d_specialization, d.email, s.salary
                       FROM doctor d LEFT JOIN staff s ON d.eid = s.eid
                       ORDER BY """ + order)
        doctors = cursor.fetchall()
    return doctors

def nurse_view(order):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT t1.nid, t1.fname, t1.lname, t1.age, t1.salary, t1.n_specialization, t2.fname, t2.lname
                       FROM (SELECT n.eid, nid, did, n_specialization, age, fname, lname, salary
                            FROM nurse n JOIN staff s ON n.eid = s.eid) AS t1
                       JOIN (SELECT did, fname, lname
                            FROM doctor d JOIN staff s ON d.eid = s.eid) AS t2
                       ON t1.did = t2.did 
                       ORDER BY t1.eid""")
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
        cursor.execute("""SELECT t3.aid, t3.p_fname, t3.p_lname, t3.fname, t3.lname, t3.app_date, t3.app_time, t3.rnum, t3.app_type, b.amount, t3.appointment_status
                        FROM (SELECT t1.aid, t1.app_date, t1.app_time, t1.app_type, t1.bid, t1.rnum, t1.p_fname, t1.p_lname, t1.appointment_status, t2.fname, t2.lname
                            FROM (SELECT aid, app_date, app_time, app_type, bid, a.did, rnum, appointment_status, p_fname, p_lname
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
        special = request.POST.get('special')
        
        password = make_password(password)

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
        special = request.POST.get('special')

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
        special = request.POST.get('special')
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
                       FROM nurse n JOIN staff s ON n.eid = s.eid
                       WHERE nid = %s""", [id])
        data = cursor.fetchone()
        
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        age = request.POST.get('age')
        salary = request.POST.get('salary')
        did = request.POST.get('did')
        special = request.POST.get('special')

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
        cursor.execute("""SELECT a.id, a.day, a.shift_start, a.shift_end
                       FROM availability a JOIN doctor d ON a.did = d.did
                       WHERE a.did = %s
                       ORDER BY CASE 
                                WHEN day = 'Saturday' THEN 1
                                WHEN day = 'Sunday' THEN 2
                                WHEN day = 'Monday' THEN 3
                                WHEN day = 'Tuesday' THEN 4
                                WHEN day = 'Wednesday' THEN 5
                                WHEN day = 'Thursday' THEN 6
                                WHEN day = 'Friday' THEN 7
                                END, shift_start""", [id])
        time = cursor.fetchall()

        cursor.execute("""SELECT fname, lname
                       FROM staff s JOIN doctor D ON s.eid = d.eid
                       WHERE d.did = %s""", [id])
        name = cursor.fetchone()
    return render(request, 'adminPage/view_available.html', {'time': time,
                                                             'name': name,
                                                             'id': id})

def edit_availability(request, id):
    if request.method == 'POST':
        aid = request.POST.get('id')
        day = request.POST.get('day')
        start = request.POST.get('start')
        end = request.POST.get('end')

        if start == 'noon':
            start = '12 p.m.'
        if end == 'noon':
            end = '12 p.m.'
        
        start = parser.parse(start).strftime("%H:%M:%S")
        end = parser.parse(end).strftime("%H:%M:%S")

        with connection.cursor() as cursor:
            cursor.execute("""UPDATE availability 
                                SET day = %s, shift_start = %s, shift_end = %s
                                WHERE did = %s and id = %s""", [day, start, end, id, aid])
            
        return redirect(reverse('available', args=[id]))
    return render(request, 'adminPage/view_available.html')

def add_shift(request, id):
    if request.method == 'POST':
        day = request.POST.get('day')
        start = request.POST.get('start')
        end = request.POST.get('end')

        if start == 'noon':
            start = '12 p.m.'
        if end == 'noon':
            end = '12 p.m.'

        start = parser.parse(start).strftime("%H:%M:%S")
        end = parser.parse(end).strftime("%H:%M:%S")
        
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO availability (day, shift_start, shift_end, did)
                                VALUES (%s,%s,%s,%s)""", [day, start, end, id])

        return redirect(reverse('available', args=[id]))
    return render(request, 'adminPage/add_shift.html', {'id':id})

def delet_shift(request, id):
    with connection.cursor() as cursor:
        cursor.execute("""SELECT did
                       FROM availability
                       WHERE id = %s""", [id])
        did = cursor.fetchone()[0]

        cursor.execute("""DELETE FROM availability
                       WHERE id = %s""", [id])
        
    return redirect(reverse('available', args=[did]))

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
                       WHERE nid = %s""", [id])
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
    return redirect('role')


def cancel_edit(request):
    return redirect('admin_profile')

def cancel_shift(request, id):
    return redirect(reverse('available', args=[id]))

# def add_nurses(request):
#     with connection.cursor() as cursor:
#         cursor.execute("""INSERT INTO technician (eid, did) VALUES
# (76, 52),
# (77, 53),
# (60, 54),
# (59, 55),
# (58, 56),
# (51, 57),
# (48, 58),
# (92, 59),
# (46, 60),
# (45, 61),
# (31, 52),
# (61, 53),
# (62, 54),
# (17, 55),
# (88, 56),
# (89, 57),
# (91, 58),
# (73, 59),
# (74, 60),
# (75, 61),
# (90, 52);

# """)
#         return redirect('admin_profile')