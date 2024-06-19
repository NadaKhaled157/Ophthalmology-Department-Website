from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

app_name = 'doctorprofile'

urlpatterns=[
    path('', views.doctor_profile, name='doctor-page'),
    path('forms/', views.forms , name='forms'),
    # path('forms/<str:status>', views.forms , name='forms'),
    path('editinfo/', views.edit_info, name='edit-info'),
    path('patientrecord/', views.p_record, name='patientrecord-page'),
    path('editrecord/', views.edit_record, name='edit-record'),
    path('appointments/', views.appointments, name='appointments-page'),
    # path('delete_appointment/<int:appointment_id>/', views.delete_appointment, name='delete_appointment'),
    # path('doctorprofile/', views.profile_front),
    # path('respond/', views.respond, name = 'respond'),

    path('test/', views.test),
]