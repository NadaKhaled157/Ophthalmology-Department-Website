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
from django.contrib.auth import authenticate, login, logout


# Create your views here.
def index(request):
    # Clearing session and cookies
    request.session.flush()
    request.session.modified = True
    form = UserCreationForm()
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

def authenticate_user(request):
    # Clearing session and cookies
    not_logged_in = request.session.get('not_logged_in_alert', False)
    if not_logged_in == True:
        request.session['not_logged_in'] = False
        return render(request, "common/login.html", {'not_logged_in':not_logged_in})
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        if role == None: return render(request, "common/login.html",{'no_role': True})
        with connection.cursor() as cursor:        
            cursor.execute(f"SELECT * FROM {role} WHERE email = %s", [email])
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
                    request.session['logged_in_user'] = user[0]
                    return redirect(reverse('doctorprofile:doctor-page')+ f'?doctor_id={user[0]}') #user[0] is did
                if role == "patient":
                    return redirect(reverse('patientprofile:patient-page')+ f'?patient_id={user[0]}') ##Ensure patient app and view name match##
            else:
                wrong_pass = "Wrong Password"
                redirect('authenticate_user')
                return render(request, "common/login.html",{'wrong_pass': True, 'not_logged_in':not_logged_in})

        else:
            wrong_email = "This user does not exist"
            return render(request, "common/login.html",{'wrong_email': True, 'not_logged_in':not_logged_in})
    return render(request, "common/login.html", {'not_logged_in':not_logged_in})

from django.db import connection
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect


#Not implemented yet
def logout(request):
    request.session.flush()
    #Make it go to homepage
    return redirect('authenticate_user')

