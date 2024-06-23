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
from pathlib import Path
from .helper import get_next_weekday, format_time, is_future_date, check_image, retrieve_image
# Create your views here.
def pprofile(request):
    pid = request.session.get('id')
    patient_name = request.session.get('name')

    with connection.cursor() as cursor:
        cursor.execute("""SELECT s.fname, s.lname, m.diagnosis, m.treatment, m.followup, m.dosage, m.frequency, a.app_date, a.app_time
                            FROM medical_history m
                            INNER JOIN appointment a ON m.aid = a.aid
                            INNER JOIN doctor d ON m.did = d.did
                            INNER JOIN staff s ON d.eid = s.eid
                            WHERE m.pid = %s"""
                                    , [pid])
        history = cursor.fetchall()

    with connection.cursor() as cursor:
        cursor.execute("SELECT * from patient where pid = %s", [pid])
        patient= cursor.fetchone()
        photo = patient[5]
        p_img = photo.tobytes() # type: ignore
        img_path = p_img.decode('utf-8')

    context = {
        'name': patient_name,
        'id': pid,
        'photo': img_path,
        'history': history,
        'patient': patient
    }

    return render(request, 'patientprofile/pprofile.html', context)

def appointment(request):
    try:
        error = request.session['no_app_type']
    except:
        error = False
    pid= request.session.get('id')
    if request.method == 'POST':
        appointment_type = request.POST.get('appointment_type')
        if appointment_type=='examination':
            return redirect('patientprofile:available_time', appointment_type= appointment_type)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT next_app_status FROM medical_history WHERE pid=%s ORDER BY mid DESC", [pid])
                next_app_status= cursor.fetchone()[0] #latest "next_appointment"
            if next_app_status==appointment_type:
                if appointment_type=='follow_up':
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT followup FROM medical_history WHERE pid=%s ORDER BY mid DESC", [pid])
                        followup_date= cursor.fetchone()[0]
                    if is_future_date(followup_date): return redirect('patientprofile:available_time', appointment_type= appointment_type)
                    else: return render(request,'patientprofile/appointment.html', {"expired":"Your followup date is expired! Examine Again or contact your doctor!"})
                else:
                    return redirect('patientprofile:available_time', appointment_type= appointment_type)
            else:
                return render(request, 'patientprofile/appointment.html', {"next_app_status": next_app_status,"error_next_app": "If you think this happen by mistake, please contact your doctor. Thanks!" })
        except: #this means next_app_status is Null, that happen for new patients
            return render(request, 'patientprofile/appointment.html', {"examine": "Sorry! You have to examine first." })
    return render(request, 'patientprofile/appointment.html',{"examine": None, "next_app_status":None, "no_app_type":error, "expired": None } )

def processed_availability(availabilities):
    # Process the examination_availabilities to convert days to next upcoming dates
    processed_availabilities = []
    doctor = []
    for availability in availabilities:
        available=True
        doctor_name , d_specialization, day_name, shift_start, shift_end, did = availability
        next_date = get_next_weekday(day_name.strip())
        #print(next_date,"  did: " , did)
        with connection.cursor() as cursor:
            cursor.execute("""SELECT count(*) from appointment where app_date=%s and did=%s""",[next_date, did])
            count= cursor.fetchone()[0]
            #print(f"count{count}")
        if count >3: available= False
        processed_availabilities.append((did, day_name, next_date, shift_start, shift_end, available))
        doctor_added = False
        # Check if the list is empty
        if len(doctor) == 0:
            doctor.append((did, doctor_name, d_specialization))
            doctor_added = True
        else:
            # Iterate over existing doctors
            for i in doctor:
                if did == i[0]:
                    # Doctor already exists, set the flag
                    doctor_added = True
                    break
        # If the doctor hasn't been added, append them to the list
        if not doctor_added:
            doctor.append((did, doctor_name, d_specialization))
    return processed_availabilities, doctor


def available_time(request, appointment_type):
    pid= request.session.get('id')
    decoded_paths_and_ids = retrieve_image(appointment_type,pid)
    print('paths_with_ids', decoded_paths_and_ids)
    if  appointment_type == 'examination':
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT s.fname || ' ' || s.lname AS doctor_name, d.d_specialization, a.day, a.shift_start, a.shift_end, d.did
                    FROM doctor d
                    INNER JOIN availability a ON d.did = a.did
                    INNER JOIN staff s ON s.eid = d.eid
                    Where d.d_specialization not in ('Surgeon')
                """)
                examination_availabilities = cursor.fetchall()
            processed_availabilities, doctor= processed_availability(examination_availabilities)

            return render(request, 'patientprofile/available_time.html', {'doctors_data':doctor,"shifts": processed_availabilities,"appointment_type": "examination", 'paths_with_ids':decoded_paths_and_ids})


    elif appointment_type == 'follow_up':
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT followup FROM medical_history WHERE did = (SELECT did FROM patient WHERE pid = %s) ORDER BY mid DESC", [pid])
                followup= cursor.fetchone()[0] #this is latest followup datetime (2024-22-06)
                followup_date = datetime.strptime(followup, '%Y-%m-%d').date()  # Convert string to datetime.date
                day_of_week = followup_date.strftime('%A')  # Get day of the week as a string that corresponds to that date (e.g., 'Monday')

            with connection.cursor() as cursor:
                cursor.execute("SELECT s.fname || ' ' || s.lname AS doctor_name, d.d_specialization, a.day ,a.shift_start, a.shift_end, d.did FROM doctor d inner join availability a ON d.did = a.did inner join staff s on s.eid = d.eid WHERE (a.did = (SELECT did FROM patient WHERE pid = %s)) and (a.day= %s) ", [pid, day_of_week])
                followup_availabilities = cursor.fetchall()
                print(followup_availabilities)
            return render(request, 'patientprofile/available_time.html', {"followup_availabilities": followup_availabilities,"appointment_type": "follow_up", "followup_date":followup, 'paths_with_ids':decoded_paths_and_ids})
        except: #in case did is updated in patient table  but not updated in medical_history table
            return HttpResponse("You have no record with this Doctor. If you think this happen by mistake please contact your doctor.")
    elif appointment_type == 'surgery':
        with connection.cursor() as cursor:
            cursor.execute("SELECT s.fname || ' ' || s.lname AS doctor_name,d.d_specialization, a.day, a.shift_start, a.shift_end, d.did FROM doctor d inner join availability a ON d.did = a.did inner join staff s on s.eid = d.eid WHERE d.d_specialization='Surgeon'")
            operation_availabilities = cursor.fetchall()
        processed_availabilities, doctor= processed_availability(operation_availabilities)
        return render(request, 'patientprofile/available_time.html', {"shifts": processed_availabilities,'doctors_data':doctor, "appointment_type": "surgery", 'paths_with_ids':decoded_paths_and_ids})

    return render(request, 'patientprofile/available_time.html')

def process_appointment(request): #after choosing appointment and available_time
    pid= request.session.get('id')
    if request.method=='POST':
        did= request.POST.get('did')
        time= request.POST.get('Time')
        print("did inside process_appointment ",did)
        app_type=request.POST.get('appointment_type')
        # print(time)---> (2020-06-22) - Monday - 8:30 a.m. - 10:30 a.m.
        app_day,app_date , start_time, end_time = time.split('*')
        if app_type=='examination':  #insert new did for patient
            with connection.cursor() as cursor:
                cursor.execute("UPDATE patient SET did = %s WHERE pid = %s", [did, pid])

        if app_type=='surgery':
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO appointment (app_date, app_time, app_type, pid, did) Values (%s, %s, %s, %s, %s)",
                                [app_date, start_time, app_type, pid, did ])
            return redirect('patientprofile:operation')

        else: #insert appointment data for followup and examination
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO appointment (app_date, app_time, app_type, pid, did) Values (%s, %s, %s, %s, %s)",
                                [app_date, start_time, app_type, pid, did ])

            return redirect('patientprofile:payment',app_type=app_type, did=did, app_date=app_date, start_time=start_time, app_day=app_day)
    return HttpResponse("Waiting to process the appointment")

def contact(request):
    pid = request.session.get('id')
    print(request.method)
    with connection.cursor() as cursor:
        cursor.execute("SELECT did from patient where pid =%s ",[pid])
        did=cursor.fetchone()[0]
        print("diddd", did)
    if not did:
        with connection.cursor() as cursor:
            cursor.execute("SELECT p_fname || ' ' || p_lname AS p_name, email, phone_number from patient where pid =%s", [pid])
            p_name, p_email, phone_number=cursor.fetchone()
        return render (request, 'patientprofile/visitor_form.html', {"p_name":p_name, "p_email":p_email, "phone_number":phone_number})
    else:
        with connection.cursor() as cursor:
            cursor.execute("SELECT s.fname || ' ' || s.lname AS doctor_name from staff s inner join doctor d on d.eid=s.eid where d.did =%s",[did])
            doctor_name= cursor.fetchone()[0]
        if request.method=='POST':
            inquiry= request.POST.get('inquiry')
            with connection.cursor() as cursor:
                cursor.execute("INSERT INTO form (pid, request ,did) Values (%s, %s, %s)", [pid, inquiry, did])
                return redirect ('patientprofile:success_request')
        return render (request, 'patientprofile/contact.html', {"doctor_name":doctor_name})


def doctor_response(request):
    pid = request.session.get('id')
    with connection.cursor() as cursor:
        cursor.execute("""SELECT f.request, f.response, f.fnum , s.fname || ' ' || s.lname AS patient_name, d.d_specialization, d.email
                       from form f
                       inner join doctor d on f.did= d.did
                       inner join staff s on d.eid= s.eid
                        where pid = %s""",[pid])
        forms= cursor.fetchall()
    return render (request, 'patientprofile/doctor_response.html', {"forms": forms})

def payment(request,app_type,did, app_date, start_time, app_day):
    p_name= request.session.get('name')
    pid= request.session.get('id')
    fees=200
    with connection.cursor() as cursor:
        cursor.execute("SELECT d.d_specialization, s.fname, s.lname from doctor d inner join staff s on d.eid=s.eid Where d.did= %s",[did])
        d_specialization, fname, lname= cursor.fetchone()
        doc_name= fname+" "+lname
    if app_type=='examination':
        if d_specialization=='General Practitioner': fees=100;
        if d_specialization=='Consultant': fees=200;
    elif app_type=='follow_up':
        if d_specialization=='General Practitioner':fees=50;
        if d_specialization=='Consultant': fees=100;
    elif app_type=='surgery':
        fees= "will be determined by the hospital soon"
    print(app_date, start_time, app_type, pid, did)
    with connection.cursor() as cursor:
        cursor.execute("SELECT aid from appointment where app_date = %s and app_time=%s and app_type= %s and pid=%s and did = %s",
                        [app_date, start_time, app_type, pid, did ])
        aid= cursor.fetchone()[0]
    print("aid in payment", aid)
    return render (request, 'patientprofile/payment.html',{"doc_name": doc_name,"patient_name":p_name, "d_specialization": d_specialization,"app_date": app_date, "app_day":app_day ,"app_type": app_type, "start_time":start_time, "fees": fees, "aid":aid})

def success_request(request):
    return render (request, 'patientprofile/success_request.html')

def success_payment(request):
    print(request.method)
    if request.method=="POST":
        aid=request.POST.get('aid')
        fees= request.POST.get('fees')
        payment_method= request.POST.get('payment-method')
        if payment_method=='cash':
            print("aid in success_payment", aid)
            with connection.cursor() as cursor:
                cursor.execute("""INSERT INTO billing (payment_status, amount) Values (%s, %s) RETURNING bid """,['Pending', fees])
                bid = cursor.fetchone()[0]
            print("bid", bid)
            with connection.cursor() as cursor:
                cursor.execute("""UPDATE appointment SET bid = %s WHERE aid = %s""", [bid, aid])

            return render (request, 'patientprofile/success_payment.html')

        elif payment_method=='visa':
                return redirect('patientprofile:pay_visa', fees=fees, aid=aid)
    else:
        return HttpResponse("POST is not seen ")



def pay_visa(request, fees, aid):
    return render (request, 'patientprofile/pay_visa.html', {"fees": fees, "aid": aid})

def success_payment_visa(request):
    date= datetime.today()
    if request.method=='POST':
        fees= request.POST.get('fees')
        aid= request.POST.get('aid')
        with connection.cursor() as cursor:
            cursor.execute("""INSERT INTO billing (bdate, payment_status, amount) Values (%s,%s, %s) returning bid """,[date,'Paid', fees])
            bid = cursor.fetchone()[0]
        with connection.cursor() as cursor:
            cursor.execute("""UPDATE appointment SET bid = %s WHERE aid = %s""", [bid, aid])
        print(aid)
        return render (request, 'patientprofile/success_payment.html')
    else:
        return HttpResponse("POST is not seen ")

def edit(request):
    pid = request.session.get('id')
    with connection.cursor() as cursor:
        cursor.execute("SELECT * from patient where pid = %s", [pid])
        patient = cursor.fetchone()
        p_img = patient[5].tobytes()
        img_path = p_img.decode('utf-8')

    if request.method == "POST":
        fname=request.POST.get('fname')
        lname=request.POST.get('lname')
        address = request.POST.get('address')
        age = request.POST.get('age')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        if confirm_password != password:
            return render(request, 'patientprofile/edit.html', {"patient": patient, "img_path": img_path, "nomatch":True})
        hashed_password = make_password(password)
        img = request.FILES.get('img')
        if img:  # if new photo
            img_name = img.name
            img_path = default_storage.save(img_name, img)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE patient SET p_fname= %s, p_lname= %s, email = %s, p_age= %s, password = %s, address = %s, phone_number = %s, p_photo = %s WHERE pid = %s",
                [fname, lname, email, age,hashed_password, address, phone_number, img_path, pid]
            )

        target_url = f'/patient/pprofile'
        return redirect(target_url)
    else:
        return render(request, 'patientprofile/edit.html', {"patient": patient, "img_path": img_path, "nomatch":False})

def operation(request):
        return render (request, 'patientprofile/operation.html')
