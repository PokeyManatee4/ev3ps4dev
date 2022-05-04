#!/usr/bin/env python3

import evdev
import ev3dev.auto as ev3
import threading
import time

## Some helpers ##
def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

def scale(val, src, dst):
    return (float(val - src[0]) / (src[1] - src[0])) * (dst[1] - dst[0]) + dst[0]

def scale_stick(value):
    return scale(value,(0,255),(-1000,1000))

def dc_clamp(value):
    return clamp(value,-1000,1000)

## Initializing ##
print("Finding ps4 controller...")
devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
ps4dev = devices[0].fn

gamepad = evdev.InputDevice(ps4dev)

forward_speed = 0
side_speed = 0
running = True

class MotorThread(threading.Thread):
    def __init__(self):
        self.left_motor = ev3.LargeMotor(ev3.OUTPUT_A)
        self.right_motor = ev3.LargeMotor(ev3.OUTPUT_D)
        threading.Thread.__init__(self)

    def run(self):
        print("Engine running!")
        while running:
            self.left_motor.run_forever(speed_sp=dc_clamp(-forward_speed+side_speed))
            self.right_motor.run_forever(speed_sp=dc_clamp(forward_speed+side_speed))
        self.left_motor.stop()
        self.right_motor.stop()

motor_thread = MotorThread()
motor_thread.setDaemon(True)
motor_thread.start()


# steer set up
steer_speed = 0

class DirectionThread(threading.Thread):
    def __init__(self):
        self.motor = ev3.MediumMotor(ev3.OUTPUT_B)
        threading.Thread.__init__(self)

    def run(self):
        print("Steer Ready...")
        while running:
            self.motor.run_direct(duty_cycle_sp=steer_speed)

steer_thread = DirectionThread()
steer_thread.setDaemon(True)
steer_thread.start()


# event listner
for event in gamepad.read_loop():   #this loops infinitely
    if event.type == 3:             #A stick is moved
        if event.code == 0:         #X axis on left stick
            forward_speed = -scale_stick(event.value)
        if event.code == 1:         #Y axis on left stick
            side_speed = -scale_stick(event.value)
        if side_speed < 100 and side_speed > -100:
            side_speed = 0
        if forward_speed < 100 and forward_speed > -100:
            forward_speed = 0

    if event.type == 1 and event.code == 308 and event.value == 1:
        steer_speed = 75

    if event.type == 1 and event.code == 309 and event.value == 1:
        steer_speed = -75


    if event.type == 1 and event.code == 305 and event.value == 1:
        print("X button is pressed. Stopping.")
        running = False
        time.sleep(0.5) # Wait for the motor thread to finish
        break

for event in gamepad.read_loop():   #this loops infinitely
    if event.type == 3:             #A stick is moved
        if event.code == 5:         #Y axis on right stick
            wheel_speed = scale_stick(event.value)
        if event.code == 0:
            steer_speed = scale_stick(event.value)/3.0

    if event.type == 1 and event.code == 302 and event.value == 1:
        print("X button is pressed. Stopping.")
        running = False
        break
