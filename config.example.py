""" Configuration Settings """

# Name of your application
application = 'Google Calendar iCal Sync'

# Secret downloaded from Google API console
client_secret = 'credentials.json'

# Credential storage cache (can be initially empty)
credential_store = 'logins.json'

# URL of a .ics file to import
ical_url = 'http://example.com/cal.ics'

# Google Calendar ID to write calendar to
# All events on this calendar will be erased
gcal_id = 'mygooglecalendar@gmail.com'

# Only events after this date will be added
start_date = '2016-01-01'