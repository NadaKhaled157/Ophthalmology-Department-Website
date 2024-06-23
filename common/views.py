from django.shortcuts import render, redirect
from django.db import connection
from django.db import connection
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.hashers import make_password
from django.core.files.storage import default_storage
from django.db import connection
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404



def welcome_page(request):
    try:
        form_submitted = request.session['form_submitted']
        form_code = request.session['form_code']
        response = request.session['response']
    except:
        form_submitted = False
        form_code = None
        response = False
    if response:
        inquiry = request.session['retrieved_inquiry']
        return render(request, 'common/welcome-page.html',{'form_submitted':form_submitted,'form_code':form_code,'inquiry':inquiry,'response':True})
    # except:
        # return render(request, 'common/welcome-page.html',{'form_submitted':False,'response':None})
    return render(request, 'common/welcome-page.html',{'form_submitted':form_submitted,'form_code':form_code, 'response':None})

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

def authenticate_user(request):
    not_logged_in = request.session.get('not_logged_in', False)
    if not_logged_in == True:
        request.session['not_logged_in'] = False
        return render(request, "common/login.html", {'not_logged_in':True})
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
            if role == "doctor":
                hashed_password = user[4]
            elif role =='patient':
                hashed_password = user[9]
                
            ##
            if check_password(password, hashed_password):
            # if (password==hashed_password):
                 ##What is this??##
                # request.session['id']= user[2]
                if role == "doctor":
                    request.session['id']=[user[0]]
                    request.session['logged_in_user'] = user[0]
                    return redirect('doctorprofile:doctor-page') #user[0] is did
                if role == "patient":
                    request.session['id']=user[3]
                    request.session['name']= user[0]
                    patient_photo= user[5].tobytes()
                    img_path=patient_photo.decode('utf-8')
                    request.session['img_path']=img_path
                    return redirect('patientprofile:patient-profile') ##Ensure patient app and view name match##
            else:
                wrong_pass = "Wrong Password"
                redirect('common:authenticate_user')
                return render(request, "common/login.html",{'wrong_pass': True})
                redirect('common:authenticate_user')
                return render(request, "common/login.html",{'wrong_pass': True})

        else:
            wrong_email = "This user does not exist"
            return render(request, "common/login.html",{'wrong_email': True})
    return render(request, "common/login.html")




#Not implemented yet
def logout(request):
    request.session.flush()
    #Make it go to homepage
    return redirect('common:welcome_page')

