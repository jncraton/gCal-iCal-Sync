#!/usr/bin/python

from __future__ import print_function
import httplib2
import os
from dateutil.parser import parse
import datetime
import re

from apiclient import discovery
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

def main():
    resp, content = httplib2.Http().request(config.ical_url)
    assert(resp['status'] == '200')

    events = []

    for event in re.findall("BEGIN:VEVENT.*?END:VEVENT", content, re.M|re.I|re.DOTALL):
        start = re.search("dtstart;TZID=(.*?):(.*)", event, re.I)
        end = re.search("dtend;TZID=(.*?):(.*)", event, re.I)
        summary = re.search("summary:(.*)", event, re.I).group(1)

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
          })

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    assert(service.calendarList().get(calendarId='primary').execute()['id'] == config.gcal_id)

    print("Clearing calendar...")
    service.calendars().clear(calendarId=config.gcal_id).execute()

    for i, event in enumerate(events):
      print("Adding %d/%d %s" % (i+1,len(events),event['summary']))
      service.events().insert(calendarId=config.gcal_id, body=event).execute()

if __name__ == '__main__':
    main()