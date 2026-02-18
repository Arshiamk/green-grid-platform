import os
import sys
import django

print("Checking environment...")
print(f"Current working directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

print("Importing settings...")
from django.conf import settings
try:
    print(f"SECRET_KEY: {settings.SECRET_KEY[:5]}...")
except Exception as e:
    print(f"Error accessing SECRET_KEY: {e}")

print("Importing apps...")
try:
    django.setup()
    print("Django setup successful!")
except Exception as e:
    print(f"Django setup failed: {e}")
    import traceback
    traceback.print_exc()

print("Checking communications module...")
try:
    import communications
    print(f"communications imported from: {communications.__file__}")
except Exception as e:
    print(f"Failed to import communications: {e}")

print("Checking rest_framework_simplejwt...")
try:
    import rest_framework_simplejwt
    print(f"simplejwt imported from: {rest_framework_simplejwt.__file__}")
except Exception as e:
    print(f"Failed to import simplejwt: {e}")

print("Checking stripe...")
try:
    import stripe
    print(f"stripe imported from: {stripe.__file__}")
except Exception as e:
    print(f"Failed to import stripe: {e}")
