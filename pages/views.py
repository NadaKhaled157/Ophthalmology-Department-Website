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
        # return HttpResponse(f"{img_name} + {img_path}")
        with connection.cursor() as cursor:
           cursor.execute("SELECT Email FROM useraccount WHERE Email = %s", [email])
           email_db = cursor.fetchone()
           if email_db:
                exist = "Email already exists!"
                return render(request, "pages/register.html", {'exist': exist})
                # return HttpResponse('''<h1 style="align-text:center; color:rgb(255,0,0);"> Email already exists! Login! </h1>''')
        if raw_password == raw_password_2:
            password= make_password(raw_password)
            with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO useraccount (Fname,Lname, Email, passward, address, phone, gender, image)
                        VALUES (%s, %s, %s,%s, %s, %s, %s, %s);
                    """, [first_name, last_name, email, password, address, phone_number, gender, img_path]) 
                    # Getting user ID
            with connection.cursor() as cursor:
                cursor.execute("""SELECT id
                               FROM useraccount
                               WHERE email = %s""", [email])
                id = cursor.fetchone()
            request.session['id']=id
            return redirect('profile')
        else:
            notmatch = "Passwords didn't match!"
            return render(request, "pages/register.html", {'match': notmatch})
            # return HttpResponse('''Password is incorrect.''')
    return render(request, "pages/register.html")

def login(request):
    return render(request, "pages/login.html")

def authenticate_user(request):
    # Clearing session and cookies
    request.session.flush()
    request.session.modified = True
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Execute the raw SQL query to fetch the user by email
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM useraccount WHERE email = %s", [email])
            user = cursor.fetchone()

        if user:
            # user[4] is the index of the password field
            hashed_password = user[4]

            # Use Django's check_password method to compare the passwords
            #if password == hashed_password:
            if check_password(password, hashed_password):
                # Password is correct, return the user object
                #return HttpResponse(user[8])
                # encoded_path = user[8].tobytes()
                # img_path= encoded_path.decode('utf-8')

                #request.session['email'] = email
                # redirect_path= reverse('profile',args=[user[0]])
                # return HttpResponseRedirect(redirect_path)
                request.session['id']=[user[0]]
                return redirect('profile')
            else:
                # return HttpResponse(f"{email}+{password}+{hashed_password}")
                # return HttpResponse("""    <div>
                #                             <h1 style='color:rgb(200,0,0)'>The password you entered is incorrect.</h1>
                #                             </div>""")
                wrong_pass = "Wrong Password"
                redirect('login-page')
                return render(request, "pages/login.html",{'wrong': wrong_pass})

        else:
            # # No user found with the provided email
            # return HttpResponse("""    <div>
            #                                 <h1 style='color:rgb(200,0,0)'>This user does not exist.<br>
            #                                 Please check your email or sign up for a new account.</h1>
            #                                 </div>""")
            wrong_email = "This user does not exist"
            return render(request, "pages/login.html",{'wrong': wrong_email})
    return render(request, "pages/login.html")

# def login_success(request,email):
    
#     return redirect(request, 'pages/profile.html', {'loginfo':user}) 

# def login_success(request):
#     user_record = request.session.get('user_record')
#     #MEDIA_URL = request.session.get('MEDIA_URL')
#     img_path = request.session.get('img_path')
#     # ... use 'user_record', 'MEDIA_URL', and 'img_path' as needed ...
#     return HttpResponseRedirect('profile',)

####PROFILE####

def profile(request):
    user_id = request.session.get('id')[0]
    if user_id:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM useraccount WHERE id = %s", [user_id])
            user = cursor.fetchone()
            cursor.execute("SELECT * FROM social WHERE id = %s", [user_id])
            accounts = cursor.fetchone()
            encoded_path = user[8].tobytes()
            img_path= encoded_path.decode('utf-8')
            cursor.execute("SELECT date , post from posts WHERE user_id = %s", [user_id])
            user_posts = cursor.fetchall()
        #return HttpResponse(f"{user_posts[0]}")

        return render(request, 'pages/profile.html', {'loginfo':user,'img_path':img_path,'acc':accounts, 'posts':user_posts}) 
    return HttpResponse("Email not found in session.")


# Editing user accounts
def edit(request):
    id = request.session.get('id')[0]
    if id:
        if request.method == 'POST':
            fb = request.POST.get('fb')
            ins = request.POST.get('ins')
            ln = request.POST.get('ln')
            git = request.POST.get('git')
            with connection.cursor() as cursor:
                cursor.execute("""SELECT id
                                FROM social
                                WHERE id = %s""", [id])
                result = cursor.fetchone()
                if result is None: result = ['dummy']
            res = [0]
            for i in range(len(result)):
                res[i] = result[i]
            if id in result:
                with connection.cursor() as cursor:
                    cursor.execute("""UPDATE social
                                    SET facebook = %s, instagram = %s, linkedin = %s, github = %s
                                    WHERE id = %s""", [fb, ins, ln, git, id])
            else:
                with connection.cursor() as cursor:
                    cursor.execute("""INSERT INTO social
                                    (id, facebook, github, instagram, linkedin)
                                    VALUES(%s, %s, %s, %s, %s)""",[id, fb, git, ins, ln])
            transaction.commit()
            return redirect('profile')
    return render(request, 'pages/edit.html')

# Editing user info
def editinfo(request):
    id = request.session.get('id')[0]
    if id:
        if request.method == 'POST':
            first = request.POST.get('first')
            last = request.POST.get('last')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            add = request.POST.get('add')
            with connection.cursor() as cursor:
                cursor.execute("""UPDATE useraccount
                                SET fname = %s, lname = %s, email = %s, phone = %s, address = %s
                                WHERE id = %s""", [first, last, email, phone, add, id])
            transaction.commit()
            return redirect('profile')
    return render(request, 'pages/editinfo.html')

def add_post(request):
    id = request.session.get('id')[0]
    if id:
        if request.method == "POST":
            # return HttpResponse("Gowa el If")
            post = request.POST.get('newpost')
            date = datetime.now().date()
            #return HttpResponse(date)
            with connection.cursor() as cursor:
                cursor.execute("""
                            INSERT INTO posts (user_id, date, post)
                        VALUES (%s, %s, %s);
                        """ , [id, date, post])
            return redirect('profile')
    return render (request, 'pages/addpost.html')

# def add_post_server(request):
#     id = request.session.get('id')[0]
#     if id:
#         if request.method == "POST":
#             # return HttpResponse("Gowa el If")
#             post = request.POST.get('newpost')
#             date = date(.today())
#             with connection.cursor() as cursor:
#                 cursor.execute("""
#                             INSERT INTO posts (user_id, date, post)
#                         VALUES (%s, %s, %s);
#                         """ , [id, date, post])
#             transaction.commit()
#     return redirect('profile')

