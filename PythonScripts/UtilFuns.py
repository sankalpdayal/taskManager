from pathlib import Path
from random import *
import re
import pandas as pd
import time
import datetime

def readFileStripped(filename):
	my_file = Path(filename)
	if my_file.is_file():
		with open(filename) as f:
			content = f.readlines()
		content = [x.strip() for x in content] 
		return content
	else:
		return []

def resetDFIndeces(df):
	df = df.reset_index(drop = True)
	return df
	
def checkForKeyWord(line, keyword, position = -1):
	if len(line) == 0:
		return False
	if position == -1:
		return (line.find(keyword) !=-1)
	else:
		if position > len(line):
			return False
		else:
			return line[position:(position+len(keyword))] == keyword
			
			
def getTagsInBrackets(line):
	tags = re.findall(r"(?<=\[)(.*?)(?=\])",line)
	return tags

def getContentBetweenWords(line, startWord, stopWord):
	s = re.escape(startWord) + r"(.*?)" + re.escape(stopWord)
	content = re.findall(s,line)
	return content
	
def generateUID(allUIDsDF):
	if len(allUIDsDF) == 0:  
		return randint(1, 1000000)
		
	newUID = -1
	while newUID == -1 :
		tempNewUID = randint(1, 1000000)
		if len(allUIDsDF[allUIDsDF == tempNewUID]) == 0:
			newUID = tempNewUID
	return newUID

def writeToPickleDF(filename, df):
	df.to_pickle(filename)
	
def loadPickleDF(filename):
	my_file = Path(filename)
	if my_file.is_file():
		df = pd.read_pickle(filename)
		return df
	else:
		return pd.DataFrame()

def splitStringUsingKeyword(line, keyword):
	splittedString = {}
	splittedString['start'] = line[:line.index(keyword)]
	splittedString['end'] = line[line.index(keyword) + len(keyword):] 
	return splittedString

def checkForKeyWordWithSeparation(line, keyword):
	if line == keyword:
		return True
	if checkForKeyWord(line, ' ' + keyword + ' '):
		return True
	if checkForKeyWord(line, ',' + keyword + ' '):
		return True
	if checkForKeyWord(line, ',' + keyword + ','):
		return True
	if checkForKeyWord(line, ' ' + keyword + ','):
		return True
	if checkForKeyWord(line, ' ' + keyword,len(line)-len(keyword)-1):
		return True
	if checkForKeyWord(line, ',' + keyword,len(line)-len(keyword)-1):
		return True
	if checkForKeyWord(line, keyword + ',',0):
		return True
	if checkForKeyWord(line, keyword + ' ',0):
		return True
	
	return False

def checkForDays(dayString):
	if checkForKeyWordWithSeparation(dayString, 'Everyday'):
		return 1111111
	if checkForKeyWordWithSeparation(dayString, 'Daily'):
		return 1111111
		
	days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
	day_index = 0
	dates = 0
	for day in days:
		if checkForKeyWordWithSeparation(dayString, day):
			dates += 10**day_index
		day_index+=1
		
	if dates == 0:
		dates = -1
	return dates
	
def createStringForDate(date):
	if date%10 == 1:
		return str(date) + 'st'
	if date%10 == 2:
		return str(date) + 'nd'
	if date%10 == 3:
		return str(date) + 'rd'
	return str(date) + 'th'

def getEnglishNumberFromString(dateString):
	for date in range(0,32):
		if checkForKeyWordWithSeparation(dateString, createStringForDate(date)):
			return date		
	return -1
	
def checkForDates(dateString):
	dates = 0
	for date in range(0,32):
		if checkForKeyWordWithSeparation(dateString, createStringForDate(date)):
			dates += 2**date
	if dates == 0:
		dates = -1
	return dates
	
def getDaysOfMonth(dateValue):
	daysofMonth = []
	for date in range(0,32):
		if int(dateValue%2) == 1:
			daysofMonth.append(date)
		dateValue = int(dateValue/2)
	return daysofMonth
		
def getDaysOfWeek(date):
	daysOfWeek = []
	days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
	dates = 0
	for day in days:
		if int(date%10) == 1:
			daysOfWeek.append(day)
		date = int(date/10)
	return daysOfWeek
	
def getTime(timeString):
	timeStrings = splitStringUsingKeyword(timeString, ':')
	hours = timeStrings['start']
	timeStrings = splitStringUsingKeyword(timeStrings['end'], ' ')
	minutes = timeStrings['start']
	if timeStrings['end'] == 'am' or int(hours) == 12:
		time = int(hours)*60 + int(minutes)
	else:
		time = (int(hours) + 12)*60 + int(minutes)
	return time
	
def getTimeString(time):
	hours = int(time/60)
	minutes = time%60
	if minutes >= 10:
		minutes_string = str(minutes)
	else:
		minutes_string = '0' + str(minutes)
		
	if hours>=12:
		if hours == 12:
			timeString = str(hours) + ':' + minutes_string + ' pm'
		else:
			timeString = str(hours-12) + ':' + minutes_string + ' pm'
	else:
		timeString = str(hours) + ':' + minutes_string + ' am'
	return timeString
	
def getDeletedCells(dfNew, dfOld):
	merged = pd.merge(dfNew, dfOld, how='outer', indicator=True)
	cellsDeleted = merged[merged['_merge'] == 'right_only']
	return 	cellsDeleted

def getDetailsOfCompletion(completionString):
	completionDetails = {}
	if checkForKeyWord(completionString, '-'):
		splittedString = splitStringUsingKeyword(completionString, '-')
		completionDetails['lastCompleted'] = getTime(splittedString['end'])
		completionDetails['duration'] = getTime(splittedString['end']) - getTime(splittedString['start'])
	else:
		completionDetails['lastCompleted'] = getTime(completionString)
		completionDetails['duration'] = -1
	return completionDetails

def getDateString(date_value):
	date_string = ''
	for date in range(0,32):
		if int(date_value%2) == 1:
			last_digit = date%10
			if last_digit == 1:
				temp = str(date) + 'st'
			if last_digit == 2:
				temp = str(date) + 'nd'
			if last_digit == 3:
				temp = str(date) + 'rd'
			if last_digit == 0 or last_digit > 3:
				temp = str(date) + 'th'
			if date_string == '':
				date_string = temp
			else:
				date_string = date_string + ', ' + temp
		date_value = int(date_value/2)
		
	return date_string	

def getDayString(date):
	date_string = ''
	days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
	dates = 0
	for day in days:
		if int(date%10) == 1:
			if date_string != '':
				date_string = date_string + ', ' + day
			else:
				date_string = day
		date = int(date/10)
		
	return date_string	
	
def getStringForFreqDateOcc(freq, date, occ):
	freqDateOccString = [];
	if freq == 'Weekly':
		if date == 1111111:
			freqDateOccString = 'Daily'
			return freqDateOccString
			
		if date == -1:
			if occ == 1:
				freqDateOccString = 'Weekly'
				return freqDateOccString
			else:
				freqDateOccString = 'Every ' + str(occ) + ' weeks'
				return freqDateOccString
		else:
			freqDateOccString = getDayString(date)
			if occ > 1:
				if occ == 2:
					freqDateOccString = freqDateOccString + ' of every 2nd week'
				if occ == 3:
					freqDateOccString = freqDateOccString + ' of every 3rd week'
				if occ > 3:
					freqDateOccString = freqDateOccString + ' of every ' + str(occ) + 'th week'	
			return freqDateOccString
				
	if freq == 'Monthly':
		if date == -1:
			if occ == 1:
				freqDateOccString = 'Monthly'
				return freqDateOccString
			else:
				freqDateOccString = 'Every ' + str(occ) + ' months'
				return freqDateOccString
		else:
			freqDateOccString = getDateString(date)
			if occ == 1:
				freqDateOccString = freqDateOccString + ' of every month'
			else:
				if occ == 2:
					freqDateOccString = freqDateOccString + ' of every 2nd month'
				if occ == 3:
					freqDateOccString = freqDateOccString + ' of every 3rd month'
				if occ > 3:
					freqDateOccString = freqDateOccString + ' of every ' + str(occ) + 'th month'	
			return freqDateOccString
	return str(freqDateOccString)

def getDayPriority(days):
	if days == 1111111:
		return 0
	else:
		priority = 0
		daysFound = 6
		for index in range(1,8):
			if days%10 == 1:
				priority += index*(10**daysFound)
				daysFound -= 1
			days = int(days/10)
		return priority

def updateFieldWithUID(df,uid,field,value):
	matchedRow = df[df['uid'] == uid]
	rowIndex = matchedRow.index.tolist()
	if len(rowIndex) == 0:
		print('Data frame doesnt have uid')
		return df
	if len(rowIndex) > 1:
		print('Data frame has more than one uid')
		return df
	
	dfValue = df.get_value(rowIndex[0],field)
	if dfValue != value:
		df.set_value(rowIndex[0],field, value) 	
	return df
	
def getValueFromRowinDF(df,field):
	if len(df) == 0:
		return []
	rowIndex = df.index.tolist()
	if len(rowIndex) == 0:
		print('Data frame doesnt have any rows')
		return []
	if len(rowIndex) > 1:
		print(df)
		print('Data frame has more than one rows')
		return []
	return df.get_value(rowIndex[0],field)
	
def getFieldValueWithUID(df,uid,field):
	if len(df) == 0:
		return []
	matchedRow = df[df['uid'] == uid]
	rowIndex = matchedRow.index.tolist()
	if len(rowIndex) == 0:
		print('Data frame doesnt have uid')
		return []
	if len(rowIndex) > 1:
		print('Data frame has more than one uid')
		return []
	return df.get_value(rowIndex[0],field)

def getDictFromRowwithUID(df,uid):
	if len(df) == 0:
		return {}
	matchedRow = df[df['uid'] == uid]
	if len(matchedRow) == 0:
		print('Data frame doesnt have uid')
		return {}
	if len(matchedRow) > 1:
		print('Data frame has more than one uid')
		return {}
	for index, row in matchedRow.iterrows():
		return row

def checkFieldWithUID(df,uid,field,value):
	if len(df) == 0:
		return False
	matchedRow = df[df['uid'] == uid]
	rowIndex = matchedRow.index.tolist()
	if len(rowIndex) == 0:
		print('Data frame doesnt have uid')
		return False
	if len(rowIndex) > 1:
		print('Data frame has more than one uid')
		return False
	
	dfValue = df.get_value(rowIndex[0],field)
	return dfValue == value
	
def appendDictAndResetIndexinDF(df,dict):
	df = df.append(pd.DataFrame([dict]))
	return resetDFIndeces(df)
	
def createSubDictWithFieldList(dict, fieldList):
	subDict = {}
	for field in fieldList:
		subDict[field] = dict[field]
	return subDict
	
def checkIfToBeDoneToday(days):
	if days == 1111111:
		return True
	dayOfWeek = datetime.date.today().weekday()
	days = int(days/(10**dayOfWeek))
	if days%10 == 1:
		return True
	else:
		return False
			
def checkIfWasDueInPast(days):
	if days == 1111111:
		return False
	dayOfWeek = datetime.date.today().weekday()
	if dayOfWeek == 0:
		return False
	days = days%(10**dayOfWeek)
	if days > 0:
		return True
	else:
		return False

def checkIfIsDueInFuture(days):
	if days == 1111111:
		return False
	dayOfWeek = datetime.date.today().weekday()
	dayOfWeek += 1
	days = int(days/(10**dayOfWeek))
	if days > 0:
		return True
	else:
		return False
	
def updateDaysToToday(days):
	if days == 1111111:
		return days
	dayOfWeek = datetime.date.today().weekday()
	if dayOfWeek > 0:
		days -= days%(10**(dayOfWeek))
	if days%(10**(dayOfWeek+1)) != 10**(dayOfWeek):
		days += (10**(dayOfWeek))
	return days
	
def updateDaysToTomorrow(days):
	if days == 1111111:
		return days
	dayOfWeek = datetime.date.today().weekday()
	dayOfWeek += 1
	days -= days%(10**(dayOfWeek))
	if dayOfWeek == 7:
		dayOfWeek = 0	
	if days%10**(dayOfWeek+1) != 10**(dayOfWeek):
		days += 10**(dayOfWeek)
	return days