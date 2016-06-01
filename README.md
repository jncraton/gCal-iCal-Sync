# gCal-iCal-Sync

[![Build status](https://travis-ci.org/jncraton/gCal-iCal-Sync.png)](https://travis-ci.org/jncraton/gCal-iCal-Sync)

Syncs a public iCal URL to a Google Calendar. On each run, this program will add events to a Google calendar from an iCal (.ics) provided as a URL. This can optionally remove all events from the calendar not found in the iCal file to create a Google calendar that is an exact copy of another available calendar.

# Installation

Assuming that you have Python and pip install correctly, you should be able to install required dependencies using:

    pip install -r requirements.txt

# Configuration

See config.example.py for an example configuration.
