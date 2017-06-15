from __future__ import division
import time
import logging
import queue
import threading
import RPi.GPIO as GPIO

def main():
        Direction_Pin = 15
        Step_Pin = 13
        Sleep_Pin = 11
        M0 = 29
        M1 = 31
        Micro = 1/16

        print("motor thread initialzied")

        #file to hold how far the motor has moved
        Motor_Status_File = "/home/pi/miura/motor_status.txt"

        #initialize the motor

        GPIO.setmode(GPIO.BOARD)

        #GPIO.setup(Sleep_Pin, GPIO.OUT)
        #GPIO.output(Sleep_Pin, True)

        GPIO.setup(Direction_Pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(Step_Pin, GPIO.OUT, initial=GPIO.LOW)

        #complete 4 cycles
        cycle = 1
        height = 11550
        while cycle!=5:
                GPIO.output(Direction_Pin, GPIO.HIGH)
                for a in range(0, height):
                        GPIO.output(Step_Pin, GPIO.HIGH)
                        GPIO.output(Step_Pin, GPIO.LOW)
                        time.sleep(.0036)
                time.sleep(1080)
                GPIO.output(Direction_Pin, GPIO.LOW)
                for b in range(0, height):
                        GPIO.output(Step_Pin, GPIO.HIGH)
                        GPIO.output(Step_Pin, GPIO.LOW)
                        time.sleep(.0036)
                time.sleep(600)
                cycle += 1
                if cycle == 3:
                        height = 16500
