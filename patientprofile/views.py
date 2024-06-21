from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404
from django.db import connection, transaction
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from django.db import connection
from datetime import date, timedelta
from datetime import datetime
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

# Create your views here.
def pprofile (request):
      patient_id= request.session.get('id')
      patient_name= request.session.get('name')
      with connection.cursor() as cursor:
          cursor.execute("SELECT p_photo from patient where pid = %s", [patient_id])
          photo=cursor.fetchone()
          p_img = photo[0].tobytes()
          img_path = p_img.decode('utf-8')


      return render(request, 'patientprofile/pprofile.html', {
            "id": patient_id,
            "name": patient_name,
            "photo": img_path })

def appointment(request):
    print(request.method)
    if request.method == 'POST':
        appointment_type = request.POST.get('appointment_type')
        return redirect('patientprofile:available_time', appointment_type= appointment_type)
    return render(request, 'patientprofile/appointment.html')

def available_time(request, appointment_type):
    pid= request.session.get('id')
    if appointment_type == 'examination':
        with connection.cursor() as cursor:
            cursor.execute("SELECT s.fname, d.d_specialization, a.day, a.shift_start, a.shift_end, d.did from doctor d inner join availability a ON d.did = a.did inner join staff s on s.eid = d.eid")
            examination_availabilities = cursor.fetchall()
        return render(request, 'patientprofile/available_time.html', {"examination_availabilities": examination_availabilities, "appointment_type": "examination"})

    elif appointment_type == 'follow_up':
        with connection.cursor() as cursor:
            cursor.execute("SELECT followup FROM medical_history WHERE did = (SELECT did FROM patient WHERE pid = %s)", [pid])
            followup= cursor.fetchall()[-1][0] #this is latest followup datetime
            followup_date = datetime.strptime(followup, '%Y-%m-%d').date()  # Convert string to datetime.date
            day_of_week = followup_date.strftime('%A')  # Get day of the week as a string (e.g., 'Monday')

        with connection.cursor() as cursor:
            cursor.execute("SELECT s.fname, d.d_specialization, a.day ,a.shift_start, a.shift_end, d.did FROM doctor d inner join availability a ON d.did = a.did inner join staff s on s.eid = d.eid WHERE (a.did = (SELECT did FROM patient WHERE pid = %s)) and (a.day= %s) ", [pid, day_of_week])
            followup_availabilities = cursor.fetchall()
        return render(request, 'patientprofile/available_time.html', {"followup_availabilities": followup_availabilities,"appointment_type": "follow_up", "followup_date":followup})

    elif appointment_type == 'surgery':
        with connection.cursor() as cursor:
            cursor.execute("SELECT s.fname, d.d_specialization, a.day, a.shift_start, a.shift_end, d.did FROM doctor d inner join availability a ON d.did = a.did inner join staff s on s.eid = d.eid WHERE d.d_specialization='Surgery'")
            operation_availabilities = cursor.fetchall()
        return render(request, 'patientprofile/available_time.html', {"operation_availabilities": operation_availabilities, "appointment_type": "surgery"})

    return render(request, 'patientprofile/available_time.html')

def process_appointment(request):
    pid= request.session.get('id')
    if request.method=='POST':
        did= request.POST.get('did')
        time= request.POST.get('Time')
        app_type=request.POST.get('appointment_type')
        # print(time)---> Monday - 8:30 a.m. - 10:30 a.m.
        if app_type=='examination' or app_type=='surgery':
            day_name, start_time, _ = time.split('-')
            app_date= get_next_weekday(day_name)
            try:
                # Convert '10 a.m.' to '10:00 AM'
                start_time_processed = start_time.strip().replace(' a.m.', ':00 AM').replace(' p.m.', ':00 PM')
                # Parse into a datetime object
                start_time = datetime.strptime(start_time_processed, '%I:%M %p').time().strftime('%H:%M')
            except ValueError:
                return HttpResponse("Invalid start time format")

            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO appointment (app_date, app_time, app_type, pid, did) Values (%s, %s, %s, %s, %s)",
                                [app_date, start_time, app_type, pid, did ])

            return redirect('patientprofile:payment',app_type=app_type, did=did, app_date=app_date, start_time=start_time)
        elif app_type=='follow_up':
            followup_date, day_name, start_time, end_time = time.split('*')
            start_time_processed = start_time.strip().replace(' a.m.', ':00 AM').replace(' p.m.', ':00 PM')
            # Parse into a datetime object
            start_time = datetime.strptime(start_time_processed, '%I:%M %p').time().strftime('%H:%M')
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO appointment (app_date, app_time, app_type, pid, did) Values (%s, %s, %s, %s, %s)",
                                [followup_date, start_time, app_type, pid, did])
            return redirect('patientprofile:payment',app_type=app_type, did=did, app_date=followup_date, start_time=start_time)
    return HttpResponse("Waiting to process the appointment")

def history(request):
    pid = request.session.get('id')
    patient_name = request.session.get('name')
    with connection.cursor() as cursor:
        cursor.execute("SELECT s.fname, s.lname, m.diagnosis, m.treatment, m.followup from medical_history m inner join doctor d ON m.did = d.did inner join staff s ON d.eid= s.eid where pid = %s", [pid])
        history = cursor.fetchall() #list of tuples, each tuple represents a row of data returned by the query
    return render (request, 'patientprofile/history.html', {"history": history,"patient_name": patient_name })


def contact(request):
    pid = request.session.get('id')
    if request.method=='POST':
        inquiry= request.POST.get('inquiry')
        with connection.cursor() as cursor:
            cursor.execute("SELECT did from patient where pid =%s ",[pid])
            did=cursor.fetchone()[0]
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO form (pid, request ,did) Values (%s, %s, %s)", [pid, inquiry, did])
            return redirect ('patientprofile:success_request')
    return render (request, 'patientprofile/contact.html')


def doctor_response(request):
    pid = request.session.get('id')
    with connection.cursor() as cursor:
        cursor.execute("SELECT request, response from form where pid = %s",[pid])
        forms= cursor.fetchall()
    return render (request, 'patientprofile/doctor_response.html', {"forms": forms})


def payment(request,app_type,did, app_date, start_time):
    p_name= request.session.get('name')
    fees=""
    with connection.cursor() as cursor:
        cursor.execute("SELECT d.d_specialization, s.fname from doctor d inner join staff s on d.eid=s.eid")
        doc_name, d_specialization= cursor.fetchone()
        if app_type=='examination':
            if d_specialization=='General Practioner':fees=100
            if d_specialization=='Consultant': fees=200
        elif app_type=='follow_up':
            if d_specialization=='General Practioner':fees=50
            if d_specialization=='Consultant': fees=100
        elif app_type=='surgery':
            fees= "will be determined by the hospital soon"

    return render (request, 'patientprofile/payment.html',{"doc_name": doc_name,"patient_name":p_name, "d_specialization": d_specialization,"app_date": app_date, "app_type": app_type, "start_time":start_time, "fees": fees})

def success_request(request):
    return render (request, 'patientprofile/success_request.html')

def edit(request):
    pid = request.session.get('id')
    with connection.cursor() as cursor:
        cursor.execute("SELECT * from patient where pid = %s", [pid])
        patient = cursor.fetchone()
        p_img = patient[5].tobytes()
        img_path = p_img.decode('utf-8')

    if request.method == "POST":
        address = request.POST.get('address')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        hashed_password = make_password(password)
        img = request.FILES.get('img')
        if img:  # if new photo
            img_name = img.name
            img_path = default_storage.save(img_name, img)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE patient SET email = %s, password = %s, address = %s, phone_number = %s, p_photo = %s WHERE pid = %s",
                [email, hashed_password, address, phone_number, img_path, pid]
            )

        target_url = f'/patient/pprofile?patient_id={pid}'
        return redirect(target_url)
    else:
        return render(request, 'patientprofile/edit.html', {"patient": patient, "img_path": img_path})

def operation(request):
        return render (request, 'patientprofile/operation.html')


def get_next_weekday(day_name):
    day_mapping = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }

    today = date.today()
    today_weekday = today.weekday()

    # Find the target weekday
    target_weekday = day_mapping[day_name.lower().strip()]

    # Calculate the difference in days to the next target weekday
    days_ahead = target_weekday - today_weekday
    if days_ahead <= 0:
        days_ahead += 7

    next_weekday = today + timedelta(days=days_ahead)
    return next_weekday