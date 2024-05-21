from django.urls import path
from . import views

urlpatterns=[
    path('', views.admin_profile, name = "admin_profile"),
    path('fire/<int:id>/', views.fire, name = 'fire'),
    path('edit_emp/<int:id>/', views.edit_emp, name = "edit_emp"),
    path('role/', views.role, name = "role"),
    path('add_doc/', views.add_doc, name = "add_doc"),
    path('add_nur/', views.add_nur, name = "add_nur"),
    path('add_tech/', views.add_tech, name = "add_tech"),
    path('cancel/', views.cancel, name = "cancel"),
]