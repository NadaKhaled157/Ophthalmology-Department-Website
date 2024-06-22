print("Script started")
from django.contrib.auth.hashers import make_password
# DJANGO_SETTINGS_MODULE=MySufferingQL.settings.py

# The password you want to hash
password = 'docpass1'

# Hash the password
hashed_password = make_password(password)

print(hashed_password)