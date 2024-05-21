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
    with connection.cursor() as cursor:
        # Fetch the info of the first doctor from the database
        # cursor.execute(
            
        #     """
        #     SELECT s.eid, s.fname,s.lname, d.did, d.d_specialization, d.email 
        #     FROM staff s 
        #     JOIN doctor d ON s.eid = d.eid 
        #     WHERE s.role = 'doctor' 
        #     ORDER BY s.eid 
        #     LIMIT 1 
        # """)
        cursor.execute(
            
            """
            SELECT s.eid, s.fname,s.lname, d.did, d.d_specialization, d.email, d.d_photo 
            FROM staff s 
            JOIN doctor d ON s.eid = d.eid 
            WHERE s.role = 'Doctor' 
            AND d.did = %s
        """, [doctor_id])
        doctor = cursor.fetchone()
        encoded_path = doctor[6].tobytes()
        img_path= encoded_path.decode('utf-8')
        # return HttpResponse(doctor)

        if doctor:
            doctor_id = doctor[3]  

            # Fetch the availability for the doctor
            cursor.execute("""
                SELECT day, start_time
                FROM availability 
                WHERE did = %s
            """, [doctor_id])
            availability = cursor.fetchall()
            print(doctor)
            print(availability)
            return render(request, 'doctorprofile/profile.html', {'doctor': doctor, 'availability': availability, 'img_path':img_path})
        else:
            return HttpResponse("No doctors found in the database.")

def forms(request):
    did = 17 ##Get DR ID from session##
    status = request.GET.get('status', 'all')  # 'all' is the default value if 'status' is not provided
    if request.method == 'POST':
        response = request.POST.get('response')
        form_num= request.POST.get('modal_id')
        # clicked_answered= request.POST.get('answered_forms')
        
        with connection.cursor() as cursor:
            del_fnum = request.POST.get('deleted_form')
            if del_fnum is not None:  #deleting form
                cursor.execute("DELETE from form where fnum = %s",[del_fnum])
            else: #inserting reponse
                cursor.execute("UPDATE form SET response = %s WHERE fnum = %s", [response, form_num])

    with connection.cursor() as cursor: #displaying forms related to this doctor
            if status =='answered':
                cursor.execute("""SELECT f.fnum, p.p_fname, p.p_lname, f.request,f.response, f.form_status
                        FROM patient AS p
                        INNER JOIN form AS f ON p.pid = f.pid
                        WHERE f.form_status = 'Answered';
                        """)
            else:
                cursor.execute("""SELECT f.fnum, p.p_fname, p.p_lname, f.request,f.response, f.form_status
                        FROM patient AS p
                        INNER JOIN form AS f ON p.pid = f.pid
                        WHERE f.form_status = 'Pending';
                        """)
            if cursor.description is not None:
                form_data = cursor.fetchall()
                return render(request,'doctorprofile/forms.html',{'forms':form_data})

    # with connection.cursor() as cursor: #displaying forms related to this doctor
    #     cursor.execute("""SELECT p.p_fname, p.p_lname, f.fnum, f.request,f.response
    #                     FROM patient AS p
    #                     INNER JOIN form AS f ON p.pid = f.pid;
    #                     """)
    # return HttpResponse(form_data)    
    return render(request,'doctorprofile/forms.html')

from django.shortcuts import render, redirect
from django.urls import reverse
from django.core.files.storage import default_storage
from django.db import connection

def edit_info(request):
    doctor_id = request.GET.get('doctor_id')
    if doctor_id:
        if request.method == 'POST':
            # Staff Data
            fname = request.POST.get('fname')
            lname = request.POST.get('lname')
            address = request.POST.get('address')
            # Doctor Data
            email = request.POST.get('email')
            img = request.FILES.get('img')
            if img:
                img_name = img.name
                img_path = default_storage.save(img_name, img)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT eid from doctor where did = %s", [doctor_id])
                    eid = cursor.fetchone()[0]
                    cursor.execute("""UPDATE staff
                                      SET fname = %s, lname = %s, address = %s
                                      WHERE eid = %s""", [fname, lname, address, eid])
                    cursor.execute("""UPDATE doctor
                                      SET email = %s, d_photo = %s
                                      WHERE did = %s""", [email, img_path, doctor_id])
            return redirect('doctorprofile:doctor-page')
        else:
            # Handle GET request here if necessary
            pass
    else:
        # Handle the case where doctor_id is not provided
        pass
    return render(request, 'doctorprofile/edit-info.html', {'doctor_id': doctor_id})



#I TEST SOME PRINTS HERE DO NOT DELETE
def test (request):
    password = make_password('docpass1')
    return HttpResponse(password)
