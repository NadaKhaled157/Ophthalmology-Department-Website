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

    path('test/', views.test),
]