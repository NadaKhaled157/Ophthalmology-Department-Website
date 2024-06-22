from django.urls import path, include
from . import views

from django.conf import settings
from django.conf.urls.static import static
app_name ='common'
urlpatterns=[
path("register/", views.index, name="registeration-page"),
path('login/', views.authenticate_user, name='authenticate_user'),
path('logout/', views.logout, name='logout'),
path('', views.welcome_page, name="welcome_page"),
# path('#contact/', views.welcome_page, name="contact"),
# path("accounts/", include(django.contrib.auth.urls))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #Check if it doesn't affect images in database
