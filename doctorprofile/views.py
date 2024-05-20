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
    with connection.cursor() as cursor:
        # Fetch the info of the first doctor from the database
        cursor.execute(
            
            """
            SELECT s.eid, s.fname,s.lname, d.did, d.d_specialization, d.email 
            FROM staff s 
            JOIN doctor d ON s.eid = d.eid 
            WHERE s.role = 'doctor' 
            ORDER BY s.eid 
            LIMIT 1 
        """)
        doctor = cursor.fetchone()

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
            return render(request, 'doctorprofile/profile.html', {'doctor': doctor, 'availability': availability})
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
            elif status == 'pending':
                cursor.execute("""SELECT f.fnum, p.p_fname, p.p_lname, f.request,f.response, f.form_status
                        FROM patient AS p
                        INNER JOIN form AS f ON p.pid = f.pid
                        WHERE f.form_status = 'Pending';
                        """)
            if cursor.description is not None:
                form_data = cursor.fetchall()
                return render(request,'doctorprofile/profile.html',{'forms':form_data})

    # with connection.cursor() as cursor: #displaying forms related to this doctor
    #     cursor.execute("""SELECT p.p_fname, p.p_lname, f.fnum, f.request,f.response
    #                     FROM patient AS p
    #                     INNER JOIN form AS f ON p.pid = f.pid;
    #                     """)
    # return HttpResponse(form_data)    
    return render(request,'doctorprofile/profile.html')


#I TEST SOME PRINTS HERE DO NOT DELETE
def test (request):
    password = make_password('docpass1')
    return HttpResponse(password)
