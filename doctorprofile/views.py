from django.shortcuts import render
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
from datetime import datetime
from pathlib import Path
# from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
# import uuid

# import base64

# from PIL import Image
# import io

# Create your views here.
def doctor_profile(request):
    try:
        doctor_id = request.session['logged_in_user']
    except:
        request.session['not_logged_in'] = True
        return redirect('common:authenticate_user')
    doctor, img_path = retrieve_doctor(doctor_id)
    if doctor:
        doctor_id = doctor[3] 
            # Fetch the availability for the doctor
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT day, shift_start,shift_end
                FROM availability 
                WHERE did = %s
            """, [doctor_id])
            availability = cursor.fetchall()
        ##Converting time to a readable format
        shifts=[]
        for shift in availability:
            new_shift = (shift[0], shift[1].strftime("%I:%M %p"), shift[2].strftime("%I:%M %p"))
            shifts.append(new_shift)
        appointments = retrieve_appointments(doctor_id)
        print(doctor)
        print(availability)
        return render(request, 'doctorprofile/profile.html', {'doctor': doctor, 'shifts': shifts,'appointments':appointments, 'img_path':img_path,'doctor_id':doctor_id})
    else:
            #return a better error
            return HttpResponse("No doctors found in the database.")

def forms(request):
    # doctor_id = request.GET.get('doctor_id') 
    # try:
    #     doctor_requested = str(request.session['logged_in_user'])
    # except:
    #     request.session['not_logged_in_alert'] = True
    #     return redirect('common:authenticate_user')
    # # return HttpResponse(f"{did.type()}|{doctor_requested.type()}")
    # if doctor_requested != did:
    #     request.session['not_logged_in_alert'] = True
    #     return redirect('common:authenticate_user')

    # doctor_requested = int(request.GET.get('doctor_id'))
    # try:
    #     # doctor_requested = request.session['logged_in_user']
    #     doctor_id = request.session['logged_in_user']
    # except:
    #     request.session['not_logged_in'] = True
    #     return redirect('common:authenticate_user')
    # if doctor_requested != doctor_id:
    #     request.session['not_logged_in'] = True
    #     return redirect('common:authenticate_user')

    try:
        # doctor_requested = request.session['logged_in_user']
        doctor_id = request.session['logged_in_user']
    except:
        request.session['not_logged_in'] = True
        return redirect('common:authenticate_user')

    status = request.GET.get('status')  # is this used?
    if request.method == 'POST':
        response = request.POST.get('response')
        form_num= request.POST.get('modal_id')
        # clicked_answered= request.POST.get('answered_forms')
        
        with connection.cursor() as cursor:
            del_fnum = request.POST.get('deleted_form')
            if del_fnum is not None:  #deleting form
                cursor.execute("DELETE from form where fnum = %s",[del_fnum])
            else: #inserting reponse
                cursor.execute("UPDATE form SET response = %s, form_status='Answered' WHERE fnum = %s", [response, form_num])

    with connection.cursor() as cursor: #displaying forms related to this doctor
            if status =='pending':
                cursor.execute("""SELECT f.fnum, p.p_fname, p.p_lname, f.request, f.response, f.form_status
                                FROM patient AS p
                                INNER JOIN form AS f ON p.pid = f.pid
                                INNER JOIN doctor AS d ON d.did = f.did
                                WHERE f.form_status = 'Pending' AND d.did = %s;
                        """,[doctor_id])
            else:
                cursor.execute("""SELECT f.fnum, p.p_fname, p.p_lname, f.request, f.response, f.form_status
                                FROM patient AS p
                                INNER JOIN form AS f ON p.pid = f.pid
                                INNER JOIN doctor AS d ON d.did = f.did
                                WHERE f.form_status = 'Answered' AND d.did = %s;
                        """,[doctor_id])
            if cursor.description is not None:
                form_data = cursor.fetchall()
                return render(request,'doctorprofile/forms.html',{'forms':form_data,'doctor_id':doctor_id})
    url = f'/doctor/forms/?status=pending&doctor_id={doctor_id}'
    return redirect(url)
    # return render(request,'doctorprofile/forms.html',{'forms':form_data,'doctor_id':did})

def visitor_form(request): #Stores Guest Inquiries and Shows Responses on Guest Side
    request.session['form_submitted'] = False
    request.session['response'] = False
    if request.method == "POST":
        if request.POST.get("check_responses") == 'True':
            form_code = request.POST.get('form_code')
            # return HttpResponse(form_code)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        f.request,
                        f.response,
                        CASE WHEN f.did IS NOT NULL
                            THEN e.fname || ' ' || e.lname
                            ELSE NULL
                        END AS doctor_name,
                        CASE WHEN f.did IS NOT NULL
                            THEN d.d_specialization
                            ELSE NULL
                        END AS d_specialization,
                        CASE WHEN f.did IS NOT NULL
                            THEN d.email
                            ELSE NULL
                        END AS email
                    FROM visitor_form f
                    LEFT JOIN doctor d ON d.did = f.did
                    LEFT JOIN staff e ON e.eid = d.eid
                    WHERE f.form_code = %s
                    """,[form_code])
                retrieved_inquiry = cursor.fetchone()
            request.session['response'] = True
            request.session['retrieved_inquiry'] = retrieved_inquiry
        else:
            # return HttpResponse("HERE")
            v_name = request.POST.get('v_name')
            v_email = request.POST.get('v_email')
            v_phone = request.POST.get('v_phone')
            v_request = request.POST.get('v_request')
            form_code = get_random_string(length=7)

            with connection.cursor() as cursor:
                cursor.execute("""
                INSERT INTO visitor_form (v_name, v_email, phone_number, request, form_code)
                VALUES(%s,%s,%s,%s,%s)
                """,[v_name,v_email,v_phone,v_request,form_code])
            request.session['form_code'] = form_code
            request.session['form_submitted'] = True
    return redirect ('common:welcome_page')
    # return render(request, 'common/welcome-page.html', {'form_submitted':True})

def guest_forms(request): #Guest Inquiries on Doctor Side
    try:
        doctor_id = request.session['logged_in_user']
    except KeyError:
        request.session['not_logged_in'] = True
        return redirect('common:authenticate_user')

    if request.method == 'POST':
        response = request.POST.get('response')
        form_num = request.POST.get('modal_id')

        with connection.cursor() as cursor:
            del_fnum = request.POST.get('deleted_form')
            if del_fnum is not None:  # deleting form
                cursor.execute("DELETE FROM visitor_form WHERE fid = %s", [del_fnum])
            else:  # inserting response and updating doctor id
                cursor.execute("UPDATE visitor_form SET response = %s, did = %s WHERE fid = %s", [response, doctor_id, form_num])

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT fid, v_name, v_email, request, response
            FROM visitor_form
            WHERE response IS NULL;
        """)
        
        if cursor.description is not None:
            form_data = cursor.fetchall()
            return render(request, 'doctorprofile/guests.html', {'forms': form_data, 'doctor_id': doctor_id})

    url = f'/doctor/guest_forms/'
    return redirect(url)

def edit_info(request):
    try:
        doctor_id = request.session['logged_in_user']
    except:
        request.session['not_logged_in'] = True
        return redirect('common:authenticate_user')

    if request.method == 'POST':
            # doctor_id = request.POST.get('doctor_id')
            # Staff Data
            fname = request.POST.get('fname')
            lname = request.POST.get('lname')
            address = request.POST.get('address')
            # Doctor Data
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            password = request.POST.get('password')
            # ##If they left password blank, keep their old one.
            # if password is None:
            #     with connection.cursor() as cursor:
            #         cursor.execute("SELECT password from doctor where did = %s", [doctor_id])
            #         password = cursor.fetchone()[0]
            # ##
            hashed_password=make_password(password)
            img = request.FILES.get('img')
            if img: #if new photo
                img_name = img.name
                img_path = default_storage.save(img_name, img)
            else: #get old photo
                with connection.cursor() as cursor:
                    cursor.execute("SELECT d_photo from doctor where did = %s", [doctor_id])
                    doctor = cursor.fetchone()[0]
                    encoded_path = doctor.tobytes()
                    img_path= encoded_path.decode('utf-8')
            with connection.cursor() as cursor:
                cursor.execute("SELECT eid from doctor where did = %s", [doctor_id])
                eid = cursor.fetchone()[0]
                cursor.execute("""UPDATE staff
                                    SET fname = %s, lname = %s, address = %s
                                    WHERE eid = %s""", [fname, lname, address, eid])
                cursor.execute("""UPDATE doctor
                                    SET email = %s, d_photo = %s, password = %s
                                    WHERE did = %s""", [email, img_path, hashed_password ,doctor_id])
            # target_url = f'/doctor/?doctor_id={doctor_id}'
            return redirect('doctorprofile:doctor-page')
    else:
        doctor_data, img_path = retrieve_doctor(doctor_id)
        return render(request, 'doctorprofile/edit-info.html', {'doctor_id': doctor_id, 'doctor':doctor_data, 'img_path':img_path})
        

def p_record(request):
    try:
        doctor_id = request.session['logged_in_user']
    except:
        request.session['not_logged_in'] = True
        return redirect('common:authenticate_user')
    
    with connection.cursor() as cursor:
        # cursor.execute(
        #      """
        #     SELECT 
        #     p.p_fname || ' ' || p.p_lname AS patient_name,
        #     p.pid,
        #     mh.diagnosis,
        #     mh.treatment,
        #     mh.dosage,
        #     mh.followup,
        #     mh.frequency
        #     FROM medical_history mh
        #     INNER JOIN patient p ON mh.pid = p.pid
        #     WHERE p.did = %s
        #     AND mh.mid = (SELECT MAX(mid) FROM medical_history where pid = p.pid);
        # """, [doctor_id])
        # latest_patientrecords = cursor.fetchall()

        # cursor.execute("""
        #     SELECT
        #     p.p_fname || ' ' || p.p_lname AS patient_name,
        #     p.pid, p.p_photo, p.phone_number, p.address, p.p_age, p.sex, p.email,
        #     mh.diagnosis,
        #     mh.treatment,
        #     mh.dosage,
        #     mh.followup,
        #     mh.frequency
        #     FROM medical_history mh
        #     INNER JOIN patient p ON mh.pid = p.pid
        #     WHERE p.did = %s
        #     ORDER BY mh.mid DESC;
        # """, [doctor_id])
        # all_patientrecords= cursor.fetchall()

        ##COMBINED QUERY##
        cursor.execute("""
            WITH latest_records AS (
                SELECT
                    p.p_fname || ' ' || p.p_lname AS patient_name,
                    p.pid,
                    p.p_photo,
                    p.phone_number,
                    p.address,
                    p.p_age,
                    p.sex,
                    p.email,
                    mh.diagnosis,
                    mh.treatment,
                    mh.dosage,
                    mh.followup,
                    mh.frequency,
                    mh.mid,
                    a.app_type,
                    a.app_date,
                    a.app_time
                FROM medical_history mh
                INNER JOIN patient p ON mh.pid = p.pid
                JOIN appointment a on mh.aid = a.aid
                WHERE p.did = %s
            )
            SELECT *
            FROM latest_records
            WHERE mid = (SELECT MAX(mid) FROM latest_records WHERE pid = latest_records.pid)

            UNION ALL

            SELECT *
            FROM latest_records
            WHERE mid != (SELECT MAX(mid) FROM latest_records WHERE pid = latest_records.pid)
            ORDER BY mid DESC;
        """, [doctor_id])
        records = cursor.fetchall()
        cursor.execute("""SELECT pid, p_photo FROM patient WHERE did =%s""",[doctor_id])
        encoded_paths_and_ids = cursor.fetchall()
        decoded_paths_and_ids = []
        for record in encoded_paths_and_ids:
            img_path_decoded = record[1].tobytes().decode('utf-8')
            patient_image = check_image(img_path_decoded)
            decoded_paths_and_ids.append((record[0],patient_image))
        print(f"Paths with IDS:{decoded_paths_and_ids}")
        
    # Separate the latest records and all records
    latest_patientrecords = []
    all_patientrecords = []
    seen_pids = set()
    for record in records:
        if record[1] not in seen_pids:
            latest_patientrecords.append(record)
            seen_pids.add(record[1])
        all_patientrecords.append(record)
    #print(all_patientrecords)
    try:
        if request.session['patient_notfound']:
            patient_not_found= True
    except:
            patient_not_found = False
    return render(request, 'doctorprofile/patientrecord.html', {'latest_patientrecords': latest_patientrecords, 'all_patientrecords':all_patientrecords, 'paths_with_ids':decoded_paths_and_ids, 'patient_not_found':patient_not_found, 'doctor_id':doctor_id})

def add_record(request):
    try:
        doctor_id = request.session['logged_in_user']
    except KeyError:
        request.session['not_logged_in'] = True
        return redirect('common:authenticate_user')

    if request.method == 'POST':
        pid = request.POST.get('pid')
        diagnosis = request.POST.get('diagnosis')
        treatment = request.POST.get('treatment')
        dosage = request.POST.get('dosage')
        next_app_status = request.POST.get('next_app_status')
        follow_up = request.POST.get('follow_up')
        frequency = request.POST.get('frequency')

        # Fetch patient's first and last name from the patient table
        with connection.cursor() as cursor:
            cursor.execute("SELECT p_fname, p_lname FROM patient WHERE pid = %s", [pid])
            patient = cursor.fetchone()
            if not patient:
                # Handle the case where the patient is not found
                request.session['patient_notfound'] = True
                return redirect('doctorprofile:patientrecord-page')

            first_name, last_name = patient
            cursor.execute("""SELECT MAX(aid)
                              FROM appointment
                              WHERE appointment_status = 'Completed'
                              AND pid = %s
                           """, [pid])
            aid_tuple = cursor.fetchone()
            aid = aid_tuple[0] if aid_tuple else None

            # Insert the new medical record
            cursor.execute(
                """
                INSERT INTO medical_history (pid, diagnosis, treatment, dosage, followup, frequency, did, aid, next_app_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [pid, diagnosis, treatment, dosage, follow_up, frequency, doctor_id, aid, next_app_status]
            )

    # Redirect to the patient records page after successful addition
    return redirect('doctorprofile:patientrecord-page')

def edit_record(request):
    pid = request.GET.get('pid')
    if request.method == "POST":
        # return HttpResponse('inside POST')
        # p_name = request.POST.get('p_name')
        diagnosis = request.POST.get('diagnosis')
        treatment = request.POST.get('treatment')
        dosage = request.POST.get('dosage')
        follow_up = request.POST.get('follow_up')
        frequency = request.POST.get('frequency')
        mid = request.POST.get('mid')
        with connection.cursor() as cursor:
            cursor.execute("""UPDATE medical_history
                           SET diagnosis= %s , treatment=%s, dosage=%s, followup=%s,frequency=%s
                           WHERE pid = %s 
                           AND mid = %s
                            """, [diagnosis,treatment,dosage,follow_up,frequency, pid, mid])
            # cursor.execute("SELECT did FROM patient WHERE pid = %s",[pid])
            # did=cursor.fetchone()[0]
        target_url = f'/doctor/patientrecord/'
        return redirect(target_url)
    
def appointments(request):
    completed_app = request.POST.get('completed_app')
    canceled_app = request.POST.get('canceled_app')

    try:
        doctor_id = request.session['logged_in_user']
    except:
        request.session['not_logged_in'] = True
        return redirect('common:authenticate_user')

    with connection.cursor() as cursor:
        if request.method == "POST":
            if completed_app is not None:
                cursor.execute("UPDATE appointment SET appointment_status = 'Completed' WHERE aid = %s", [completed_app])
            elif canceled_app is not None:
                cursor.execute("SELECT bid FROM appointment WHERE aid = %s", [canceled_app])
                cancelled_bid = cursor.fetchone()
                cursor.execute("UPDATE appointment SET appointment_status = 'Cancelled' WHERE aid = %s", [canceled_app])
                if cancelled_bid:
                    cursor.execute("UPDATE billing SET payment_status = 'Cancelled' WHERE bid = %s", [cancelled_bid])
        
        appointments = retrieve_appointments(doctor_id)
    
    return render(request, 'doctorprofile/appointments.html', {'appointments': appointments, 'doctor_id': doctor_id})



def retrieve_doctor(did):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.eid, s.fname,s.lname, d.did, d.d_specialization, d.email, d.d_photo, s.address, d.password, d.d_phone
            FROM staff s 
            JOIN doctor d ON s.eid = d.eid 
            WHERE s.role = 'Doctor' 
            AND d.did = %s
        """, [did])
        doctor = cursor.fetchone()
        if doctor:
            encoded_path = doctor[6].tobytes()
            try:
                img_path= encoded_path.decode('utf-8')
            except:
                final_image_path = '../../../media/default-image.jpg'
            final_image_path = check_image(img_path)
        else:
            #Return a better error message
            return HttpResponse('error')
    return doctor, final_image_path

def retrieve_appointments(did):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
            a.aid, p.p_fname, p.p_lname, a.app_date, a.app_time, a.app_type, a.rnum, a.appointment_status
            FROM appointment a
            JOIN patient p ON a.pid = p.pid
            WHERE a.did = %s AND a.appointment_status = 'coming';
            """, [did]
        )
        appointments = cursor.fetchall()
    return appointments

def check_image(img_path):
    default_image_path = '../../../media/default-image.jpg'

    actual_image_path = Path('media') / img_path
    # print(actual_image_path)
    if actual_image_path.exists():
        image_path = img_path
    else:
        image_path = default_image_path
    return image_path

#I TEST SOME PRINTS HERE DO NOT DELETE
# import base64
# from django.core.files.storage import default_storage
def test (request):
    # img = request.FILES.get('img')
    # if img:
    #     img_name = img.name
    #     img_path = default_storage.save(img_name, img)
    #     return HttpResponse(img_path)
    #         # encoded_path = doctor[6].tobytes()
    #         # img_path= encoded_path.decode('utf-8')
    # return render(request,'doctorprofile/test.html')




    password = make_password('pass123')
    hashed = 'pbkdf2_sha256$600000$OT9oWKU5A05bOsCaXM3ygP$cxtmxNljVX/6e3/OQPEY8L15g8pezf4Lwjil7al+gc0='
    # return HttpResponse(password)
    #return render(request, 'doctorprofile/test.html')
    return HttpResponse(password)
