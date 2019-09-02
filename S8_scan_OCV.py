#!/usr/bin/env python
# This script scans Super 8 films and uses CV to adjust the frames

import time
import datetime
import RPi.GPIO as GPIO
from picamera import PiCamera
from picamera.array import PiRGBArray
import cv2
from time import sleep
import os.path
import sys
import subprocess
import S8_cal_crop


DIR = 27   # Direction GPIO Pin
STEP = 22  # Step GPIO Pin
CW = 1     # Clockwise Rotation
CCW = 0    # Counterclockwise Rotation
MODE = (18, 15, 14)   # Microstep Resolution GPIO Pins
STEPON = 0 # pin to turn on/off the stepper
resW = 3280 #camera with 2304 , 3072
resH = 2464 #camera hight 1296,2304
BtnLeft = 13    # buttons
BtnRight = 19
BtnStart = 16
BtnStop = 26
BtnRew = 20
Photoint = 21 # photointeruptor
ledon = 12 # pin for LED
pinForward = 5 #motor pin (spool)
pinBackward = 6
step_count = 100 # steps per frame (S8)
delay = .001 # delay inbetween steps
r = 0 # button repeat counter
midy = 150 #ideal mid y coordinate of blob (S8)
tolerance = 10 #pixel tolerance
uptol = midy + tolerance
downtol = midy - tolerance
tolstep = tolerance / 2 # defines how many steps are done for correction
# this determines the image number (#of files in directory +1 for next file):
path = os.getenv('HOME') + '/scanframes' #directory of scanned files
i = len([f for f in os.listdir(path)if os.path.isfile(os.path.join(path, f))])# - number of files in directory
#camera settings:
camera = PiCamera()
camera.sensor_mode=6
camera.rotation = 180
camera.resolution = (2048,1536) #(1920,1440)#(1640,1232)#(3280,2464)
##camera.iso = 100
sleep(2)
##camera.shutter_speed = 9000
##camera.awb_mode = 'sunlight'
##camera.awb_gains = [1.4, 1.1]
##camera.zoom = (0.2, 0.3, 0.5, 0.5)
##camera.meter_mode= 'matrix'
##camera.exposure_mode = 'auto'
stepMinus = 0 # counter for stepper corrections
stepPlus = 0
#cropping coordinates: (S8)
y=90
x=15
h=300
w=35
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

p = GPIO.PWM(5, 40) # set PWM channel, hz



def motorStart(): #for spoolmotor
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
##        p.start(100)
        GPIO.output(pinForward, GPIO.HIGH)
        GPIO.output(pinBackward, GPIO.LOW)
    else:
##        p.ChangeDutyCycle(0)
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

def takePicture():
    global image, oimage, cY , M, area
    rawCapture = PiRGBArray(camera)
    camera.capture(rawCapture, format="bgr")
    image = rawCapture.array
    oimage = image
    image = cv2.resize(image, (640, 480))
    image = image[y:y+h, x:x+w]
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret,thresh = cv2.threshold(gray_image,127,255,0)
    contours,hierarchy = cv2.findContours(thresh, 1, 2)

    for l in range(10): #if more contours are found, take the one that's area is >2000
        cnt = contours[l]
        area = cv2.contourArea(cnt)
        if area > 1000:
            break
    M = cv2.moments(cnt)
    
    try:
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
    except ZeroDivisionError:
        cX = 15
        cY = 100


GPIO.output(MODE, RESOLUTION['1/8']) # set stepmode (full - 1/32)
GPIO.output(ledon, GPIO.HIGH) #turn on LED
GPIO.output(STEPON, GPIO.HIGH)
sleep(2)
camera.start_preview()
sleep(1)
takePicture()

try:

    while True:

        motorStop()
        spool()

        if GPIO.input(BtnRight) == GPIO.LOW: #step to adjust frame
            stepCW(tolstep)
            takePicture()


        if GPIO.input(BtnLeft) == GPIO.LOW: #step to adjust frame
            stepCCW(tolstep)
            takePicture()

        if GPIO.input(BtnRew) == GPIO.LOW: #rewind
            
            if r == 0:
                r+=1
            else:
                r-=1
            

        if GPIO.input(BtnStart) == GPIO.LOW: #start recording

            while GPIO.input(BtnStop):
                motorStart()
                takePicture()
##                if stepMinus >5:
##                    print '>5'
##                    stop()
##                    break
##                if stepPlus >5:
##                    print '>5'
##                    stop()
##                    break
                if area >8000: #end of film
                    stop()
                    calcrop = S8_cal_crop.calCrop() #run script cal_crop
##                    break

                if cY > uptol:
                    stepCW(tolstep)
                    stepMinus += 1


                if cY < downtol:
                    stepCCW(tolstep)
                    stepPlus += 1


                if cY <= uptol and cY >= downtol:
                    camera.capture('/home/pi/scanframes/scan'+ ' - '+ format(i,'06') +'.jpg',use_video_port = True)
                    mt = subprocess.Popen(['/opt/vc/bin/vcgencmd', 'measure_temp'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                    (res,err) = mt.communicate()
                    logTXT = (str(i) +";"+ str(time.strftime("%H"+":"+"%M"+":"+"%S"))+";"+str(stepMinus)+";"+str(stepPlus)+";"+str(cY)+";"+str(area)+";"+str(res))
                    with open("logfile.txt", "a") as logfile:
                        logfile.write(logTXT)
                    stepCW(step_count)
                    stepMinus = 0
                    stepPlus = 0
                    i += 1


        if GPIO.input(BtnStop) == GPIO.LOW:
            print 'push1'
            sleep(5)
            if GPIO.input(BtnStop) == GPIO.LOW:
                print 'push2'
                stop()
                calcrop = S8_cal_crop.calCrop() #run script cal_crop


except KeyboardInterrupt:
    stop()
    sys.exit(0)




