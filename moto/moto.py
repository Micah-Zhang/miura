import time
import moto.cmoto as cmoto
import moto.fmoto as fmoto
import RPi.GPIO as GPIO
import threading

#gpio setup
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

#motor setup
GPIO.setup(cmoto.Direction_Pin, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(cmoto.Step_Pin, GPIO.OUT, initial=GPIO.LOW)

#button setup
GPIO.setup(cmoto.Upper_Button,GPIO.IN)
GPIO.setup(cmoto.Lower_Button,GPIO.IN)

# Encoder initialization
pin_A = 18
pin_B = 16
GPIO.setup(pin_A, GPIO.IN)
GPIO.setup(pin_B, GPIO.IN)
encoder = fmoto.Encoder(pin_A, pin_B)

# To access encoder count, use encoder.get_encoder_count()

encoder_thread = threading.Thread(target=fmoto.encoder_function, args=(encoder,))
encoder_thread.start()

def main(downlink, moto_cmd, safe_mode, cam_is_moving, cam_is_open, cam_reset):
	downlink.put(["MO","BU","MOTO"]) #verify succesful thread start
	cmoto.mission_start_time = time.time() #keep track of mission start time
	cam_reset.set()
	while(True):
		fmoto.checkUplink(moto_cmd, downlink, safe_mode, cam_is_moving, cam_is_open, cam_reset)
		if cmoto.top_calib:
			cam_is_open.clear()
			cam_reset.set()
			cam_is_moving.set()
			fmoto.move(16000, downlink, safe_mode, encoder)
			cam_is_moving.clear()
			cam_reset.set()
			cam_is_open.set()
			cmoto.top_calib = False
			print("top calibrated")
		if cmoto.bot_calib:
			cam_is_open.clear()
			cam_reset.set()
			cam_is_moving.set()
			fmoto.move(-16000, downlink, safe_mode, encoder)
			cam_is_moving.clear()
			cam_reset.set()
			cmoto.bot_calib = False
			print("bottom calibrated")
		if cmoto.nudge_state:
			cam_is_open.clear()
			cam_reset.set()
			cam_is_moving.set()
			fmoto.move(cmoto.nudge_step, downlink, safe_mode, encoder)
			cam_is_moving.clear()
			cam_reset.set()
			cmoto.nudge_state = False
		if cmoto.minimum_success or cmoto.full_extension:
			if not cmoto.cycle_extended:
				cam_is_open.clear()
				cam_reset.set()
				cam_is_moving.set()
				cmoto.cycle_start_time = time.time()
				if cmoto.minimum_success:
					fmoto.move(int(73*(cmoto.max_step/100) - cmoto.step_count), downlink, safe_mode, encoder)
				else:
					fmoto.move(cmoto.max_step - cmoto.step_count + 750, downlink, safe_mode, encoder)
				cmoto.motor_start_time = time.time()
				cam_is_moving.clear()
				cam_reset.set()
				cam_is_open.set()
				cmoto.cycle_extended = True
			elif not cmoto.cycle_contracted and (time.time() > cmoto.motor_start_time + cmoto.top_wait_time):
				cam_is_open.clear()
				cam_reset.set()
				cam_is_moving.set()
				fmoto.move(- cmoto.step_count - 750, downlink, safe_mode, encoder)
				cmoto.motor_end_time = time.time()
				cam_is_moving.clear()
				cam_reset.set()
				cmoto.cycle_contracted = True
			elif cmoto.cycle_extended and cmoto.cycle_contracted and (time.time() > cmoto.motor_end_time + cmoto.bot_wait_time):
				cmoto.cycle_extended = False
				cmoto.cycle_contracted = False
				cmoto.minimum_success = False
				cmoto.cycle_end_time = time.time()
		if not cmoto.auto_set and (time.time() > cmoto.mission_start_time + cmoto.auto_wait): #begin automation after set amount of time
			cmoto.auto_set = True
			cmoto.automation = True
		if cmoto.automation:
			if cmoto.cycle_count == -2:
				cmoto.cycle_count += 1
				downlink.put(["MO","CC",str(cmoto.cycle_count)])
				moto_cmd.put(b"\x01")
			elif cmoto.cycle_count == -1:
				cmoto.cycle_count += 1
				downlink.put(["MO","CC",str(cmoto.cycle_count)])
				moto_cmd.put(b"\x02")
			elif cmoto.cycle_count == 0:
				cmoto.cycle_count += 1
				downlink.put(["MO","CC",str(cmoto.cycle_count)])
				moto_cmd.put(b"\x01")
			elif cmoto.cycle_count > 0:
				if not cmoto.cmd_sent:
					moto_cmd.put(b"\x04")
					cmoto.cmd_sent = True
				elif not cmoto.full_extension:
					cmoto.cmd_sent = False
					cmoto.cycle_count += 1
					downlink.put(["MO","CC",str(cmoto.cycle_count)])
		downlink.put(["MO","SC",str(cmoto.step_count)])
		downlink.put(["MO","SP",'{:.2f}%'.format(cmoto.step_count/cmoto.max_step * 100)])
		lower = GPIO.input(cmoto.Lower_Button)
		upper = GPIO.input(cmoto.Upper_Button)
		downlink.put(["MO","BT",str(lower) + ' ' + str(upper)])
		downlink.put(["MO","EC",str(encoder.get_encoder_count())])
		time.sleep(1)
