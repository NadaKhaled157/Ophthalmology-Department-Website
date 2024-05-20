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
def index(request):
    # Clearing session and cookies
    request.session.flush()
    request.session.modified = True
    img_path = None 
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone_number = request.POST.get('number')
        address = request.POST.get('address')
        email = request.POST.get('email')
        raw_password = request.POST.get('password')
        raw_password_2 = request.POST.get('confirm-password')
        gender = request.POST.get('gender')
        img = request.FILES.get('img')
        if img:
            img_name = img.name
            img_path = default_storage.save(img_name, img)
        with connection.cursor() as cursor:
           cursor.execute("SELECT Email FROM useraccount WHERE Email = %s", [email])
           email_db = cursor.fetchone()
           if email_db:
                exist = "Email already exists!"
                return render(request, "common/register.html", {'exist': exist})
        if raw_password == raw_password_2:
            password= make_password(raw_password)
            with connection.cursor() as cursor:
                    ##EDIT BASED ON PATIENT TABLE##
                    cursor.execute("""
                        INSERT INTO patient (Fname,Lname, Email, passward, address, phone, gender, image)
                        VALUES (%s, %s, %s,%s, %s, %s, %s, %s);
                    """, [first_name, last_name, email, password, address, phone_number, gender, img_path]) 
                
            with connection.cursor() as cursor:
                ##EDIT BASED ON PATIENT TABLE##
                cursor.execute("""SELECT id
                               FROM useraccount
                               WHERE email = %s""", [email])
                id = cursor.fetchone()
            request.session['id']=id
            return redirect('profile')
        else:
            notmatch = "Passwords didn't match!"
            return render(request, "common/register.html", {'match': notmatch})
            # return HttpResponse('''Password is incorrect.''')
    else:
        return render(request, "common/register.html")

# def login(request):
#     return render(request, "common/login.html")

def authenticate_user(request):
    # Clearing session and cookies
    request.session.flush()
    request.session.modified = True

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        with connection.cursor() as cursor:
            ##Add if condition of radio button (is user a patient or doctor?)##
            cursor.execute(f"SELECT * FROM {role} WHERE email = %s", [email])
            ##
            user = cursor.fetchone()
        if user:
            ##Add if condition of radio button (is user a patient or doctor?)##
            ##and get password index from the different tables to validate password##
            hashed_password = user[4]
            # return HttpResponse(check_password(password, hashed_password))
            ##
            if check_password(password, hashed_password):
            # if (password==hashed_password):
                request.session['id']=[user[0]] ##What is this??##
                # request.session['id']= user[2]
                if role == "doctor":
                    return redirect(reverse('doctorprofile:doctor-page'))
                if role == "patient":
                    return redirect(reverse('patientprofile:patient-page')) ##Ensure patient app and view name match##
            else:
                wrong_pass = "Wrong Password"
                redirect('authenticate_user')
                return render(request, "common/login.html",{'wrong': wrong_pass})

        else:
            wrong_email = "This user does not exist"
            return render(request, "common/login.html",{'wrong': wrong_email})
    return render(request, "common/login.html")

