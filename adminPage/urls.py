from django.urls import path
from . import views

from django.conf import settings

urlpatterns=[
    path('dashboard/', views.admin_profile, name = "admin_profile"),
    path('hire', views.hire, name = "hire"),
    path('remove/<int:item_id>/', views.remove_staff, name='remove_staff'),
]