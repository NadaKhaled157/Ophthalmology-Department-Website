from django.urls import path
from . import views

urlpatterns=[
    path('', views.admin_profile, name = "admin_profile"),
    path('hire/', views.hire, name = "hire"),
    path('fire/<int:id>/', views.fire, name = 'fire'),
    path('edit_emp/<int:id>/', views.edit_emp, name = "edit_emp"),
]