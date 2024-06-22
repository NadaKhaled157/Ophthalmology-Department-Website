from django.urls import path
from . import views
app_name="patientprofile"
urlpatterns=[
path("pprofile", views.pprofile, name="patient-profile"),
path('appointment', views.appointment, name='appointment'),
#path("history", views.history, name='history'),
path("contact", views.contact, name='contact'),
path("payment/<str:app_type>/<int:did>/<str:app_date>/<str:start_time>/<str:app_day>/", views.payment, name='payment'),
path("edit", views.edit, name="edit"),
path("operation", views.operation, name="operation"),
path("doctor_response", views.doctor_response, name="doctor_response"),
path("available_time/<str:appointment_type>/", views.available_time, name="available_time"),
path("success_request", views.success_request, name="success_request"),
path("process_appointment", views.process_appointment, name="process_appointment"),
path("success_payment", views.success_payment, name="success_payment"),
path("pay_visa/<int:fees>/<int:aid>", views.pay_visa, name="pay_visa"),
path("success_payment_visa", views.success_payment_visa, name="success_payment_visa"),

]
