#!/usr/bin/env python3

from evdev import InputDevice, list_devices, ecodes
from select import select
# https://github.com/torvalds/linux/blob/master/include/uapi/linux/input-event-codes.h

def complement(val):
    val = val if val >=0 else (~-val+1)&0xFF
    return val if 0 <= val <= 255 else 0


class Mouse:

    def __init__(self):
        self.hid = "/dev/hidg1"
        self.report = [0] * 4
        self.write()
        self.kmap = {
            ecodes.BTN_LEFT:   [ 0xFE, 0x01 ], 
            ecodes.BTN_RIGHT:  [ 0xFD, 0x02 ], 
            ecodes.BTN_MIDDLE: [ 0xFB, 0x04 ]
        }

    def write(self):
        with open(self.hid, "wb+") as fd:
            fd.write(bytearray(self.report))
    
    def press(self, code, value):
        if value == 0:
            self.report[0] &= self.kmap[code][value]
        if value == 1:
            self.report[0] |= self.kmap[code][value]
        self.write()

    def relative_x(self, val):
        self.report[1] = complement(val)
        self.write()
        self.report[1] = 0
        self.write()

    def relative_y(self, val):
        self.report[2] = complement(val)
        self.write()
        self.report[2] = 0
        self.write()

    def vertical(self, val):
        if val > 0:
            self.report[3] = 0x01
        if val < 0:
            self.report[3] = 0xFF
        self.write()
        self.report[3] = 0x00
        self.write()

class Keyboard:
    def __init__(self):
        self.hid = "/dev/hidg0"
        self.kset = set()
        self.report = [0] * 8
        self.write()
        self.kmap = [
            0x00, 0x29, 0x1e, 0x1f, 0x20, 0x21, 0x22, 0x23,
            0x24, 0x25, 0x26, 0x27, 0x2d, 0x2e, 0x2a, 0x2b,
            0x14, 0x1a, 0x08, 0x15, 0x17, 0x1c, 0x18, 0x0c,
            0x12, 0x13, 0x2f, 0x30, 0x28, 0x00, 0x04, 0x16,
            0x07, 0x09, 0x0a, 0x0b, 0x0d, 0x0e, 0x0f, 0x33,
            0x34, 0x35, 0x00, 0x31, 0x1d, 0x1b, 0x06, 0x19,
            0x05, 0x11, 0x10, 0x36, 0x37, 0x38, 0x00, 0x55,
            0x00, 0x2c, 0x39, 0x3a, 0x3b, 0x3c, 0x3d, 0x3e,
            0x3f, 0x40, 0x41, 0x42, 0x43, 0x53, 0x47, 0x5f,
            0x60, 0x61, 0x56, 0x5c, 0x5d, 0x5e, 0x57, 0x59,
            0x5a, 0x5b, 0x62, 0x63, 0x00, 0x00, 0x00, 0x44,
            0x45, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x58, 0x00, 0x54, 0x46, 0x00, 0x00, 0x4a, 0x52,
            0x4b, 0x50, 0x4f, 0x4d, 0x51, 0x4e, 0x49, 0x4c,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x48,
            0x00, 0x00, 0x00, 0x00, 0x00, 0xe3, 0x00, 0xe7
        ]
        self.mmap = {
            ecodes.KEY_LEFTCTRL:   [ 0xFE, 0x01 ], 
            ecodes.KEY_LEFTSHIFT:  [ 0xFD, 0x02 ], 
            ecodes.KEY_LEFTALT:    [ 0xFB, 0x04 ],
            ecodes.KEY_LEFTMETA:   [ 0xF7, 0x08 ], 
            # ecodes.KEY_RIGHTCTRL:  [ 0xEF, 0x10 ], 
            ecodes.KEY_RIGHTSHIFT: [ 0xDF, 0x20 ], 
            ecodes.KEY_RIGHTALT:   [ 0xBF, 0x40 ],
            ecodes.KEY_RIGHTMETA:  [ 0x7F, 0x80 ], 
        }

    def write(self):
        with open(self.hid, "wb+") as fd:
            fd.write(bytearray(self.report))

    def press(self, code, value):
        if code in self.mmap:
            if value == 0:
                self.report[0] &= self.mmap[code][value]
            if value == 1:
                self.report[0] |= self.mmap[code][value]
        else:
            if value == 0:
                self.kset.discard(self.kmap[code])
            if value == 1:
                self.kset.add(self.kmap[code])
            rsize = len(self.kset) if len(self.kset) <=6 else 6
            self.report[2:] = [0]*6
            self.report[2:2+rsize] = list(self.kset)[:rsize]
        self.write()

def get_devices_list():
    return [InputDevice(device_fn) for device_fn in reversed(list_devices())]
devices = get_devices_list()
try:
    for device in devices:
        device.grab()
except IOError:
    print("Error")
    exit(1)
mouse = Mouse()
keyboard = Keyboard()
from inotify_simple import INotify, flags
inotify = INotify()
inotify.add_watch("/dev/input", flags.CREATE | flags.ATTRIB)
##################
modmap = {
    ecodes.KEY_ESC: ecodes.KEY_GRAVE,
    ecodes.KEY_CAPSLOCK: ecodes.KEY_ESC,
}
ctrlmap = {
    ecodes.KEY_GRAVE: ecodes.KEY_ESC, 
    ecodes.KEY_1: ecodes.KEY_F1, 
    ecodes.KEY_2: ecodes.KEY_F2, 
    ecodes.KEY_3: ecodes.KEY_F3, 
    ecodes.KEY_4: ecodes.KEY_F4, 
    ecodes.KEY_5: ecodes.KEY_F5, 
    ecodes.KEY_6: ecodes.KEY_F6, 
    ecodes.KEY_7: ecodes.KEY_F7, 
    ecodes.KEY_8: ecodes.KEY_F8, 
    ecodes.KEY_9: ecodes.KEY_F9, 
    ecodes.KEY_0: ecodes.KEY_F10, 
    ecodes.KEY_MINUS: ecodes.KEY_F11,
    ecodes.KEY_EQUAL: ecodes.KEY_F12
    
}
combine_set = set()

##################
try:
    while True:
        try:
            waitables = devices[:]
            waitables.append(inotify.fd)
            r, w, x = select(waitables, [], [])

            for waitable in r:
                if isinstance(waitable, InputDevice):
                    for event in waitable.read():
                        if event.type == ecodes.EV_REL:
                            if event.code == ecodes.REL_X:
                                mouse.relative_x(event.value)
                            if event.code == ecodes.REL_Y:
                                mouse.relative_y(event.value)
                            if event.code == ecodes.REL_WHEEL_HI_RES:
                                mouse.vertical(event.value)
                        if event.type == ecodes.EV_KEY:
                            if event.code in mouse.kmap:
                                mouse.press(event.code, event.value)
                            if event.code < 128:
                                ecode = event.code
                                if event.value == 1:
                                    combine_set.add(ecode)
                                if event.value == 0:
                                    combine_set.discard(ecode)
                                if ecode in modmap:
                                    ecode = modmap[ecode]
                                if ecodes.KEY_RIGHTCTRL in combine_set:
                                    if ecode in ctrlmap:
                                        ecode = ctrlmap[ecode]
                                keyboard.press(ecode, event.value)
                else:
                    for event in inotify.read():
                        new_device = InputDevice("/dev/input/" + event.name)
                        try:
                            new_device.grab()
                        except IOError:
                            # Ignore errors on new devices
                            print("IO: " + str(new_device.name))
                            continue
                        devices.append(new_device)
                                

        except OSError:
            if isinstance(waitable, InputDevice):
                    devices.remove(waitable)
                    try:
                        waitable.ungrab()
                    except OSError as e:
                        pass
finally:
    for device in devices:
        try:
            device.ungrab()
        except OSError as e:
            pass
    inotify.close()
