import smbus 
import time

bus = smbus.SMBus(1) #initialization 
address = 0x40 #sensor specific

## List of commands:
# 0xE5: Measure RH, Hold Master Mode
# 0xF5 Measure RH, No Hold Master Mode (DEFAULT)
# 0xE3: Measure Temp, Hold Master Mode
# 0xF3: Measure Temp, No Hold Master Mode (DEFAULT)
# 0xE0: Read Temperature Value from Previous RH Measurement
# 0xFE: Reset  

#reads raw data
def raw():
	raw = bus.read_word_data(address,command)
	return raw

#convert raw to relative humidity
def rh(raw):
	rh = 125 * raw / 65536 - 6
	return rh

#convert raw to temperature (celsius)
def temp(raw):
	temp = 175.72 * raw / 65536 - 46.85
	return temp  
	
#continuously read and print sensor data
while True:
	setting = input("Enter 'RH' for relative humidity OR 'T' for temperature OR 'Q' to exit: ")
	if setting == 'RH':
		command = 0xF5
		master = input("Enter any key for DEFAULT (no hold master). Else enter 'HM': ")
		if master == 'HM':
			command = 0xE5
			while True:
				time.sleep(0.5) 
				a = raw()
				b = rh(a)
				print(a,hex(int(a)),b,hex(int(b)))
		else:
			while True:
				time.sleep(0.5)
				a = raw()
				b = rh(a) 
				print(a,hex(int(a)),b,hex(int(b)))
	elif setting == 'T':
		command = 0xF3
		master = input("Enter any key for DEFAULT (no hold master). Else enter 'HM': ")
		if master == 'HM':
			command = 0xE3
			while True:
				time.sleep(1)
				a = raw()
				b = temp(a)
				print(a,hex(int(a)),b,hex(int(b)))
		else:
			while True:
				time.sleep(1)
				a = raw()
				b = temp(a)
				print(a,hex(int(a)),b,hex(int(b)))
	else: 
		print("quitting")
		break
	
#git stage -a 
