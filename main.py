#!/usr/bin/python

from __future__ import print_function
import httplib2
import os
from dateutil.parser import parse
import datetime
import re
import hashlib
from time import sleep

from apiclient import discovery, errors
import oauth2client
from oauth2client import client
from oauth2client import tools

import config

def get_credentials():
  store = oauth2client.file.Storage(config.credential_store)
  credentials = store.get()
  if not credentials or credentials.invalid:
    flow = client.flow_from_clientsecrets(config.client_secret, 'https://www.googleapis.com/auth/calendar')
    flow.user_agent = config.application
    credentials = tools.run_flow(flow, store)
    print('Storing credentials to ' + credential_path)
  return credentials

def get_calendar_service():
  credentials = get_credentials()
  http = credentials.authorize(httplib2.Http())
  return discovery.build('calendar', 'v3', http=http)

def load_ical(url):
  resp, content = httplib2.Http().request(url)
  assert(resp['status'] == '200')

  events = []

  for event in re.findall("BEGIN:VEVENT.*?END:VEVENT", content, re.M|re.I|re.DOTALL):
    start = re.search("dtstart;TZID=(.*?):(.*)", event, re.I)
    end = re.search("dtend;TZID=(.*?):(.*)", event, re.I)
    summary = re.search("summary:(.*)", event, re.I).group(1)

    hash = hashlib.sha256("%s %s %s" % (start.group(2),end.group(2),summary)).hexdigest()

    if parse(start.group(2).replace('Z','')) >= parse(config.start_date):
      events.append({
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
      })

  return events

def handle_existing_events(service, events):
  if config.erase_all:
    print("Clearing calendar...")
    service.calendars().clear(calendarId=config.gcal_id).execute()
  elif config.remove_stale:
    for event in service.events().list(calendarId=config.gcal_id, maxResults=2500).execute()['items']:
      if event['id'] not in [e['id'] for e in events]:
        print("Deleting stale event %s..." % (event['id'][0:8]))
        service.events().delete(calendarId=config.gcal_id, eventId=event['id']).execute()

def add_ical_to_gcal(service, events):
  for i, event in enumerate(events):
    print("Adding %d/%d %s" % (i+1,len(events),event['summary']))
    sleep(.3)
    try:
      service.events().insert(calendarId=config.gcal_id, body=event).execute()
    except errors.HttpError, e:
      if e.resp.status == 409:
        print("Event already exists")
      else:
        raise e

if __name__ == '__main__':
  events = load_ical(config.ical_url)
  service = get_calendar_service()
  handle_existing_events(service, events)
  add_ical_to_gcal(service, events)
