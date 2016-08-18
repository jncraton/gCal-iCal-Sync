#!/usr/bin/python

from __future__ import print_function
import httplib2
from dateutil.parser import parse
import re
import hashlib
from time import sleep

from apiclient import discovery, errors
import oauth2client
from oauth2client import client
from oauth2client import tools

import config

def get_credentials():
  """ Gets credentials to access gCal API """

  store = oauth2client.file.Storage(config.credential_store)
  credentials = store.get()
  if not credentials or credentials.invalid:
    flow = client.flow_from_clientsecrets(config.client_secret, 'https://www.googleapis.com/auth/calendar')
    flow.user_agent = config.application
    credentials = tools.run_flow(flow, store)
    print('Storing credentials to ' + config.credential_store)
  return credentials

def get_calendar_service():
  """ Gets a service object to use to query gCal API """

  credentials = get_credentials()
  http = credentials.authorize(httplib2.Http())
  return discovery.build('calendar', 'v3', http=http)

def load_ical(url):
  """ Loads an iCal file from a URL and returns an events object

  >>> events = load_ical("http://www.houghton.edu/calendar-events/icsexport/")
  >>> len(events) > 50
  True
  >>> 'summary' in events.itervalues().next()
  True
  >>> 'start' in events.itervalues().next()
  True
  >>> 'end' in events.itervalues().next()
  True
  """

  resp, content = httplib2.Http().request(url)
  assert(resp['status'] == '200')

  events = {}

  for event in re.findall("BEGIN:VEVENT.*?END:VEVENT", content, re.M|re.I|re.DOTALL):
    start = re.search("dtstart;TZID=(.*?):(.*)", event, re.I)
    end = re.search("dtend;TZID=(.*?):(.*)", event, re.I)
    summary = re.search("summary:(.*)", event, re.I).group(1)

    hash = hashlib.sha256("%s%s%s" % (start.group(2),end.group(2),summary)).hexdigest()

    if parse(start.group(2).replace('Z','')) >= parse(config.start_date):
      events[hash] = {
        'summary': summary,
        'start': {
          'dateTime': str(parse(start.group(2).replace('Z',''))).replace(' ','T'),
          'timeZone': start.group(1),
        },
        'end': {
          'dateTime': str(parse(end.group(2).replace('Z',''))).replace(' ','T'),
          'timeZone': end.group(1),
        },
        'id': hash
      }

  return events

def handle_existing_events(service, new_events):
  """ Examines existing gCal events and prunes as needed """

  if config.erase_all:
    print("Clearing calendar...")
    service.calendars().clear(calendarId=config.gcal_id).execute()

  for event in service.events().list(calendarId=config.gcal_id, maxResults=2500).execute()['items']:
    if event['id'] in new_events:
      del new_events[event['id']]
    elif config.remove_stale:
      print("Deleting stale event %s..." % (event['id'][0:8]))
      service.events().delete(calendarId=config.gcal_id, eventId=event['id']).execute()

def add_ical_to_gcal(service, events):
  """ Adds all events in event list to gCal """

  for i, event in enumerate(events):
    print("Adding %d/%d %s" % (i+1,len(events),events[event]['summary']))
    sleep(.3)
    try:
      service.events().insert(calendarId=config.gcal_id, body=events[event]).execute()
    except errors.HttpError, e:
      if e.resp.status == 409:
        print("Event already exists. Updating...")
        service.events().update(calendarId=config.gcal_id, eventId=event, body=events[event]).execute()
        print("Event updated.")
      else:
        raise e

if __name__ == '__main__':
  new_events = load_ical(config.ical_url)
  service = get_calendar_service()
  handle_existing_events(service, new_events)
  add_ical_to_gcal(service, new_events)
