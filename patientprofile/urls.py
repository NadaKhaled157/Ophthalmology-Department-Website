from django.urls import path
from . import views
app_name="patientprofile"
urlpatterns=[
path("pprofile", views.pprofile, name="patient-profile"),
path('appointment', views.appointment, name='appointment'),
path("history", views.history, name='history'),
path("contact", views.contact, name='contact'),
path("payment", views.payment, name='payment'),
path("edit", views.edit, name="edit"),
path("operation", views.operation, name="operation"),
path("doctor_response", views.doctor_response, name="doctor_response"),
path("available_time/<str:appointment_type>/", views.available_time, name="available_time"),
path("success_request", views.success_request, name="success_request"),
path("process_appointment", views.process_appointment, name="process_appointment"),
]
