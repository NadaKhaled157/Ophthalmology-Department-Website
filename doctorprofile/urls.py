from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

app_name = 'doctorprofile'

urlpatterns=[
    path('', views.doctor_profile, name='doctor-page'),
    path('forms/', views.forms , name='forms'),
    # path('respond/', views.respond, name = 'respond'),

    path('test/', views.test),
]