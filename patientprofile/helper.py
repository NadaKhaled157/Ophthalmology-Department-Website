from datetime import date, timedelta
from datetime import datetime
from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU
from pathlib import Path
from django.db import connection
from django.core.files.storage import default_storage


def get_next_weekday(day_name):
    day_mapping = {
        'monday': 0,
        'tuesday': 1,
        'wednesday': 2,
        'thursday': 3,
        'friday': 4,
        'saturday': 5,
        'sunday': 6
    }

    today = date.today()
    today_weekday = today.weekday()

    # Find the target weekday
    target_weekday = day_mapping[day_name.lower().strip()]

    # Calculate the difference in days to the next target weekday
    days_ahead = target_weekday - today_weekday
    if days_ahead <= 0:
        days_ahead += 7

    next_weekday = today + timedelta(days=days_ahead)
    return next_weekday

def format_time(time_str):
    # Normalize the time string: remove periods and convert to lowercase
    normalized_time_str = time_str.replace('.', '').strip().lower()

    # Parse the normalized time string into a datetime object
    time_obj = datetime.strptime(normalized_time_str, "%I:%M %p")

    # Format the datetime object back to a string with the desired format
    formatted_time_str = time_obj.strftime("%I:%M %p").lower()

    # Ensure single digit hours have a leading zero
    if formatted_time_str[1] == ':':
        formatted_time_str = '0' + formatted_time_str

    return formatted_time_str


def is_future_date(date_str):
    try:
        given_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.today().date()
        return given_date >= today
    except ValueError:
        # Handle invalid date format
        print("Invalid date format. Please use 'YYYY-MM-DD'.")
        return False

def check_image(img_path):
    default_image_path = '../../../media/default-image.jpg'

    actual_image_path = Path('media') / img_path
    # print(actual_image_path)
    if actual_image_path.exists():
        image_path = img_path
    else:
        image_path = default_image_path
    return image_path

def retrieve_image(appointment_type,pid):
    if appointment_type == "examination" or appointment_type == "surgery":
        with connection.cursor() as cursor:
            if appointment_type == "examination":
                cursor.execute("""SELECT did, d_photo FROM doctor WHERE d_specialization not in ('Surgeon')""")
            if appointment_type == "surgery":
                cursor.execute("""SELECT did, d_photo FROM doctor WHERE d_specialization in ('Surgeon')""")
            encoded_paths_and_ids = cursor.fetchall()
            decoded_paths_and_ids = []
        for record in encoded_paths_and_ids:
            img_path_decoded = record[1].tobytes().decode('utf-8')
            patient_image = check_image(img_path_decoded)
            decoded_paths_and_ids.append((record[0],patient_image))

    elif appointment_type == "follow_up":
        with connection.cursor() as cursor:
            cursor.execute("""
                           SELECT d.did, d.d_photo
                           FROM doctor d
                           JOIN patient p on p.did = d.did
                           WHERE p.pid = %s""",[pid])
            encoded_paths_and_ids = cursor.fetchall()
            print(encoded_paths_and_ids)
            decoded_paths_and_ids = []
            img_path_decoded = encoded_paths_and_ids[0][1].tobytes().decode('utf-8')
            patient_image = check_image(img_path_decoded)
            decoded_paths_and_ids.append((encoded_paths_and_ids[0][0],patient_image))
    return decoded_paths_and_ids
