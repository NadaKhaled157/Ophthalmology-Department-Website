from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns=[
path("", views.index, name="registeration-page"),
path('login/', views.authenticate_user, name='authenticate_user'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) #Check if it doesn't affect images in database
