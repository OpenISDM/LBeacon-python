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
from lxml import etree

import select
import time
import itertools
import dbus

import logging


class OBEX_Pusher(DeviceDiscoverer):

    def pre_inquiry(self):
        self.inquiry_time_start = time.time()
        self.done = False
        self.discovered_address = []
        self.OBEX_UUID = '00001105-0000-1000-8000-00805f9b34fb'
        self.CHANNEL_XPATH = etree.XPath(
            "/record/attribute[@id='0x0004']/sequence/sequence/uuid[@value='0x0003']/../uint8/@value")
        self.local_bdaddrs = {
            "hci1": "00:1A:7D:DA:71:02", "hci0": "00:1A:7D:DA:71:03"}
        self.current_hci = itertools.cycle(self.local_bdaddrs)
        self.signal_strength = -80
        print ("Inquiry Start!")

    def device_discovered(self, address, device_class, rssi, name):
        found_time = time.time()
        print ("|- Found a device: Time[ %f ] %s RSSI[ %s ] Name[ %s ]" %
               (found_time - self.inquiry_time_start, address, rssi, name))
        if rssi > self.signal_strength:
            if address not in self.discovered_address:
                self.discovered_address.append(address)
                try:
                    hci = next(self.current_hci)
                    bus = dbus.SystemBus()
                    manager = dbus.Interface(bus.get_object(
                        "org.bluez", "/"), "org.bluez.Manager")
                    adapter = dbus.Interface(bus.get_object("org.bluez", manager.FindAdapter(hci)),
                                             "org.bluez.Adapter")
                    # print ("   |- Created a Thread for OBJECT PUSH process")
                    Thread(target=self.object_push,
                           args=(address, hci, adapter,)).start()
                except Exception as e:
                    print (e)
        # else:
        #     print ("   |- Bluetooth Signal Strength is NOT GOOD!")

    def object_push(self, address, hci, adapter):
        # s = BluetoothSocket(RFCOMM)
        # bdaddr = self.local_bdaddrs[hci]
        # s.bind((bdaddr, 0))

        start_time = time.time()
        channel = self.find_push_channel(address, adapter)
        print ("[ %s ] OBEX OBJECT PUSH Channel is %s"% (address, channel))
        end_time = time.time()
        # print ("      |- FindingEndTime [ %s ] - Finding OBEX_OBJPUSH service from[ %s ]" % (
        #     end_time - start_time, address))

        # if channel:
        #     client = Client(address, channel)
        #     print ("      |- OBEX_OBJPUSH Channel is %s" % channel)
        #     try:
        #         client.set_socket(s)
        #         client.connect()
        #         client.put('message.txt', 'Hello World!')
        #         client.disconnect()
        #     except IOError as e:
        #         print (e)
        # else:
        #     print ("      |- NO OBEX_OBJPUSH PROFILE!!")

    def find_push_channel(self, address, adapter=None, bus=dbus.SystemBus()):
        try:
            adapter.CreateDevice(address)
            print("Device created: %s" % address)
        except:
            print("Device all ready known: %s" % address)

        path = adapter.FindDevice(address)

        device = dbus.Interface(bus.get_object("org.bluez", path),
                                "org.bluez.Device")
        properties = device.GetProperties()

        if self.OBEX_UUID in properties['UUIDs']:
            services = device.DiscoverServices(self.OBEX_UUID)
            for key in services.keys():
                root = etree.XML(str(services[key]))
                res = self.CHANNEL_XPATH(root)
                if len(res) > 0:
                    return int(res[0], 16)
            else:
                return None
        else:
            return None

    def inquiry_complete(self):
        self.inquiry_time_end = time.time()
        self.done = True
        print ("Inquiry Completed!")
        print ("  Inquiry Time - [ %f ]" %
               (self.inquiry_time_end - self.inquiry_time_start))
        print ("  Found %d devices" % len(self.discovered_address))
        print ("  Discovered Bluetooth Address:")
        print (self.discovered_address)


logging.basicConfig(level=logging.INFO)

op = OBEX_Pusher(device_id=2)
op.find_devices(lookup_names=False, duration=8, flush_cache=True)

readfiles = [op, ]

while True:
    rfds = select.select(readfiles, [], [])[0]

    if op in rfds:
        op.process_event()

    if op.done:
        break
