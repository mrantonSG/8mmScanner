#!/usr/bin/env python

import os
import random
import time
import numpy as np
import cv2
from time import sleep
import fnmatch
import RPi.GPIO as GPIO
import sys
import glob
import subprocess

class calCrop(object):

    def __init__(self):
        
        ycal = 50 # calibrate camera frame y position 0=center of blob
        xcal = 0
        ysize = 494 #770 #y size /2 530
        xsize = 1310  #2054 1410
        xstart = 290 #465 #x startpoint

        r = 0
        pinForward = 6 #motor pin (spool)
        pinBackward = 5

        xy = 1

        BtnLeft = 13    # buttons
        BtnRight = 19
        BtnStart = 16
        BtnStop = 26
        BtnRew = 20
                    
        scanDir = '/home/pi/scanframes/'
        cropPath = '/home/pi/cropframes/'

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BtnRight, GPIO.IN, pull_up_down=GPIO.PUD_UP)    
        GPIO.setup(BtnLeft, GPIO.IN, pull_up_down=GPIO.PUD_UP)    
        GPIO.setup(BtnStart, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(BtnStop, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(BtnRew, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(pinForward, GPIO.OUT)
        GPIO.setup(pinBackward, GPIO.OUT)

        def spool():
            if r == 1:
                GPIO.output(pinForward, GPIO.HIGH)
                GPIO.output(pinBackward, GPIO.LOW)
            else:
                GPIO.output(pinForward, GPIO.LOW)
                GPIO.output(pinBackward, GPIO.LOW)

        def endocv():
            for k in range (8):
                cv2.destroyAllWindows()
                cv2.waitKey(1)

        def calPic():

            img = cv2.imread(scanDir + randompic)
            print (randompic)
            image = cv2.resize(img, (640, 480)) 

            y=0 #15
            x=10
            h=480 #300
            w=30
            image = image[y:y+h, x:x+w]

            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            ret,thresh = cv2.threshold(gray_image,127,255,0)
            _,contours,hierarchy = cv2.findContours(thresh, 1, 2)

            for l in range(10):
                cnt = contours[l]
                area = cv2.contourArea(cnt)

                if area > 2000:
                    break
            M = cv2.moments(cnt)
            try:
                cY = int(M["m01"] / M["m00"])
            except ZeroDivisionError:
                cY = 100
                
            LMP = int(cY * 3.2)+ycal #x size of scanned image 2084 / 640
            cv2.rectangle(img,(xstart+xcal,LMP-ysize),(xstart+xsize+xcal,LMP+ysize),(0,255,0),50)
            cv2.imshow('Cal-Crop', img)
            cv2.waitKey(50)



        def cropPic():

            img = cv2.imread(n)
            image = cv2.resize(img, (640, 480)) 

            y=0 #15
            x=10
            h=480 #300
            w=30
            image = image[y:y+h, x:x+w]

            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            ret,thresh = cv2.threshold(gray_image,127,255,0)
            _,contours,hierarchy = cv2.findContours(thresh, 1, 2)

            for l in range(10):
                cnt = contours[l]
                area = cv2.contourArea(cnt)
                if area > 2000:
                    break
            M = cv2.moments(cnt)
            try:
                cY = int(M["m01"] / M["m00"])
            except ZeroDivisionError:
                cY = 100
            LMP = int(cY * 3.2)+ycal
            img = img[LMP-ysize:LMP+ysize, xstart+xcal:xstart+xsize+xcal]

            cv2.imwrite(os.path.join(cropPath , n), img)
            cv2.waitKey(25)
            cv2.imshow('Cal-Crop', img)
            cv2.waitKey(50)
            

            

        cv2.namedWindow('Cal-Crop', cv2.WINDOW_NORMAL);
        cv2.resizeWindow('Cal-Crop', 640,480)
        randompic = random.choice(os.listdir('/home/pi/scanframes/'))
        calPic()

        while True:
            spool()
            if GPIO.input(BtnStart) == GPIO.LOW:     
                randompic = random.choice(os.listdir('/home/pi/scanframes/'))
                calPic()
                sleep(2)
                if GPIO.input(BtnStart) == GPIO.LOW and GPIO.input(BtnRight) == GPIO.LOW:
                    os.chdir(scanDir)
                    for n in sorted(glob.glob('*.jpg')):
                        cropPic()
                        print (n)
                        if GPIO.input(BtnStop) == GPIO.LOW:
                            break
                    cv2.waitKey(1)
                    endocv()
##                    for k in range (8):
##                        cv2.destroyAllWindows()
##                        cv2.waitKey(1)
                    os.chdir('/home/pi/cropframes/')
                    subprocess.check_output('ffmpeg -r 18 -f image2 -s 1920x1080  -pattern_type glob -i "*.jpg" -vcodec libx264 -preset ultrafast -crf 10  -vf format=yuv420p film.mp4', shell=True)

                    print ("done")
                    sys.exit(0)
                

            if GPIO.input(BtnLeft) == GPIO.LOW:
                if xy == 1:
                    ycal += 10
                    calPic()
                else:
                    xcal += 10
                    calPic()

            if GPIO.input(BtnRight) == GPIO.LOW:
                if xy == 1:
                    ycal -= 10
                    calPic()
                else:
                    xcal -= 10
                    calPic()

            if GPIO.input(BtnStop) == GPIO.LOW:
                if xy == 1:
                    xy += 1
                    sleep(1)
                else:
                    xy -= 1
                    sleep(1)
                if GPIO.input(BtnStop) == GPIO.LOW:
                    print ("push2")
                    endocv()
                    sys.exit(0)

            if GPIO.input(BtnRew) == GPIO.LOW:
                if r == 0:
                    r+=1
                else:
                    r-=1

            
                

                    


                

                
        ##GPIO.cleanup()
        ##    cv2.waitKey(0)
        ##    cv2.destroyAllWindows()
