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
    if request.method == 'POST':
        response = request.POST.get('response')
        form_num= request.GET.get('modal_id')
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO form (response) VALUES (%s) WHERE fnum = %s", [response, form_num])
        return
    with connection.cursor() as cursor:

        cursor.execute("""SELECT p.p_fname, p.p_lname, f.fnum, f.request,f.response
                        FROM patient AS p
                        INNER JOIN form AS f ON p.pid = f.pid;
                    """)
        form_data = cursor.fetchall()
    return render(request,'doctorprofile/forms.html',{'forms':form_data})


#I TEST SOME PRINTS HERE DO NOT DELETE
def test (request):
    password = make_password('docpass1')
    return HttpResponse(password)
