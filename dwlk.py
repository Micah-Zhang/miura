import threading
import serial
import time
import queue

q = queue.Queue()

ser = serial.Serial(
	port = '/dev/ttyUSB0',
	baudrate = 4800,
	parity = serial.PARITY_NONE,
	stopbits = serial.STOPBITS_ONE,
	bytesize = serial.EIGHTBITS,
	timeout = 1
)

ser.close()
ser.open()

def main():
	print("downlink thread initialized")
	while True:
		a = q.get()		
		b = ser.write(bytes(a, encoding="UTF-8"))
		print("packet sent")
