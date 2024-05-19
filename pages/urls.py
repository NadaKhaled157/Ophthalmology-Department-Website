from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns=[
path("", views.index, name="registeration-page"),
path("login/", views.login, name="login-page"),
path('authenticate/', views.authenticate_user, name='authenticate_user'),
path('profile/', views.profile, name='profile'),
path('edit/', views.edit, name='edit'),
path('editinfo/', views.editinfo, name='editinfo'),
# path('authenticate/login_success/', views.login_success, name='login_success'),
path('addpost/', views.add_post, name='add-post'),
# path('addserver/', views.add_post_server, name ='add_post_server'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #Check if it doesn't affect images in database
