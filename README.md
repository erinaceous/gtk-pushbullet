gtk-pushbullet
--------------

This is a simple [PushBullet](https://www.pushbullet.com) client for FreeDesktop-compliant desktops (so, all the Linux and BSD ones, basically). It's written in Python. Should be compatible with both Python2 and Python3.

![Screenshot of gtk-pushbullet in action](http://i.imgur.com/z0NnIZJ.png)

The above screenshot shows `gtk-pushbullet` running (on the Awesome WM desktop environment), with three notifications from my phone being shown. One additional notification has been hidden. The pushbullet logo with a notifications counter can be seen in the icon tray, indicating the number of "live" notifications.

This client is *read-only*, meaning it cannot dismiss notifications on all your devices. All you can do is hide the notifications on your desktop locally -- they won't be cleared from your other devices. Right-clicking the tray icon brings up the "Show closed notifications" option, which will bring back all the notifications that haven't been dismissed on an Android/iPhone device.

Notifications automatically disappear when they're dismissed on your other devices.

Requirements
------------
* Python2 or Python3
* [PyGObject](https://wiki.gnome.org/PyGObject)
* [websocket-client](https://pypi.python.org/pypi/websocket-client/)
* Your PushBullet 'Access Token'. This can be seen on your [account page](https://www.pushbullet.com/account).

Running
-------
    cd path/to/gtk-pushbullet
    ./pushbullet <YOUR API KEY>

Simples :)

License
-------
My script is under the MIT license. It should be noted that it relies on PyGObject and websocket-client which are both LGPL, and it also makes use of the PushBullet Icon for the tray (which is probably under some kind of copyright! But they probably won't mind it being used for this...)
