# utility functions

diameterOfWheel = 65.087 # mm
circumferenceOfWheel = 204.476841044199 # mm  diameterofWheel*pi
stateChangesPerRevolution = 40 # there are 20 slots, but 40 state changes
distPerBlip = 5.11192102610497 # mm  circumfrenceOfWheel/stateChangesPerRevolution
maxVel = .51192102620497 # m/s  distPerBlip/getAverageBlip() when pwm = 100
minVel = .01 # m/s just a guess //TODO make not a guess
botWidth = 139.7 #mm distance from middle of tire to the other wheel's middle of its tire

# this is different for both RPi and Edison
# TODO, needs to be in encoder file or config.txt
leftEncPin = 11
rightEncPin = 12

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
	return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
