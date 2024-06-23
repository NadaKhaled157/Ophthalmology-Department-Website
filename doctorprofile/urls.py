from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

app_name = 'doctorprofile'



urlpatterns=[
    path('', views.doctor_profile, name='doctor-page'),
    path('forms/', views.forms , name='forms'),
    path('editinfo/', views.edit_info, name='edit-info'),
    path('patientrecord/', views.p_record, name='patientrecord-page'),
    path('editrecord/', views.edit_record, name='edit-record'),
    path('appointments/', views.appointments, name='appointments-page'),
    path('add-record/', views.add_record, name="add-record"),
    path('visitor_form/', views.visitor_form, name="visitor-form"),
    path('guest_forms/',views.guest_forms,name='guest_forms'),

    path('test/', views.test,name='test'),
]