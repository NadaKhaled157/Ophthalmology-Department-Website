from django.urls import path
from . import views

urlpatterns=[
    path('', views.login, name = "login"),
    path('admin', views.admin_profile, name = "admin_profile"),
    path('role/', views.role, name = "role"),
    path('add_doc/', views.add_doc, name = "add_doc"),
    path('add_nur/', views.add_nur, name = "add_nur"),
    path('add_tech/', views.add_tech, name = "add_tech"),
    path('cancel/', views.cancel, name = "cancel"),
    path('rmv_doc/<int:id>/', views.rmv_doc, name = 'rmv_doc'),
    path('rmv_nur/<int:id>/', views.rmv_nur, name = 'rmv_nur'),
    path('rmv_tech/<int:id>/', views.rmv_tech, name = 'rmv_tech'),
    path('edit_nur/<int:id>/', views.edit_nur, name = "edit_nur"),
    path('edit_doc/<int:id>/', views.edit_doc, name = "edit_doc"),
    path('edit_tech/<int:id>/', views.edit_tech, name = "edit_tech"),
    path('available/<int:id>/', views.available, name = "available"),
    path('edit_availability/<int:id>/', views.edit_availability, name = "edit_availability"),
    path('add_shift/<int:id>/', views.add_shift, name = "add_shift"),
    path('cancel_shift/<int:id>/', views.cancel_shift, name = "cancel_shift"),
    path('cancel_edit/', views.cancel_edit, name = "cancel_edit"),
    path('delet/<int:id>?', views.delet_shift, name = "delet_shift"),

]