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

# taken from stack overflow's Mark Ransom http://stackoverflow.com/questions/24682260/how-to-convert-4-byte-ieee-little-endian-float-binary-representation-to-float#24682634
def magnitude(x):
    return 0 if x==0 else int(math.floor(math.log10(abs(x)))) + 1

def round_total_digits(x, digits=7):
    return round(x, digits - magnitude(x))

'''
>>> round_total_digits(struct.unpack('<f', '\x94\x53\xF0\x40')[0])
7.510202
>>> round_total_digits(struct.unpack('<f', '\x0C\x02\x0F\x41')[0])
8.938
>>> x = struct.unpack('<f', struct.pack('<f', 12345.67))[0]
>>> x
12345.669921875
>>> round_total_digits(x)
12345.67
'''