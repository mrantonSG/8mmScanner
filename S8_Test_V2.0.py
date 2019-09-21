#!/usr/bin/env python
# This script helps to test the basic funtions of the 8mm film scanner

import time
import datetime
import RPi.GPIO as GPIO
from picamera import PiCamera
from time import sleep


DIR = 27   # Direction GPIO Pin
STEP = 22  # Step GPIO Pin
CW = 1     # Clockwise Rotation
CCW = 0    # Counterclockwise Rotation
MODE = (18, 15, 14)   # Microstep Resolution GPIO Pins
STEPON = 0 # pin to turn on/off the stepper
BtnLeft = 13    # buttons
BtnRight = 19
BtnStart = 16
BtnStop = 26
BtnRew = 20
Photoint = 21 # photointeruptor
ledon = 12 # pin for LED
pinForward = 6 #motor pin (spool)
pinBackward = 5
step_count = 100 # steps per frame (S8)
delay = .001 # delay inbetween steps
r = 0 # button repeat counter

#camera settings:
camera = PiCamera()
camera.sensor_mode=6
camera.rotation = 180
camera.resolution = (2048,1536)
##camera.awb_mode = 'off'
##camera.awb_gains = [1.8, 1.1]

#stepper mode:
RESOLUTION = {'Full': (0, 0, 0),
              'Half': (1, 0, 0),
              '1/4': (0, 1, 0),
              '1/8': (1, 1, 0),
              '1/16': (0, 0, 1),
              '1/32': (1, 0, 1)}


GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)
GPIO.setup(STEPON, GPIO.OUT)
GPIO.setup(ledon, GPIO.OUT)
GPIO.setup(pinForward, GPIO.OUT)
GPIO.setup(pinBackward, GPIO.OUT)
GPIO.setup(BtnRight, GPIO.IN, pull_up_down=GPIO.PUD_UP)    
GPIO.setup(BtnLeft, GPIO.IN, pull_up_down=GPIO.PUD_UP)    
GPIO.setup(BtnStart, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BtnStop, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BtnRew, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(Photoint, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
GPIO.setup(MODE, GPIO.OUT)

p = GPIO.PWM(6, 40) # set PWM channel, hz

def motorStart():
    if GPIO.input(Photoint):
        p.start(10)
        GPIO.output(pinBackward, GPIO.LOW)

    else:
        p.ChangeDutyCycle(0)
        GPIO.output(pinBackward, GPIO.LOW)

def motorStop():
    p.ChangeDutyCycle(0)
    GPIO.output(pinBackward, GPIO.LOW)

def spool():
    if r == 1:
        GPIO.output(pinForward, GPIO.HIGH)
        GPIO.output(pinBackward, GPIO.LOW)

    else:
        GPIO.output(pinForward, GPIO.LOW)
        GPIO.output(pinBackward, GPIO.LOW)


def stepCW(steps):
    for x in range(steps):
        GPIO.output(DIR, CW)
        GPIO.output(STEP, GPIO.HIGH)
        sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        sleep(delay)

def stepCCW(steps):
    for x in range(steps):
        GPIO.output(DIR, CCW)
        GPIO.output(STEP, GPIO.HIGH)
        sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        sleep(delay)

def stop():
    motorStop()
    GPIO.output(ledon, GPIO.LOW)
    GPIO.output(STEPON, GPIO.LOW)
    camera.stop_preview()
    GPIO.cleanup()


GPIO.output(MODE, RESOLUTION['1/8']) # set stepmode (full - 1/32)
GPIO.output(ledon, GPIO.HIGH) #turn on LED
GPIO.output(STEPON, GPIO.HIGH)
sleep(2)
camera.start_preview()
sleep(1)


try:

    while True:
        spool()
        motorStart()

        if GPIO.input(BtnRight) == GPIO.LOW: 
            stepCW(20)

        if GPIO.input(BtnLeft) == GPIO.LOW: 
            stepCCW(20)

        if GPIO.input(BtnRew) == GPIO.LOW: #rewind
            
            if r == 0:
                r+=1
            else:
                r-=1
            

        if GPIO.input(BtnStart) == GPIO.LOW: #take picture
            
            camera.capture('/home/pi/Desktop/test.jpg',use_video_port = True)


        if GPIO.input(BtnStop) == GPIO.LOW:
            stop()
            exit()

except KeyboardInterrupt:
    stop()
    exit(0)




