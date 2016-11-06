# utility functions

diameterOfWheel = 65.087 # mm
radiusOfWheel = 32.5435 # mm
circumferenceOfWheel = 204.476841044199 # mm  diameterofWheel*pi
stateChangesPerRevolution = 40.0 # there are 20 slots, but 40 state changes
cirDivChanges = circumferenceOfWheel/stateChangesPerRevolution
distPerBlip = 5.11192102610497 # mm  circumfrenceOfWheel/stateChangesPerRevolution
maxVel = 511.92102620497 # mm/s  distPerBlip/getAverageBlip() when pwm = 100
minVel = .1 # mm/s just a guess //TODO make not a guess
botWidth = 139.7 #mm distance from middle of tire to the other wheel's middle of its tire
 
# this is different for both RPi and Edison
# TODO, needs to be in encoder file or config.txt
leftEncPin = 11
rightEncPin = 12

microcontroller = None

# used to change pin or pwm values, or to request a input or analog read
controllerQueue = None
gpioQueue = None
encQueue = None
gcsDataQueue = None

# returns a unique identifier for a process
def getIdentifier(process):
	return str(process).split('(')[1].split(',')[0]

def clampToRange(x, lower, upper):
		if x < lower:
			return lower
		elif x > upper:
			return upper
		else:
			return x

# maps x which is in the range of in_min to in_max to x's corresponding
# value between out_min and out_max
def transform(x, in_min, in_max, out_min, out_max):
	in_max = float(in_max)
	return (x - in_min) * (out_max - out_min)/(in_max - in_min) + out_min

