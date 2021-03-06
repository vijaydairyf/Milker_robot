# Explore the arena to find the desired misterious liquid (milk)
# The coordenates of the arena will be taken this way:
# This approach starts after picking up the terrine
'''
	NOMENCLATURE:
	1. Empty Terrines zone
	2. Drop Terrines zone

			 EAST
	 	 _____________
   		|			  | 
NORTH 	|			  |	SOUTH
   		|			  |
   		-2----	-----1-
   			 ***

   			 WEST
'''
##-----------LIBRARIES-----------##
import cv2
import time
import math
import numpy as np
import LARC1 as rb
import random
import serial
import statistics
import gtk
import subprocess
from copy import deepcopy
##-------------------------------##

##-----------GLOBAL VARIABLES-----------##
binValue = 70
headingWall = "E"	# GLOBAL DIRECTION VARIABLE
mainFrame = []	# Initialize global variable for image
UVCDYNCTRLEXEC = "/usr/bin/uvcdynctrl"
lastTurn = "left"
firstWalk = "225"
##--------------------------------------##

##-----------SETUP-----------##
cap = cv2.VideoCapture(0)
# Check that the connection with the camera is open
if not cap.isOpened():
	cap.open()
if not cap.isOpened():
	print "ERROR WITH CAMERA"		
arduino = serial.Serial('/dev/ttyACM0',9600, timeout = 1)
##---------------------------##


##-----------MAIN FUNCTIONS-----------##
def takePicture():
	global mainFrame
	for i in range(4):
		cap.grab()
	goodFrm, mainFrame = cap.read()
	print "I took a pic"
	return goodFrm

def analizeEnviroment():
	# This function manages the walk throguh the corral zone that Rob will 
	# carry out to search for a cow that is suitable to milk.
	global headingWall
	cowFound = False
	row = 1
	
	# This subproces is to turn up the camera agle
	# time.sleep(3)	
	# subprocess.Popen([UVCDYNCTRLEXEC,"-s","Tilt Reset","--","1"])
	# time.sleep(3)
	# subprocess.Popen([UVCDYNCTRLEXEC,"-s","Tilt (relative)","--","-550"])
	
	# At this time we must have the terrine grabed and we should be pointing North
	# we will seek the cow for ever.
	while 1:
		#print "Beginning to anaEnv"
		#print "Turn Right"
		# Rob is in the first row
		res = "0"
		if headingWall == "E":
			print "Going east"
			print "Opportunity to find cow: 1"
			turnBot("105")
			cowFound, cowTissue,allSquares = isThereACowRecife(-1)
			if cowFound:
				print "Cow Found"
				go,lL,lR,lT,theta = isCowMilkeable(cowTissue,allSquares)
				if go:
					print "Ready to go"
					if(prepareToMilk(lL,lR,lT,theta)):
						return True
					else: 
						pass
			for di in range(4):
				print "Opportunity to find cow: ", di + 2
				turnBot("-15")
				cowFound, cowTissue,allSquares = isThereACowRecife(-1)
				if cowFound:
					print "Cow Found"
					go,lL,lR,lT,theta = isCowMilkeable(cowTissue,allSquares)
					if go:
						print "Ready to go"
						if(prepareToMilk(lL,lR,lT,theta)):
							return True
						else: 
							pass
			turnTo()
		elif headingWall == "W":
			print "Going South"
			print "Opportunity to find cow: 1"
			turnBot("-105")
			cowFound, cowTissue,allSquares = isThereACowRecife(-1)
			if cowFound:
				print "Cow Found"
				go,lL,lR,lT,theta = isCowMilkeable(cowTissue,allSquares)
				if go:
					print "Ready to go"
					if(prepareToMilk(lL,lR,lT,theta)):
						return True
					else: 
						pass

			for di in range(4):
				print "Opportunity to find cow: ", di + 2
				turnBot("15")
				cowFound, cowTissue,allSquares = isThereACowRecife(-1)
				if cowFound:
					print "Cow Found"
					go,lL,lR,lT,theta = isCowMilkeable(cowTissue,allSquares)
					if go:
						print "Ready to go"
						if(prepareToMilk(lL,lR,lT,theta)):
							return True
						else: 
							pass
			turnTo()				

		#''' Cow not found, so we must continue traversing the arena '''
		res = moveBot("200")

		if res == "0":
			print "Rob has't arrived to the wall"
			pass 
		else:
			print "Both sensors have reached distance"
			# Rob is in the corner... or not...
			# checkCorner = True
			turnBot("right")
			moveBot("10")
			turnBot("right")
			headingWall = updateDirection(headingWall)
			headingWall = updateDirection(headingWall) 
		# elif res == "-1":
		# 	# Something went wrong, distance not reached 
		# 	# turn robot one row further and keep looking
		# 	# change directions and look in other way
		# 	# or skip cow
		# 	#			##### TO DO #####
		# 	#					*******			
		# 	row = row + 1 
		# 	#					*******

def findTank():
	good = takePicture()
	if good:
		hsv = cv2.cvtColor(mainFrame,cv2.COLOR_BGR2HSV)

		# Define 'red' in HSV colorspace
		lower_range = np.array([169,100,100], dtype=np.uint8)
		upper_range = np.array([189,255,255], dtype=np.uint8)

		# Threshold the HSV image to get only red color
		mask = cv2.inRange(hsv, lower_range, upper_range)

		# Bitwise-AND mask and original image
		res = cv2.bitwise_and(mainFrame,mainFrame,mask=mask)
		res = cv2.medianBlur(res, 5)

		# cv2.imshow('m',mainFrame)
		# cv2.imshow('Color Detector', res)
		# cv2.waitKey(0)
		# cv2.destroyAllWindows()
	
def findMaxLevel(tissue):
	# Find the level of the tissue that has most squares. If tie, the higher.
	maxLevel = []
	levels = []
	for t in tissue:
		levels.append(t.getLevel())
	modeLevels = statistics.mode(levels)
	for i in range(len(tissue)):
		t = tissue[i]
		# Check for the 1st square of the most popular level
		if t.getLevel() == modeLevels:
			while t.getLevel() == modeLevels:
				maxLevel.append(t)
				i += 1
				# Update the variable 't' or return maxLevel.
				if i < len(tissue):
					t = tissue[i]
				else:
					return maxLevel
			return maxLevel

def moveTo50(x):
	# Move Rob to be 50 cm far away from the cow
	y = 29.69*math.exp(0.0044*x)
	# print "y: ",y
	# print "movement", int(y-50)
	if y > 45:
		moveBot(str(int(y - 40)))
	elif y < 35:
		moveBot(str(int(y - 40)))
	return y

def center2center(left,right,top,theta):
	moveTo50(top)
	if left > right:
		correction = int((left- 100)/8.5) # cm
		if theta > 0:
				turnBot(str(90 - theta * 2))
				moveBot(str(correction))
				turnBot(str(-90))
		else:
			turnBot(str(-(90 + theta * 2)))
			moveBot(str(correction))
			turnBot(str(90))		
	else:
		correction = int((right-100)/8.5) # cm
		if theta > 0:
				turnBot(str(90 - theta * 2))
				moveBot(str(correction))
				turnBot(str(-90))
		else:
			turnBot(str(-(90 + theta * 2)))
			moveBot(str(correction))
			turnBot(str(90))

def calcCowLimits(maxLvl):
	maxLvl = sorted(maxLvl, key=lambda x:x.getX(), reverse = False)
	limitRight = maxLvl[len(maxLvl)-1].getTopRightC()[0]
	limitLeft = maxLvl[0].getX()
	maxLvl = sorted(maxLvl, key=lambda x:x.getY(), reverse = False)
	topY = maxLvl[0].getY()
	return limitLeft, limitRight, topY

def isThereACow(flag):
	global mainFrame
	global binValue
	maxLenT = [] # maximumLenghtTissue
	cowRecCopy = []
	minNumSquares = 5
	# mainFrame = cv2.imread('/home/pi/pruebasVision/FotosVaca/img4.jpg') 
	gF = True
	gF = takePicture() # returns boolean to know if the picture is OK
	if gF:
		filteredFrame = rb.clearImage(mainFrame)	# Clear the image with a GaussianBlur
		if flag == -1:
			# FOR: search for the best threshold value
			for binValueT in range(30,130,3):
				thresFrame = rb.doThresHold(filteredFrame, binValueT) # Thresholds the image and erodes it
				# print "binval:", binValueT
				# cv2.imshow('t',thresFrame)
				# cv2.waitKey(0)
				# cv2.destroyAllWindows()
				contours = rb.findContours(thresFrame) # Finds all the contours inside the image
				cowRectangles = rb.getGoodSquares(contours,mainFrame,thresFrame) # From contours, extract possile cow squares
				newCowRectangles = sorted(cowRectangles, key=lambda x:x.getY(), reverse=True)
				# When there are more than 'minNumSquares', it can be found at least one tissue
				if len(newCowRectangles) > minNumSquares:
					cowRecCopy = deepcopy(cowRectangles)
					greatestTissue = rb.makeTissue(newCowRectangles,[],50,0,[0,0],0)
					if len(greatestTissue) > len(maxLenT):
						maxLenT = greatestTissue
						binValue = binValueT

			#-------END FOR------
			# for c in cowRecCopy:
			# 	cv2.rectangle(mainFrame,(c.getX(),c.getY()),(c.getX()+c.getW(),c.getY()+c.getH()),(255,255,255),4)
			# drawGreatestTissue(maxLenT)

			if len(maxLenT) > minNumSquares:
				return True, maxLenT
			else:
				return False, maxLenT
		elif flag == 0:
			thresFrame = rb.doThresHold(filteredFrame, binValue) # Thresholds the image and erodes it
			contours = rb.findContours(thresFrame) # Finds all the contours inside the image
			cowRectangles = rb.getGoodSquares(contours,mainFrame) # From contours, extract possile cow squares
			newCowRectangles = sorted(cowRectangles, key=lambda x:x.getY(), reverse=True)
			maxLenT = rb.makeTissue(newCowRectangles,[],20,0,[0,0],0)
			return True, maxLenT
	return False, maxLenT

def isThereACowRecife(flag):
	global mainFrame
	global binValue
	maxLenT = [] # maximumLenghtTissue
	allSquares = [] # Store, in each iteration of the binarization, the squares found in the image
	minNumSquares = 4
	# mainFrame = cv2.imread('/home/pi/pruebasVision/FotosVaca/img25.jpg') 
	gF = True
	gF = takePicture() # returns boolean to know if the picture is OK
	if gF:
		filteredFrame = rb.clearImage(mainFrame)	# Clear the image with a GaussianBlur
		equalizedFrame = cv2.equalizeHist(filteredFrame)
		if flag == -1:
			# FOR: search for the best threshold value
			for binValueT in range(40,131,3):
				cp0 = cp1 = cp2 = deepcopy(equalizedFrame)

				thresFrame0 = rb.doThresHold(cp0, binValueT,7,1) 
				contours0 = rb.findContours(thresFrame0) 
				cowRectangles0 = rb.getGoodSquares(contours0,mainFrame,thresFrame0) 
				findEquals(allSquares,cowRectangles0,15)

				thresFrame1 = rb.doThresHold(cp1, binValueT,3,3) # Thresholds the image and erodes it
				contours1 = rb.findContours(thresFrame1) # Finds all the contours inside the image
				cowRectangles1 = rb.getGoodSquares(contours1,mainFrame,thresFrame1) # From contours, extract possile cow squares
				findEquals(allSquares,cowRectangles1,15)

				thresFrame2 = rb.doThresHold(cp2, binValueT,5,2) 
				contours2 = rb.findContours(thresFrame2) 
				cowRectangles2 = rb.getGoodSquares(contours2,mainFrame,thresFrame2) 
				findEquals(allSquares,cowRectangles2,15)

				del cp0
				del cp1
				del cp2
			print "im done with thres"
			#-------END FOR------
			# for c in allSquares:
			# 	cv2.rectangle(mainFrame,(c.getX(),c.getY()),(c.getX()+c.getW(),c.getY()+c.getH()),(255,255,255),4)
			# When there are more than 'minNumSquares', it can be found at least one tissue
			if len(allSquares) > minNumSquares:
				tempAllSquares = deepcopy(allSquares)
				maxLenT = rb.makeTissue(tempAllSquares,[],50,0,[0,0],0)

				# drawGreatestTissue(maxLenT)
				# cv2.imshow("m",mainFrame)
				# cv2.waitKey(5000)
				# cv2.destroyAllWindows()
				if len(maxLenT) > minNumSquares:
					return True,maxLenT,allSquares
	return False,[],[]

def findEquals(allSqrs,partial,epsilon):
	while len(partial) > 0:
		testSqr = partial.pop(0)
		found = False
		for compSqr in allSqrs:
			if (distanceBCorners(compSqr.getTopLeftC(),testSqr.getTopLeftC()) < epsilon or distanceBCorners(compSqr.getTopRightC(),testSqr.getTopRightC()) < epsilon or distanceBCorners(compSqr.getBotLeftC(),testSqr.getBotLeftC()) < epsilon or distanceBCorners(compSqr.getBotRightC(),testSqr.getBotRightC()) < epsilon) and not found:
				found = True 
				if testSqr.getArea() > compSqr.getArea():
					compSqr.x = testSqr.x
					compSqr.y = testSqr.y
					compSqr.w = testSqr.w
					compSqr.h = testSqr.h
					compSqr.area = testSqr.area
					compSqr.level = testSqr.level
					compSqr.topLeftC = testSqr.topLeftC
					compSqr.topRightC = testSqr.topRightC
					compSqr.botLeftC = testSqr.botLeftC
					compSqr.botRightC = testSqr.botRightC
				
		if not found:
			allSqrs.append(testSqr)

def isCowMilkeable(tissue,squares):
	# INPUT: maximunLengthTissue found in isThereACow
	# OUTPUT : bool to go and milk the cow, limLeft, limRight, limTop
	# if tissue[0].getLevel() != tissue[1].getLevel() and tissue[1].getLevel() == tissue[2].getLevel():
	# 	# To remove any noise that is higher than the cow
	# 	tissue.pop(0)

	if tissue[0].getLevel() == tissue[1].getLevel() and tissue[1].getLevel() == tissue[2].getLevel():
		# Tissue has the 3 squares on the top...
		if len(tissue) >= 6:
			if (tissue[3].getLevel() == tissue[4].getLevel() and tissue[4].getLevel() == tissue[5].getLevel()):
				# ... and also the tissue has the 3 squares from the second row...
				print "Found the 6 squares from cow"
				tempLevel = [tissue[0],tissue[1],tissue[2],tissue[3],tissue[4],tissue[5]]
				limLeft,limRight,limTop = calcCowLimits(tempLevel)
				return True,limLeft,limRight,limTop,0
		if len(tissue) >= 5:
			if tissue[3].getLevel() == tissue[4].getLevel():
				print "Found 5/6 squares 1.0"
				tempLevel = [tissue[0],tissue[1],tissue[2],tissue[3],tissue[4]]
				limLeft,limRight,limTop = calcCowLimits(tempLevel)
				coinLeft = 0
				coinRight = 0
				for s in squares:
					if limLeft != s.getX() and abs(limLeft - s.getX()) < 15:
						coinLeft += 1
					elif limRight != s.getX()+s.getW() and abs(limRight - (s.getX()+s.getW())) < 15:
						coinRight += 1
				if coinLeft != 0 or coinRight != 0:
					if coinLeft > coinRight:
						limRight += tissue[0].getW()
					else:
						limLeft -= tissue[0].getW()

					return True,limLeft,limRight,limTop,0

	elif tissue[0].getLevel() == tissue[1].getLevel() and tissue[1].getLevel() != tissue[2].getLevel():
		if len(tissue) >= 5:
			if tissue[2].getLevel() == tissue[3].getLevel() and tissue[3].getLevel() == tissue[4].getLevel():
				print "Found 5/6 squares 2.0"
				tempLevel = [tissue[0],tissue[1],tissue[2],tissue[3],tissue[4]]
				limLeft,limRight,limTop = calcCowLimits(tempLevel)
				coinLeft = 0
				coinRight = 0
				for s in squares:
					if limLeft != s.getX() and abs(limLeft - s.getX()) < 15:
						coinLeft += 1
					elif limRight != s.getX()+s.getW() and abs(limRight - (s.getX()+s.getW())) < 15:
						coinRight += 1
				if coinLeft != 0 or coinRight != 0:
					if coinLeft > coinRight:
						limRight += tissue[0].getW()
					else:
						limLeft -= tissue[0].getW()

					return True,limLeft,limRight,limTop,0

	
	return False,0,0,0,0
	# listMaxLevel = findMaxLevel(tissue)
	# theta,A,B = rb.ajusteDeCurvas(listMaxLevel)
	# limLeft,limRight,limTop = calcCowLimits(listMaxLevel,tissue)
	
	##-------PRINTS-------
	# drawGreatestTissue(tissue)
	# drawSlope(A,B)
	# drawLimits(limLeft,limRight,limTop)
	# cv2.imshow('mF',mainFrame)
	# cv2.waitKey(0)
	# cv2.destroyAllWindows()
	##--------------------
	# if (640 - limLeft - (640 - limRight)) < 200:
	# 	# There is a cow but you can't milk it
	# 	return False,limLeft,limRight,limTop,theta
	# else:
	# 	# Go milk the cow
	# 	return True,limLeft,limRight,limTop,theta

def prepareToMilk(lL,lR,lT,t):
	moveTo50(lT)
	actCenter = centerOfCow(lL,lR)
	print "Act Center: ",actCenter
	if actCenter < 440 and actCenter > 200:
		cv2.line(mainFrame,(actCenter,0),(actCenter,480),(255,0,0),3)
		cv2.line(mainFrame,(320,0),(320,480),(255,0,0),3)
		if actCenter > 330:
			movement = abs(actCenter - 330) / 10
			turnBot(str(movement))
		elif actCenter < 310:
			movement = abs(actCenter - 330) / 10
			turnBot("-"+str(movement))
	print "Cow ready to milk"
	return True
		
def isThereATank():
	# Arrange the inclination of the camera
	subprocess.Popen([UVCDYNCTRLEXEC,"-s","Tilt Reset","--","1"])

	# Load the new picture
	global mainFrame
	tank = [0,0,0,0,0]
	gF = True
	gF = takePicture()
	# mainFrame = cv2.imread('/home/pi/pruebasVision/FotosVaca/img19.jpg')
	if gF:
		# Converting to HSV
		copyMF = deepcopy(mainFrame)
		hsv = cv2.cvtColor(copyMF,cv2.COLOR_BGR2HSV)

		# Defining the boundries
		lower_orange = np.array([0,120,120])
		upper_orange = np.array([50,255,255])

		# Create a mask to find the orange
		mask = cv2.inRange(hsv,lower_orange,upper_orange)

		# Use contours to find the tank
		contours = rb.findContours(mask)
		for cnt in contours:
			area = cv2.contourArea(cnt)
			x,y,w,h = cv2.boundingRect(cnt)
			if area > 1000 and area > tank[0]:
				tank = [area,x,y,w,h]

		# Print the tank in the image
		# cv2.rectangle(mainFrame,(tank[1],tank[2]),(tank[1]+tank[3],tank[2]+tank[4]),(0,255,0),4)
		# cv2.imshow('mainF',mainFrame)
		# cv2.imshow('mask',mask)
		# cv2.waitKey(0)
		# cv2.destroyAllWindows()

		if tank[0] > 1000:
			return True, tank
		else:
			return False, tank

def centerToTank(tank):
	tCenter = tank[1] + tank[3]*0.5
	if tCenter > 325:
		turnBot("7")
		_,tank = isThereATank()
		tCenter = tank[1] + tank[3]*0.5
		while tCenter > 325:
			turnBot("7")
			_,tank = isThereATank()
			tCenter = tank[1] + tank[3]*0.5
	elif tCenter < 315:
		turnBot("-7")
		_,tank = isThereATank()
		tCenter = tank[1] + tank[3]*0.5
		while tCenter > 325:
			turnBot("-7")
			_,tank = isThereATank()
			tCenter = tank[1] + tank[3]*0.5

def startMode(fileName):
	file = open(fileName,'r')
	num = file.read()
	file.close()
	file = open(fileName,'w')
	file.write(str(int(num) + 1))
	file.close()
	return num

# def huntingCow(theta, maxLevel):
	# maxLevel = sorted(maxLevel, key=lambda x:x.getX(), reverse=False)
	# xLeft = maxLevel[0]
	# xRight = 640 - maxLevel[len(maxLevel)-1]
	# if len(maxLevel) > 3:
	# 	if abs(xLeft - xRight) < 40:
	# 		if theta > 0 and theta < 10:

##------------------------------------##

##-----------SECONDARY FUNCTIONS-----------##
def drawClusters(clusters):
	global mainFrame
	for i in range(len(clusters)):
		b = int ( random.uniform(50,255))
		g = int ( random.uniform(50,255))
		r = int ( random.uniform(50,255))
		list_1 = clusters[i].get_old_points()
		x,y = clusters[i].get_center()
		cv2.circle(mainFrame,(x,y),10,(b,g,r),4)
		for j in range (len(list_1)):
			x = list_1[j][0]
			y = list_1[j][1]
			cv2.circle(mainFrame,(x,y),5,(b,g,r),-1)

def clustersNotEmpty(clusters):
	for cluster in clusters:
		if len(cluster.get_old_points()) <= 1:
			return False
	return True	

def updateDirection(lasDir):

	if lasDir == "N":
		return "E"
	elif lasDir == "S":
		return "W"
	elif lasDir == "E":
		return "S"
	else:
		return "N"

def drawGreatestTissue(greatestTissue):
	global mainFrame
	font = cv2.FONT_HERSHEY_SIMPLEX
	areaT = 0
	for c in greatestTissue:
		areaT += c.getArea()
		b = int ( random.uniform(50,255))
		g = int ( random.uniform(50,255))
		r = int ( random.uniform(50,255))
		x = c.getX()
		y = c.getY()
		cv2.circle(mainFrame,(x,y),5,(b,g,r),-1)
		cv2.putText(mainFrame,(str(c.getLevel())),(c.getX(),c.getY()), font, 0.5,(0,0,255),1,cv2.LINE_AA)
	# areaT /= len(greatestTissue)
	# cv2.putText(mainFrame,(str(areaT)),(50,50), font, 1,(0,0,255),1,cv2.LINE_AA)

def drawSlope(A,B):
	x1 = 0
	x2 = 600
	y1 = int(A*x1 + B)
	y2 = int(A*x2 + B)
	cv2.line(mainFrame,(x1,y1),(x2,y2),(0,0,255),3)

def drawLimits(left,right,y):
	font = cv2.FONT_HERSHEY_SIMPLEX
	cv2.line(mainFrame,(left,0),(left,480),(255,0,0),3)
	cv2.line(mainFrame,(right,0),(right,480),(255,0,0),3)
	cv2.line(mainFrame,(0,y),(640,y),(255,0,0),3)
	cv2.putText(mainFrame,("diff L: " + str(left)),(30,20), font, 0.8,(0,0,255),1,cv2.LINE_AA)
	cv2.putText(mainFrame,("diff R: " + str(640-right)),(30,50), font, 0.8,(0,0,255),1,cv2.LINE_AA)
	cv2.putText(mainFrame,("diff Top: " + str(y)),(30,80), font, 0.8,(0,0,255),1,cv2.LINE_AA)

def readFromFile(fileName):
	num = open('begin.txt','r').read()
	print num
	num = str(1+int(num))
	file = open('begin.txt','w')
	file.write(num)
	file.close()

def centerOfCow(l,r):
	return (l+r)/2

def distanceBCorners(c1,c2):
	x1 = c1[0]
	x2 = c2[0]
	y1 = c1[1]
	y2 = c2[1]
	return rb.distance(x1,y1,x2,y2)

def emiloTest():
	checkForArduino()
	cowFound, cowTissue,allSquares = isThereACow(-1)
	if cowFound:
		# print "Cow Found"
		go,lL,lR,lT,theta = isCowMilkeable(cowTissue,allSquares)
		if go:
			prepareToMilk(lL,lR,lT,theta)
			milk()
			# print "Theta: ",theta
			# if go:
			# 	print "Trying to milk..."
			# 	center2center(lL,lR,lT,theta)
			# 	milk()
##-----------------------------------------##

##-----------Arduino Interaction-----------##
def checkForArduino():
	# Send a 'b' to tell the Arduino the RaspberryPi is alive
	# print "Conecting with arduino"
	time.sleep(3)
	arduino.write("b")
	ans = wait4ArduAnswer()	
	# print "Time to boot arduino: ", (time.time() - start)
	print "Arduino is alive",ans
	return True

def confirmTerrineZone(): # *********CHECK THIS**********
	# This function is for the 1st case of the Arduino. The position of the terrines 
	# should detect a wall with the left and back distance sensors.
	arduino.write("1")	# Execute the 1st state of the arduino
	ans = wait4ArduAnswer()
	print "Confirm terrine zone: ", ans
	return ans

def findTerrine():
	arduino.write("2")
	ans = wait4ArduAnswer()
	print "Terrine Found: ", ans
	return ans

def grabTerrine():
	arduino.write("3")
	ans = wait4ArduAnswer()
	print "Terrine grabed: ", ans
	return ans

def moveBot(cm):
	print "Moving Fwd"
	if cm == "forward":
		cm = "50"
	elif cm == "backward":
		cm = "-50"

	arduino.write("4")
	arduino.write("0")
	arduino.write(cm)
	print "FWD complete"
	return wait4ArduAnswer()

def turnBot(degrees):
	if degrees == "right":
		#print "Turn Right"
		degrees = "90"
	elif degrees == "left":
		#print "Turn Left"
		degrees = "-90"
        
	arduino.write("4")
	arduino.write("1")
	arduino.write(degrees)
	return wait4ArduAnswer()

def turnTo():
	global headingWall
	arduino.flushOutput()
	arduino.flushInput()
	print "TurnTO"
	arduino.write("4")
	arduino.write("2")
	if headingWall == "N":
		arduino.write("0")
	elif headingWall == "E":
		arduino.write("90")
	elif headingWall == "S":
		arduino.write("180")
	elif headingWall == "W":
		arduino.write("270")
	return wait4ArduAnswer()
	print "TurnTo complete"

def wait4ArduAnswer():
	print "Waiting 4 Arduino..."
	while(arduino.inWaiting() <= 0):
		pass
	print "DONE"
	time.sleep(2)
	return arduino.read(arduino.inWaiting())

def wait4ArduAnswerBoot(timeout):
	# print "Waiting 4 Arduino..."
	start = time.time()
	actTime = time.time()
	while(arduino.inWaiting() <= 0 and actTime - start < timeout):
		actTime = time.time()
	arduino.flushOutput()
	arduino.flushInput()
	if actTime - start > timeout:
		# Timeout reached
		return False
	else:
		# Answer recieved before time out
		return True

def flush():
	arduino.flushOutput()
	arduino.flushInput()

def milk():
	arduino.write("7")
	print "bot going down the cow"
	ans = wait4ArduAnswer()
	return ans

def milkTheCow():
	arduino.write("8")
	wait4ArduAnswer()

def goAlamus():
	# After we milked cow, it's time to go to the gate
	arduino.write("9")
	arduino.write("270")
	# Get to the wall you were before
	ans = wait4ArduAnswer()
	print "Get out of the cow: ", ans
	arduino.write("5")
	ans = wait4ArduAnswer()
	print "Going for the red block: ", ans
	moveBot("200")
	turnBot(lastTurn)
	moveBot("200")
	arduino.write("6")
	wait4ArduAnswer()

##--------------------------------------##

##-----------LOOP-----------##
def myMain():
	# takePicture()
	# cv2.imshow('m',mainFrame)
	# cv2.waitKey(0)
	if(checkForArduino()):
		confirmTerrineZone()	
		print "In terrine zone"
		findTerrine()
		print "found"
		grabTerrine()
		print "grabed"
		print "Get away from the terrines zone"
		moveBot(firstWalk)
		turnBot("right")
		moveBot("20")
		turnBot("left")
		while (1):
			analizeEnviroment()	
			ans = milk()
		 	milkTheCow()
		 	goAlamus()
			
				# moveBot("-40")
			 # 	turnTo()
				 	
				# time.sleep(5)
##-------------------------##
# myMain()
checkForArduino()
# cowFound, cowTissue,allSquares = isThereACowRecife(-1)
# if cowFound:
# 	# print "Cow Found"
# 	go,lL,lR,lT,theta = isCowMilkeable(cowTissue,allSquares)
# 	drawLimits(lL,lR,lT)
# 	if go:
# 		prepareToMilk(lL,lR,lT,theta)
# 		ans = milk()
# 		print ans
# 		if(ans == "0"):
# 			 milkTheCow()
# 		elif(ans == "-1" or ans == "-2"):
# 			moveBot("-40")
# 		 	turnTo()
milkTheCow()
# goAlamus()
# else: 
# 	print "No hay vaca"
# drawGreatestTissue(cowTissue)
# cv2.imshow('m',mainFrame)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

##-----------Final Instructions-----------##
cap.release()
##----------------------------------------##