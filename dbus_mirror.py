#!/usr/bin/env python
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    dbus_mirror.py: Listens for notifications on DBUS. Forwards them to
    PushBullet as ephemerals.

    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""

from __future__ import print_function
import platform
import argparse
import httplib
import urllib
import json
import glib
import dbus
from dbus.mainloop.glib import DBusGMainLoop


API_KEY = None
api_key = API_KEY
device_id = None
user_id = None


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('api_key')
    return parser.parse_args()


def register():
    headers = {'Authorization': 'Bearer %s' % api_key,
               'Content-type': 'application/x-www-form-urlencoded'}
    data = urllib.urlencode({
        'nickname': platform.node(),
        'type': 'stream'
    })
    conn = httplib.HTTPSConnection('api.pushbullet.com')
    conn.request('GET', '/v2/users/me', '', headers)
    response = conn.getresponse()
    out = response.read()
    print(headers, out)
    out_json = json.loads(out)
    _user_id = out_json['iden']
    conn.request('POST', '/v2/devices', data, headers)
    response = conn.getresponse()
    out = response.read()
    print(headers, data, out)
    out_json = json.loads(out)
    _device_id = out_json['iden']
    conn.close()
    return _user_id, _device_id


def mirror(bus, message):
    print(message.get_member())
    if message.get_member() != 'Notify':
        return
    print('message!')
    args = message.get_args_list()
    sender = args[0]
    if sender == 'me.odj.pushbullet.gtk':
        return
    notification_id = str(args[1])
    title = args[3]
    body = args[4]
    headers = {'Authorization': 'Bearer %s' % api_key,
               'Content-type': 'application/json'}
    data = json.dumps({'type': 'push', 'push': {
        'type': 'mirror',
        'package_name': 'me.odj.pushbullet.gtk',
        'notification_id': notification_id,
        'notification_tag': None,
        'source_user_iden': user_id,
        'source_device_iden': device_id,
        'dismissable': True,
        'has_root': False,
        'client_version': 0,
        'icon': None,
        'title': title,
        'body': body
    }})
    conn = httplib.HTTPSConnection('api.pushbullet.com')
    conn.request('POST', '/v2/ephemerals', data, headers)
    response = conn.getresponse()
    out = response.read()
    conn.close()
    print(headers, data, out)


if __name__ == '__main__':
    args = parse_args()
    api_key = args.api_key
    user_id, device_id = register()
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    bus.add_match_string_non_blocking(
        "eavesdrop=true, " +
        "interface='org.freedesktop.Notifications', " +
        "member='Notify'"
    )
    bus.add_message_filter(mirror)

    mainloop = glib.MainLoop()
    mainloop.run()

