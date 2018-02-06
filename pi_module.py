### >>>>>>>> VERSION 1 <<<<<<<<< ###
import glob
import os
import tensorflow as tf
import numpy as np
import sys
import time
from collections import Counter
import RPi.GPIO as GPIO # PI 3
import spidev # IR sensor
import picamera # pi camera
import xmlrpc.client
import picamclient # picam streaming client
import threading
import time
from threading import Thread
from time import sleep
from multiprocessing.pool import ThreadPool

client = xmlrpc.client.ServerProxy('http://192.168.43.12:9009')
OBSTACLE_DETECTOR=None

OBSTACLE_THRESHOLD_IR=40 			#cm
OBSTACLE_THRESHOLD_US=30 			#cm
GPIO.setmode(GPIO.BOARD) 			#pi GPIO
spi = spidev.SpiDev() 				#IR adc 
spi.open(0,0)						#IR adc

# load US sensor
def obj_detected_US():
	TRIG = 12
	ECHO = 16
	#GPIO.setmode(GPIO.BOARD)
	GPIO.setup(TRIG,GPIO.OUT)
	GPIO.setup(ECHO,GPIO.IN)

	GPIO.output(TRIG, False)
	#print("Waiting For Sensor To Settle", timer)
	time.sleep(0.025)

	GPIO.output(TRIG, True)
	time.sleep(0.00001)
	GPIO.output(TRIG, False)

	while GPIO.input(ECHO)==0:
	  pulse_start = time.time()

	while GPIO.input(ECHO)==1:
	  pulse_end = time.time()

	pulse_duration = pulse_end - pulse_start

	distance = pulse_duration * 17150

	distance = round(distance, 2)
	#print("distance US ",distance)
	if(distance<OBSTACLE_THRESHOLD_US):
		print("\nObject detected by UltraSonic sensor at %s cm" % str(distance))
		global OBSTACLE_DETECTOR
		OBSTACLE_DETECTOR="US"
		return True
	else:
		return False

# load IR sensor
def read_IR_adc_mcp3008(adcnum):
    if ((adcnum > 7) or (adcnum < 0)):
        return -1
    r = spi.xfer2([1,(8+adcnum)<<4,0])
    adcout = ((r[1]&3) << 8) + r[2]
    return adcout

def obj_detected_IR():
	time.sleep(0.1)
	val = read_IR_adc_mcp3008(0)
	r = []
	for i in range (0,10):
	    r.append(read_IR_adc_mcp3008(1))
	a = sum(r)/10.0
	v = (a/1023.0)*3.3
	d = 16.2537 * v**4 - 129.893 * v**3 + 382.268 * v**2 - 512.611 * v + 306.439
	cm = int(round(d))
	if(cm<OBSTACLE_THRESHOLD_IR):
		print("\nObject detected by IR sensor at %s cm" % cm)
		global OBSTACLE_DETECTOR
		OBSTACLE_DETECTOR="IR"
		return True
	else:
		return False

#obstacle checker
def is_obstacle_there(sensor):
	#print("inside obs det",sensor)
	sensor="US"
	if(sensor=="US"):
		if(obj_detected_US()):
			return True
		else:
			return False
	elif(sensor=="IR"):
		#print("inside IR")
		if(obj_detected_IR()):
			return True
		else:
			return False


# keep US, IR sensor on scanning mode
try:
	print("Initialising module.....")#print("AI engine LOADING.............")
	client.load_ai_engine()#PORT 9009 RPC hit 
	print("Module initialised")
	pool = ThreadPool(processes=1)
	while True:
	# if US, IR detect object >>
		if(obj_detected_IR() or obj_detected_US()):#
		# 1. FIRE camera
			total_strt_time = time.time()
			async_result = pool.apply_async(client.load_ai_server)
			print("Picam streaming ON")
			t2 = Thread(target = picamclient.stream_to_ai_server)
			t2.start()
			t2.join()
			return_val = async_result.get()
			total_end_time = time.time()
			print("%s identified in %.2f seconds" % (str(return_val), (total_end_time - total_strt_time)))
			while(is_obstacle_there(sensor=OBSTACLE_DETECTOR)):#ensure items being loaded gets weighed
				print("bird is still sitting...")
				#dont accept negative values
			#try
			#query
			
except (Exception,KeyboardInterrupt, SystemExit) as e:
	GPIO.cleanup()
	print("\nModule shutdown successfuly!\n ERROR: ", str(e))
	sys.exit()
