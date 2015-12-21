"""
asynchronous_obex_push.py

OBEX client class for sending objects to OBEX server.

Copyright (C) 2015 Bookjan <johnsonsu@iis.sinica.edu.tw>

This file is part of the LBeacon Python package.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from bluetooth import *
from PyOBEX.client import Client
from threading import Thread

import select
import time


class OBEX_Pusher(DeviceDiscoverer):

    def pre_inquiry(self):
        self.inquiry_time_start = time.time()
        self.done = False
        self.discovered_address = []
        self.signal_strength = -100
        print "Inquiry Start!"

    def device_discovered(self, address, device_class, rssi, name):
        found_time = time.time()
        print ("|- Found a device: Time[ %f ] %s RSSI[ %s ] Name[ %s ]" %
               (found_time - self.inquiry_time_start, address, rssi, name))
        if rssi > self.signal_strength:
            if address not in self.discovered_address:
                self.discovered_address.append(address)
                print "   |- Start a OBJECT PUSH process"
                try:
                    print "   |- Created a Thread"
                    Thread(target=self.object_push, args=(address,)).start()
                except Exception as e:
                    print e
        else:
            print "   |- The device's bluetooth signal strength is not good."

    def object_push(self, address):
        print '      |- Finding the OBEX_OBJPUSH service from %s' % address
        services = find_service(address=address, uuid=OBEX_OBJPUSH_CLASS)
        if services:
            channel = services[0]['port']
            client = Client(address, channel)
            print '      |- OBEX_OBJPUSH Channel is %s' % channel
            try:
                client.connect()
                client.put('message.txt', 'Hello World!')
                client.disconnect()
            except IOError as e:
                print e
        else:
            print '      |- NO OBEX_OBJPUSH PROFILE!!'

    def inquiry_complete(self):
        self.inquiry_time_end = time.time()
        self.done = True
        print "Inquiry Completed!"
        print ("  Inquiry Time - [ %f ]" %
               (self.inquiry_time_end - self.inquiry_time_start))
        print ("  Found %d devices" % len(self.discovered_address))
        print "  Discovered Bluetooth Address with OBEX PUSH PROFILE:"
        print self.discovered_address

op = OBEX_Pusher(device_id=1)
op.find_devices(lookup_names=False, duration=8, flush_cache=True)

readfiles = [op, ]

while True:
    rfds = select.select(readfiles, [], [])[0]

    if op in rfds:
        op.process_event()

    if op.done:
        break
