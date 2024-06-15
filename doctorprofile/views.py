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

# Create your views here.
def doctor_profile(request):
    doctor_id = request.GET.get('doctor_id')
    # return HttpResponse(doctor_id)
    # with connection.cursor() as cursor:
    #     cursor.execute(
    #         """
    #         SELECT s.eid, s.fname,s.lname, d.did, d.d_specialization, d.email, d.d_photo 
    #         FROM staff s 
    #         JOIN doctor d ON s.eid = d.eid 
    #         WHERE s.role = 'Doctor' 
    #         AND d.did = %s
    #     """, [doctor_id])
    #     doctor = cursor.fetchone()
    doctor, img_path = retrieve_doctor(doctor_id)
        # return HttpResponse(doctor)
    # encoded_path = doctor[6].tobytes()
    # img_path= encoded_path.decode('utf-8')
        # return HttpResponse(doctor)

    if doctor:
        doctor_id = doctor[3] 
            # Fetch the availability for the doctor
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT day, start_time
                FROM availability 
                WHERE did = %s
            """, [doctor_id])
            availability = cursor.fetchall()
        print(doctor)
        print(availability)
        return render(request, 'doctorprofile/profile.html', {'doctor': doctor, 'availability': availability, 'img_path':img_path,'doctor_id':doctor_id})
    else:
            return HttpResponse("No doctors found in the database.")

def forms(request):
    did = request.GET.get('doctor_id') ##Get DR ID from session##
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
            if status =='answered':
                cursor.execute("""SELECT f.fnum, p.p_fname, p.p_lname, f.request, f.response, f.form_status
                                FROM patient AS p
                                INNER JOIN form AS f ON p.pid = f.pid
                                INNER JOIN doctor AS d ON d.did = f.did
                                WHERE f.form_status = 'Answered' AND d.did = %s;
                        """,[did])
            else:
                cursor.execute("""SELECT f.fnum, p.p_fname, p.p_lname, f.request, f.response, f.form_status
                                FROM patient AS p
                                INNER JOIN form AS f ON p.pid = f.pid
                                INNER JOIN doctor AS d ON d.did = f.did
                                WHERE f.form_status = 'Pending' AND d.did = %s;
                        """,[did])
            if cursor.description is not None:
                form_data = cursor.fetchall()
                return render(request,'doctorprofile/forms.html',{'forms':form_data,'doctor_id':did})
    return render(request,'doctorprofile/forms.html')

def edit_info(request):
    doctor_id = request.GET.get('doctor_id')
    if request.method == 'POST':
            doctor_id = request.POST.get('doctor_id')
            # Staff Data
            fname = request.POST.get('fname')
            lname = request.POST.get('lname')
            address = request.POST.get('address')
            # Doctor Data
            email = request.POST.get('email')
            password = request.POST.get('password')
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
            target_url = f'/doctor/?doctor_id={doctor_id}'
            return redirect(target_url)
    else:
        doctor_data, img_path = retrieve_doctor(doctor_id)
    ##not sure why we're getting eid?
    # with connection.cursor() as cursor:
    #             cursor.execute("SELECT eid from doctor where did = %s", [doctor_id])
    ##
        return render(request, 'doctorprofile/edit-info.html', {'doctor_id': doctor_id, 'doctor':doctor_data, 'img_path':img_path})

def p_record(request):
    doctor_id = request.GET.get('doctor_id')
    with connection.cursor() as cursor:
        cursor.execute(
             """
            SELECT 
            p.p_fname || ' ' || p.p_lname AS patient_name,
            p.pid,
            mh.diagnosis,
            mh.treatment,
            mh.dosage,
            mh.followup,
            mh.frequency
        FROM medical_history mh
        INNER JOIN patient p ON mh.pid = p.pid
        WHERE p.did = %s;
        """, [doctor_id])
        patientrecord = cursor.fetchall()
        print(patientrecord)
    return render(request, 'doctorprofile/patientrecord.html', {'patientrecord': patientrecord,'doctor_id':doctor_id})

def edit_record(request):
    pid = request.GET.get('pid')
    # return HttpResponse(pid)
    if request.method == "POST":
        # return HttpResponse('inside POST')
        p_name = request.POST.get('p_name')
        # pid = request.POST.get('pid')
        diagnosis = request.POST.get('diagnosis')
        treatment = request.POST.get('treatment')
        dosage = request.POST.get('dosage')
        follow_up = request.POST.get('follow_up')
        frequency = request.POST.get('frequency')
        with connection.cursor() as cursor:
            cursor.execute("""UPDATE medical_history
                           SET diagnosis= %s , treatment=%s, dosage=%s, followup=%s,frequency=%s
                           WHERE pid = %s
                            """, [diagnosis,treatment,dosage,follow_up,frequency, pid])
            cursor.execute("SELECT did FROM patient WHERE pid = %s",[pid])
            did=cursor.fetchone()
            # return HttpResponse(pid)
        target_url = f'/doctor/patientrecord/?doctor_id={did[0]}'
        return redirect(target_url)
    
def appointments(request):
    did= request.GET.get('doctor_id')
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
             a.aid,a.app_date, a.app_time, a.app_type, a.rnum,
                p.p_fname, p.p_lname, p.p_age
            FROM appointment a
            INNER JOIN patient p ON a.pid = p.pid
            INNER JOIN doctor d ON p.did = d.did
            WHERE d.did= %s;
            """, [did]
        )
        appointments = cursor.fetchall()
        print(appointments)
    return render(request, 'doctorprofile/appointments.html', {'appointments': appointments, 'doctor_id':did})

def delete_appointment(request, appointment_id):
    # with connection.cursor() as cursor:
    #     try:
    #         cursor.execute("DELETE FROM appointment WHERE aid = %s", [appointment_id])
    #         if cursor.rowcount > 0:
    #             return JsonResponse({'message': 'Appointment deleted successfully.'}, status=200)
    #         else:
    #             return JsonResponse({'message': 'Appointment not found.'}, status=404)
    #     except Exception as e:
    #         return JsonResponse({'message': 'Error deleting appointment.', 'error': str(e)}, status=500)
        
     with connection.cursor() as cursor:
            cursor.execute("DELETE FROM appointment WHERE aid = %s", [appointment_id])
            if cursor.rowcount > 0:
                return redirect('doctorprofile:doctor-page')
            return redirect('doctorprofile:doctor-page')

#I TEST SOME PRINTS HERE DO NOT DELETE
def test (request):
    password = make_password('hiddenkey4')
    hashed = 'pbkdf2_sha256$600000$3oJ0vg82JcBTYcKMllLsFw$MPpv8qXMvhKLsa7/yJPqpRgjrRLxdqhmDmyURjIkqF8='
    # return HttpResponse(password)
    return render(request, 'doctorprofile/test.html')
    # return HttpResponse(check_password(password, hashed))

def retrieve_doctor(did):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.eid, s.fname,s.lname, d.did, d.d_specialization, d.email, d.d_photo, s.address, d.password
            FROM staff s 
            JOIN doctor d ON s.eid = d.eid 
            WHERE s.role = 'Doctor' 
            AND d.did = %s
        """, [did])
        doctor = cursor.fetchone()
        encoded_path = doctor[6].tobytes()
        img_path= encoded_path.decode('utf-8')
    return doctor, img_path
