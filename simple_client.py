#!/usr/bin/env python
# vim: set tabstop=4 shiftwidth=4 textwidth=79 cc=72,79:
"""
    pushbullet_client.py: Simple PushBullet websocket client that uses
    GObject Introspection to create notifications with images.

    The client is read-only; meaning when you dismiss notifications on
    the desktop, they're just hidden on that computer. Only when you
    swipe them away on Android devices / the website, do notifications
    truly get deleted. This is intentional.

    Uses the websocket-client PIP package:
    https://pypi.python.org/pypi/websocket-client/
    and PyGObject:
    https://wiki.gnome.org/PyGObject

    What license I should be using for my own code is a bit fuzzy;
    websocket-client and PyGObject are both LGPL. BUT this script itself
    is under the permissive MIT license.

    Original Author: Owain Jones [github.com/erinaceous] [contact@odj.me]
"""

from __future__ import print_function
from gi.repository import Notify, GdkPixbuf, Gio, GLib, GObject, Peas, PeasGtk, Gtk
import threading
import websocket
import argparse
import httplib
import urllib
import base64
import time
import json


API_KEY = None
STREAM = 'wss://stream.pushbullet.com/websocket/{api_key}'
ICON_FORMAT = '/usr/share/icons/pushbullet/pushbullet{num}.png'


notifications = {}
tray = None
wst = None
api_key = API_KEY


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('api_key')
    return parser.parse_args()


class TrayIcon(GObject.Object, Peas.Activatable):
    __gtype_name__ = 'TrayIcon'
    object = GObject.property(type=GObject.Object)

    def do_activate(self):
        self.staticon = Gtk.StatusIcon()
        self.change_icon()
        self.staticon.connect("activate", self.trayicon_activate)
        self.staticon.connect("popup_menu", self.trayicon_popup)
        self.staticon.set_visible(True)

    def change_icon(self, num=0):
        if num < 0:
            num = 0
        elif num > 9:
            num = 10
        self.staticon.set_from_file(ICON_FORMAT.format(num=num))

    def trayicon_activate(self, widget, data=None):
        for notification in notifications.values():
            notification.show()

    def trayicon_clear(self, widget, data=None):
        keys = list(notifications.keys())
        for ident in keys:
            notifications[ident].close()
            del notifications[ident]
        tray.change_icon(len(notifications))

    def trayicon_quit(self, widget, data=None):
        exit()

    def trayicon_popup(self, widget, button, time, data=None):
        self.menu = Gtk.Menu()
        menuitem_show = Gtk.MenuItem("Show closed notifications")
        menuitem_clear = Gtk.MenuItem("Clear notifications")
        menuitem_quit = Gtk.MenuItem("Quit")
        menuitem_show.connect("activate", self.trayicon_activate)
        menuitem_clear.connect("activate", self.trayicon_clear)
        menuitem_quit.connect("activate", self.trayicon_quit)
        self.menu.append(menuitem_show)
        self.menu.append(menuitem_clear)
        self.menu.append(menuitem_quit)
        self.menu.show_all()
        self.menu.popup(
            None, None,
            lambda w, x: self.staticon.position_menu(self.menu, self.staticon),
            self.staticon, 3, time)

    def do_deactivate(self):
        self.staticon.set_visible(False)
        del self.staticon


def dismiss(notification, iden, *args):
    source_user_id, source_device_id, notification_id = iden.split('_')
    headers = {'Authorization': 'Bearer %s' % api_key,
               'Content-type': 'application/json'}
    data = json.dumps({'type': 'push', 'push': {
        'type': 'dismissal',
        'package_name': 'me.odj.pushbullet.gtk',
        'notification_id': notification_id,
        'notification_tag': None,
        'source_user_iden': source_user_id
    }})
    conn = httplib.HTTPSConnection('api.pushbullet.com')
    conn.request('POST', '/v2/ephemerals', data, headers)
    response = conn.getresponse()
    out = response.read()
    conn.close()
    print(headers, data, out)


def notify(title, description, iden, icon=None):
    if iden in notifications.keys():
        notification = notifications[iden]
        notification.update(title, description)
    else:
        notification = Notify.Notification.new(title, description)
        notification.add_action(iden, "Dismiss", dismiss, None, None)
    notification.set_timeout(0)
    notification.set_urgency(Notify.Urgency.LOW)

    if icon is not None:
        pbl = GdkPixbuf.PixbufLoader()
        pbl.write(bytes(base64.b64decode(icon)))
        pbl.close()
        notification.set_icon_from_pixbuf(pbl.get_pixbuf())

    notifications[iden] = notification
    notification.show()


def on_message(ws, message):
        if type(message) == bytes:
            message = message.decode(encoding='UTF-8')
        message = json.loads(message)
        if message['type'] == 'push':
            push = message['push']
            ident = '_'.join([
                push['source_user_iden'], push['source_device_iden'],
                push['notification_id']
            ])
            if push['type'] == 'mirror':
                icon = None
                if 'icon' in push.keys():
                    icon = push['icon']
                title = push['application_name']
                if 'title' in push.keys():
                    title = '%s: %s' % (push['application_name'],
                                        push['title'])
                notify(title, push['body'], ident, icon)
            elif push['type'] == 'dismissal':
                if ident in notifications.keys():
                    notifications[ident].close()
                    del notifications[ident]
        tray.change_icon(len(notifications))


class WebSocketThread(threading.Thread):
    def __init__(self, api_key=API_KEY):
        threading.Thread.__init__(self)
        self.daemon = True
        self.api_key = api_key

    def run(self):
        while True:
            ws = websocket.WebSocketApp(STREAM.format(api_key=self.api_key),
                                        on_message=on_message)
            ws.run_forever()
            time.sleep(1)


if __name__ == '__main__':
    args = parse_args()
    Notify.init("me.odj.pushbullet.gtk")
    tray = TrayIcon()
    tray.do_activate()
    api_key = args.api_key
    wst = WebSocketThread(api_key=args.api_key)
    wst.start()
    Gtk.main()
