from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from django.db import connection
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404



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
        age = request.POST.get('age')
        raw_password = request.POST.get('password')
        raw_password_2 = request.POST.get('confirm-password')
        gender = request.POST.get('gender')
        img = request.FILES.get('img')
        if img:
            img_name = img.name
            img_path = default_storage.save(img_name, img)
            request.session['img_path'] = img_path

        with connection.cursor() as cursor:
           cursor.execute("SELECT Email FROM patient WHERE Email = %s", [email])
           email_db = cursor.fetchone()
           if email_db:
                exist = "Email already exists!"
                return render(request, "common/register.html", {'exist': exist})
        if raw_password == raw_password_2:
            password= make_password(raw_password)
            with connection.cursor() as cursor:
                    ##EDIT BASED ON PATIENT TABLE##
                    cursor.execute("""
                        INSERT INTO patient (p_fname,p_lname, email, password, address, phone_number, sex, p_photo,p_age)
                        VALUES (%s, %s, %s,%s, %s, %s, %s, %s,  %s);
                    """, [first_name, last_name, email, password, address, phone_number, gender, img_path, age])

            with connection.cursor() as cursor:
                ##EDIT BASED ON PATIENT TABLE##
                cursor.execute("""SELECT pid, p_fname
                               FROM patient
                               WHERE email = %s""", [email])
                id, name = cursor.fetchone()
            request.session['id']=id
            request.session['name']=name

            return redirect('patientprofile:patient-profile')
        else:
            notmatch = "Passwords didn't match!"
            return render(request, "common/register.html", {'match': notmatch})
            # return HttpResponse('''Password is incorrect.''')
    else:
        return render(request, "common/register.html")

def login(request):
     return render(request, "common/login.html")

def authenticate_user(request):
    # Clearing session and cookies
    request.session.flush()
    request.session.modified = True

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        if role == None: return render(request, "common/login.html",{'no_role': True})
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {role} WHERE email = %s", [email])
            user = cursor.fetchone()
        if user:
            hashed_password = user[9]

            if check_password(password, hashed_password):
                request.session['id']=user[3] ##What is this??##
                request.session['name']= user[0]
                patient_photo= user[5].tobytes()
                img_path=patient_photo.decode('utf-8')
                request.session['img_path']=img_path
                if role == "doctor":
                    return redirect(reverse('doctorprofile:doctor-page')+ f'?doctor_id={user[0]}') #user[0] is did
                if role == "patient":
                    return redirect(reverse('patientprofile:patient-profile')+ f'?patient_id={user[3]}') ##pid

            else:
                wrong_pass = "Wrong Password"
                redirect('common:authenticate_user')
                return render(request, "common/login.html",{'wrong_pass': True})

        else:
            wrong_email = "This user does not exist"
            return render(request, "common/login.html",{'wrong_email': True})
