'''
    ____  ____  ____      ____________________   __  _________  ______  ___ 
   / __ \/ __ \/ __ \    / / ____/ ____/_  __/  /  |/  /  _/ / / / __ \/   |
  / /_/ / /_/ / / / /_  / / __/ / /     / /    / /|_/ // // / / / /_/ / /| |
 / ____/ _, _/ /_/ / /_/ / /___/ /___  / /    / /  / // // /_/ / _, _/ ___ |
/_/   /_/ |_|\____/\____/_____/\____/ /_/    /_/  /_/___/\____/_/ |_/_/  |_|
    __  _____   _____ ____     ___   ____ ________ 
   / / / /   | / ___// __ \   |__ \ / __ <  /__  /
  / /_/ / /| | \__ \/ /_/ /   __/ // / / / /  / /
 / __  / ___ |___/ / ____/   / __// /_/ / /  / /
/_/ /_/_/  |_/____/_/       /____/\____/_/  /_/
'''

import sched
import os
import time
import smbus
import RPi.GPIO as GPIO
import math
import re
from w1thermsensor import W1ThermSensor

#LED Setup
led_pin = 35
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(led_pin,GPIO.OUT)
GPIO.setup(led_pin,False)
led_on = False

camera_wall_1 = "00000865ce6c"
camera_wall_2 = "00000828fbdd"
camera_wall_3 = "00000865e2e7"
camera_wall_4 = "000007a8af78"
temp_motor = "0000086460f1"
buck_converter = "000007a891a3"
ambient_internal = "000007a8a632"
ambient_external = "000007a8acab"
motor_driver = "000007a89303"

GAIN = 1
bus = smbus.SMBus(1)

# Extra Setup
bus.write_byte_data(0x60, 0x26, 0x39) #pres

#place holders. replace with actual values later
temp_max = [70.,70.,70.,70.,80.,105.,125.,125.,150.]
temp_min = [-20.,-20.,-20.,-20.,-20.,-20.,-25.,-25.,-40.]

# Handles sensor reading schedule
class PeriodicScheduler:
	def __init__(self):
		self.scheduler = sched.scheduler(time.time, time.sleep)

	def setup(self, interval, action, actionargs=()):
		self.scheduler.enter(interval, 1, self.setup, (interval, action, actionargs))
		action(*actionargs)

	def run(self):
		self.scheduler.run()


# Converts data array into string
def cs_str(data):
	out = "" # Initialize variable with empty string
	for i in range(len(data)): # Iterate through each "word" in data
		if i % 2 == 0:
			out += "{:.0f}: ".format(data[i]) # Add each word to the string "out"
		else:
			out += "{0:.2f} ".format(data[i])
	return out # Return newly formed string


# Check to see if temp sensors are within normal operating temperatures
def check_temp(data):
	for i in range(len(data)):
		if i % 2 == 0:
			label = data[i] - 1
		else:
			value = data[i]
			if value > temp_max[label] or value < temp_min[label]:
				return True
	return False


# Determine temperature sensor identity
def temp_find(address):
	if address == camera_wall_1:
		return 1
	elif address == camera_wall_2:
		return 2
	elif address == camera_wall_3:
		return 3
	elif address == camera_wall_4:
		return 4
	elif address == temp_motor:
		return 5
	elif address == buck_converter:
		return 6
	elif address == ambient_internal:
		return 7
	elif address == ambient_external:
		return 8
	elif address == motor_driver:
		return 9

# Read temperature and downlink
def read_temp(downlink, temp_led):
	try:
		data = []
		for sensor in W1ThermSensor.get_available_sensors(): # Grab temp values from all available sensors in a round robin fashion
			data.append(temp_find(sensor.id))
			data.append(sensor.get_temperature())
		if check_temp(data):
			if not temp_led.is_set():
				GPIO.output(led_pin,True)
				temp_led.set()
		else:
			if temp_led.is_set():
				GPIO.output(led_pin,False)
				temp_led.clear()
		downlink.put(["SE", "T%i" % (len(data)/2), cs_str(data)]) # Send the packaged data packet to the downlink thread.
	except:
		pass


# Grab raw data from bus. Convert raw data to nice data.
def read_humi(downlink):
	try:
		bus.write_byte(0x40, 0xF5)
		time.sleep(0.3)
		data0 = bus.read_byte(0x40)
		data1 = bus.read_byte(0x40)
		humidity = ((data0 * 256 + data1) * 125 / 65536.0) - 6
		time.sleep(0.3)
		downlink.put(["SE", "HU", "{0:.2f}".format(humidity)])
	except:
		pass


# Grab raw data from bus. Convert raw data to nice data.
def read_pres(downlink):#downlink
	try:
		data = bus.read_i2c_block_data(0x60, 0x00, 4)
		pres = ((data[1] * 65536) + (data[2] * 256) + (data[3] & 0xF0)) / 16 # Use with humidity sensor?
		pressure = (pres / 4.0) / 1000.0
		downlink.put(["SE", "PR", "{0:.2f}".format(pressure)])
	except:
		pass


# Check Pi temperature, CPU usage, and disk usage
def read_hrbt(downlink):
	try:
		temp_read = os.popen("vcgencmd measure_temp").readline().replace('temp=','').replace("'C",'')
		cpu = os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip() + '%'
		disk_read = os.popen("df -h /")
		disk_read.readline()
		disk_usage = disk_read.readline() 
		disk_usage = re.findall(r'\d{1,3}%',disk_usage)[0]
		downlink.put(["SE", "HB", '{} {} {}'.format(temp_read, cpu, disk_usage).replace('\n','')])
		return
	except:
		pass
