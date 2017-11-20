import UtilFuns as utils
import pandas as pd
import time
import datetime
import pickle
from pathlib import Path
import numpy as np
import os

class TaskList:
	#Addresses
	__pickleDBAdd = []
	__textListDBAdd = []
	__progressDBAdd = []
	__notesDBAdd = []

	#Dataframes
	__allTasksDF = []
	__algoCustomerNamesDF = []
	__repeatingTaskFreqDF = []
	__weeklyTasksDF = []
	__dailyTasksDF = []
	__followupTasksDF = []
	
	#Time
	__dayChanged = False
	__weekChanged = False
	
	def __init__(self, config = []):
		#Initialize file names for databases
		if len(config) == 0:
			self.__pickleDBAdd = '../DB'
			self.__textListDBAdd = '../Lists'
			self.__progressDBAdd = '../Progress'
			self.__notesDBAdd = '../Notes'
		
	
	#Function: Reads old data frame stored in pickle and all tasks text file. Updates old data frames and returns change list
	#	Writes the new data frame
	#Input: <None>
	#Return: change list
	def loadAllTasks(self):
		#Load all tasks, algo customer names and repeating task data frames from pickle
		self.__allTasksDF = utils.loadPickleDF(self.__pickleDBAdd + '/' + 'allTasksDF.p')
		self.__algoCustomerNamesDF = utils.loadPickleDF(self.__pickleDBAdd + '/' + 'algoCustomerNamesDF.p')
		self.__repeatingTaskFreqDF = utils.loadPickleDF(self.__pickleDBAdd + '/' + 'repeatingTaskFreqDF.p')
		self.__followupTasksDF = utils.loadPickleDF(self.__pickleDBAdd + '/' + 'followupTasksDF.p')
		
		#Update all tasks, algo and repeating task data frames by reading the text file
		changeList = self.__updateAllTasksFromTextFile(self.__textListDBAdd + '/' + 'Tasks.txt')
		
		#Write updated data frames
		utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'allTasksDF.p',self.__allTasksDF)
		utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'algoCustomerNamesDF.p',self.__algoCustomerNamesDF)
		utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'repeatingTaskFreqDF.p',self.__repeatingTaskFreqDF)
		utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'followupTasksDF.p',self.__followupTasksDF)
		
		print('Loaded all tasks.')
		return changeList
		
		
	#Function: Reads all tasks text file line by line and update all tasks data frame
	#Input: all tasks text file name
	#Return: change list
	def __updateAllTasksFromTextFile(self, filename):
		#Init new change list
		changeList = []
		
		#Read contents of file line by line and remove new lines, tabs
		content = utils.readFileStripped(filename)
		if len(content) == 0:
			return changeList
			
		#Init current category as unknown
		currentCategory = 'Unknown'

		#Start new data frame to track uids read in text file.
		uidsInTextFile = pd.DataFrame()
		
		#Loop over all lines
		for line in content:
			if len(line) > 0:
				#Check if it is a task or category
				if self.__checkIfCurrentLineIsTask(line):
				
					#parse line to get all task dict
					taskDict = self.__parseAllTasks(currentCategory, line)
					
					#Depending on contents of task, it checks if task already exists or not
					uid = self.__checkIfTaskExists(taskDict)
					
					if uid != -1:
						#Task already exists in all task list
						
						#If task is algo, check if customer name is same, otherwise update it
						if taskDict['subCategory'] == 'Algo':
							if not utils.checkFieldWithUID(self.__algoCustomerNamesDF, uid, 'customer', taskDict['customer']):
								self.__algoCustomerNamesDF = utils.updateFieldWithUID(self.__algoCustomerNamesDF, uid, 'customer', taskDict['customer'])
								changeList = self.__updateChangeList(uid, 'allTasks', 'customerUpdated', changeList)
								
						#If status is repeating, check if freq, dates, occurance or last performed change, if yes, then update it
						if taskDict['status'] == 'Repeating':
							if not utils.checkFieldWithUID(self.__repeatingTaskFreqDF, uid, 'freq', taskDict['freq']):
								self.__repeatingTaskFreqDF = utils.updateFieldWithUID(self.__repeatingTaskFreqDF, uid, 'freq', taskDict['freq'])
								changeList = self.__updateChangeList(uid, 'allTasks', 'freqUpdated', changeList)
							
							if not utils.checkFieldWithUID(self.__repeatingTaskFreqDF, uid, 'dates', taskDict['dates']):
								self.__repeatingTaskFreqDF = utils.updateFieldWithUID(self.__repeatingTaskFreqDF, uid, 'dates', taskDict['dates'])
								changeList = self.__updateChangeList(uid, 'allTasks', 'datesUpdated', changeList)
							
							if not utils.checkFieldWithUID(self.__repeatingTaskFreqDF, uid, 'occ', taskDict['occ']):
								self.__repeatingTaskFreqDF = utils.updateFieldWithUID(self.__repeatingTaskFreqDF, uid, 'occ', taskDict['occ'])
								changeList = self.__updateChangeList(uid, 'allTasks', 'occuranceUpdated', changeList)
							
							if not utils.checkFieldWithUID(self.__repeatingTaskFreqDF, uid, 'lastPerformed', taskDict['lastPerformed']):
								self.__repeatingTaskFreqDF = utils.updateFieldWithUID(self.__repeatingTaskFreqDF, uid, 'lastPerformed', taskDict['lastPerformed'])
								changeList = self.__updateChangeList(uid, 'allTasks', 'lastPerformedUpdated', changeList)
						
						#if task has follow up
						if 'followupDate' in taskDict:
							#Check if task already exist in followup list, if yes then update follow up date, else create new task and then update follow up date.
							if len(self.__followupTasksDF[self.__followupTasksDF['uid'] == uid]) == 1:
								if utils.getFieldValueWithUID(self.__followupTasksDF, uid, 'followupDate') != taskDict['followupDate']:
									self.__followupTasksDF = utils.updateFieldWithUID(self.__followupTasksDF, uid, 'followupDate', taskDict['followupDate'])
									changeList = self.__updateChangeList(uid, 'allTasks', 'followupDateUpdated', changeList)
							else:
								self.__followupTasksDF = utils.appendDictAndResetIndexinDF(self.__followupTasksDF,{'uid':uid, 'followupDate': taskDict['followupDate']})
								changeList = self.__updateChangeList(uid, 'allTasks', 'followupAdded', changeList)
						
						
					else:	
						#Generate new UID
						if len(self.__allTasksDF) == 0:
							uid = utils.generateUID([])
						else:
							uid = utils.generateUID(self.__allTasksDF['uid'])
							
						taskDict['uid'] = uid
						
						#Update all tasks data frame
						allTaskDict = utils.createSubDictWithFieldList(taskDict, ['uid','category','details','notesFlag','progressFlag','status','subCategory'])
						self.__allTasksDF = utils.appendDictAndResetIndexinDF(self.__allTasksDF, allTaskDict)		
					
						#If algo Update algo data frame
						if taskDict['subCategory'] == 'Algo':
							algoDict = utils.createSubDictWithFieldList(taskDict, ['uid','customer'])
							self.__algoCustomerNamesDF = utils.appendDictAndResetIndexinDF(self.__algoCustomerNamesDF, algoDict)	
								
						#If repeating Update repeating task data frame
						if taskDict['status'] == 'Repeating':
							repTaskDict = utils.createSubDictWithFieldList(taskDict, ['uid','freq','dates','occ','lastPerformed'])
							self.__repeatingTaskFreqDF = utils.appendDictAndResetIndexinDF(self.__repeatingTaskFreqDF, repTaskDict)	
						
						#Update change list with change as new task added	
						changeList = self.__updateChangeList(uid, 'allTasks', 'taskAdded', changeList)
						
						#if task has follow up
						if 'followupDate' in taskDict:
							self.__followupTasksDF = utils.appendDictAndResetIndexinDF(self.__followupTasksDF,{'uid':uid, 'followupDate': taskDict['followupDate']})
							changeList = self.__updateChangeList(uid, 'allTasks', 'followupAdded', changeList)
						
					
					#Update data frame tracking uids in text file
					uidsInTextFile = uidsInTextFile.append(pd.DataFrame([{'uid':uid}]))
				else:
					#Current line is not a task, hence a category
					currentCategory = line
					
		#Since text file is completely read, check what uid's need to be deleted
		if len(uidsInTextFile) > 0:
			uidsDeleted = utils.getDeletedCells(uidsInTextFile, self.__allTasksDF['uid'].to_frame())
			if len(uidsDeleted) > 0:
				for index, row in uidsDeleted.iterrows():
					changeList = self.__updateChangeList(row['uid'], 'allTasks', 'taskDeletedFromAllTasks', changeList)
			
		else:
			print('All Tasks text file is empty')
			
		#return changelist to be used to update weekly and daily lists
		return changeList
	
	
	
	
	#Function: Check if current line has a task
	#Input: Line
	#Return: Boolean
	def __checkIfCurrentLineIsTask(self,line):
		#For line to be a task, first character should be *
		return utils.checkForKeyWord(line,'*',0)
	

	
	#Function: Create all task dictonary from line in Tasks.txt file
	#Input: Line having task, category
	#Output: All task dictonary 
	def __parseAllTasks(self, currentCategory, line):
		#Init empty dict
		task = {}
		tagsParsed = 0
		
		#Parse contents in brackets as tags
		tags = utils.getTagsInBrackets(line)
		
		#Minimum tag count should be 3
		if len(tags) < 3:
			print(line)
			print('Invalid Task found, there should be at least 3 tags')
			return tasks
		
		#Update category and first 3 tags
		task['category'] = currentCategory
		task['status'] = tags[0]						
		task['subCategory'] = tags[1]
		task['details'] = tags[2]
		tagsParsed = 3
		
		#If status is repeating then there will be at least 2 more tags
		if task['status'] == 'Repeating':
			if len(tags) < 5:
				print(line)
				print('Invalid Task found, repeating task should have at least 5 tags')
				return task
			
			#Get freq, date and occurance from freq tag and update in dict
			freqDateOcc = self.__getFreqDateOcc(tags[3])
			task['freq'] = freqDateOcc['freq']
			task['dates'] = freqDateOcc['dates']
			task['occ'] = freqDateOcc['occ']
			
			#Update last performed date in dict
			task['lastPerformed'] = tags[4]	
			tagsParsed = 5
			
		#If subCategory is Algo then there will be at least 1 more tag
		if task['subCategory'] == 'Algo':
			if len(tags) < 4:
				print(line)
				print('Invalid Task found, algo task should have at least 4 tags')
				return tasks
			task['customer'] = tags[3]
			tagsParsed = 4
	
		#There could be tags for progress and notes which have to be checked
		task['progressFlag'] = False
		task['notesFlag'] = False
		for currentTagIndex in range(tagsParsed,len(tags)):
			if tags[currentTagIndex] == 'Progress':
				task['progressFlag'] = True
			if tags[currentTagIndex] == 'Notes':
				task['notesFlag'] = True
			if utils.checkForKeyWordWithSeparation(tags[currentTagIndex], 'Followup'):
				task['followupDate'] = (tags[currentTagIndex][tags[currentTagIndex].index('Followup') + len('Followup'):]).strip()
				
		return task	
				
	
	#Function: Updates change list by appneding with the previous
	#Input: UID, source where change happened,  change type, previous change list
	#Output: Updated change list
	def __updateChangeList(self, uid, source, changeType, changeList):
		changeDict = {}
		changeDict['uid'] = uid
		changeDict['source'] = source
		changeDict['change'] = changeType
		changeList.append(changeDict)
		return changeList
	
	
	#Function: Depending on contents of task, it checks if task already exists or not 
	#Input: Task dict and check level, level 3: Highest, level 2: Medium, level 1: Lowest
	#Output: UID, if task doesnt exist returned value is -1
	def __checkIfTaskExists(self, task, checkLevel = 3):
		#Check if all task data frame or dict is empty
		if len(self.__allTasksDF) == 0 or len(task) == 0:
			return -1
		
		df = self.__allTasksDF
		#Check for critical fields [subCategory, details]
		df = df[(df['subCategory'] == task['subCategory']) & (df['details'] == task['details']) ]
		if len(df) == 0:
			return -1
		if checkLevel == 1:
			return utils.getValueFromRowinDF(df,'uid')
			
		#Check for secondry fields [category, details]
		df = df[(df['category'] == task['category']) & (df['status'] == task['status'])]
		if len(df) == 0:
			return -1
		else:
			return utils.getValueFromRowinDF(df,'uid')
			
	
	#Function: Interprates freq string and creates dictonary for freq, dates and occurance
	#Input: Freq string
	#Output: Dict with freq, dates and occurance
	def __getFreqDateOcc(self, freqDateString):
		freqDateOcc = {}
		freqDateOcc['freq'] = []
		freqDateOcc['dates'] = []
		freqDateOcc['occ'] = []
		
		if utils.checkForKeyWord(freqDateString, 'Daily'):
			freqDateOcc['freq'] = 'Weekly'
			freqDateOcc['dates'] = 1111111
			freqDateOcc['occ'] = 1
			return freqDateOcc
		
		if utils.checkForKeyWord(freqDateString, 'Weekly') or utils.checkForKeyWord(freqDateString, 'Every week'):
			freqDateOcc['freq'] = 'Weekly'
			freqDateOcc['dates'] = -1
			freqDateOcc['occ'] = 1
			return freqDateOcc		
		
		if utils.checkForKeyWord(freqDateString, 'Monthly') or utils.checkForKeyWord(freqDateString, 'Every month'):
			freqDateOcc['freq'] = 'Monthly'
			freqDateOcc['dates'] = -1
			freqDateOcc['occ'] = 1
			return freqDateOcc
			
		
		tokens = utils.getContentBetweenWords(freqDateString, 'Every', 'weeks')
		if len(tokens) > 0:	
			freqDateOcc['freq'] = 'Weekly'
			freqDateOcc['dates'] = -1
			freqDateOcc['occ'] = int(tokens[0])
			return freqDateOcc
		
		tokens = utils.getContentBetweenWords(freqDateString, 'Every', 'months')
		if len(tokens) > 0:	
			freqDateOcc['freq'] = 'Monthly'
			freqDateOcc['dates'] = -1
			freqDateOcc['occ'] = int(tokens[0])
			return freqDateOcc
		
		if utils.checkForKeyWord(freqDateString, 'of every'):
			splittedStrings = utils.splitStringUsingKeyword(freqDateString,'of every')
			#Before "of every"
			startString = splittedStrings["start"]
			days = utils.checkForDays(startString)		
			if days != -1:
				freqDateOcc['dates'] = days
			
			dates = utils.checkForDates(startString)		
			if dates != -1:
				freqDateOcc['dates'] = dates
			
			#After "of every"
			endString = splittedStrings["end"] 
			if utils.checkForKeyWord(freqDateString,'week'):
				freqDateOcc['freq'] = 'Weekly'
				
			if utils.checkForKeyWord(freqDateString,'month'):
				freqDateOcc['freq'] = 'Monthly'
				
			occurance = utils.getEnglishNumberFromString(endString)
			if occurance != -1:
				freqDateOcc['occ'] = occurance
			else:
				freqDateOcc['occ'] = 1
			return freqDateOcc
		else:
			days = utils.checkForDays(freqDateString)
			if days != -1:
				freqDateOcc['freq'] = 'Weekly'
				freqDateOcc['dates'] = days
				freqDateOcc['occ'] = 1
				return freqDateOcc
		return freqDateOcc
		
	
	#Function: Reads old data frame for weekly tasks stored in pickle and weekly tasks text file. 
	#	Updates old data frame and returns change list. Writes the new data frame
	#Input: <None>
	#Return: change list
	def loadWeeklyTasks(self):
		#Load old data frame from pickle
		self.__weeklyTasksDF = utils.loadPickleDF(self.__pickleDBAdd + '/' + 'weeklyTasksDF.p')
		
		#Update weekly tasks data frame from text file
		changeList = self.__updateWeeklyTasksFromTextFile(self.__textListDBAdd + '/' + 'WeeklyTasks.txt')
		
		#Write update data frame to pickle
		utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'weeklyTasksDF.p',self.__weeklyTasksDF)
		
		print('Loaded weekly tasks.')
		return changeList

		
	#Function: Reads weekly tasks text file line by line and update weekly tasks data frame
	#Input: weekly tasks text file name
	#Return: change list
	def __updateWeeklyTasksFromTextFile(self, filename):
		#Init new change list
		changeList = []
		
		#If weekly task DF is empty, weekly list data frame has to be created first before being read.
		if len(self.__weeklyTasksDF) == 0:
			self.__weekChanged = True
			self.__dayChanged = True
			changeList = self.regenerateWeeklyTasks()
			self.__weekChanged = False
			self.__dayChanged = False
		
		#Read contents of file line by line and remove new lines, tabs
		content = utils.readFileStripped(filename)
		if len(content) == 0:
			return changeList
		
		#Init current category as unknown
		currentCategory = 'Unknown'
		
		#Start new data frame to track uids read in text file.
		uidsInTextFile = pd.DataFrame()
		
		#Loop over all lines
		for line in content:
			if len(line) > 0:
				#Check if it is a task or category
				if self.__checkIfCurrentLineIsTask(line):
				
					#parse line to get weekly task dict
					taskDict = self.__parseWeeklyTasks(currentCategory, line)

					#Depending on contents of task, it checks if task already exists or not
					uid = self.__checkIfTaskExists(taskDict)
					
					if uid != -1:
						#Task exists in all task list
						
						#Check if status is not active, if it is not, make status active
						if not utils.checkFieldWithUID(self.__weeklyTasksDF, uid, 'weeklyStatus', 'Active'):
							self.__weeklyTasksDF = utils.updateFieldWithUID(self.__weeklyTasksDF, uid, 'weeklyStatus', 'Active')
							changeList = self.__updateChangeList(uid, 'weeklyTasks', 'taskActivatedInWeeklyTasks', changeList)
						
						#Check if obtained dates show that it was due in past then update to todays
						if utils.checkIfWasDueInPast(taskDict['days']):
							taskDict['days'] = utils.updateDaysToToday(taskDict['days'])
							
						#Check if days changed
						if not utils.checkFieldWithUID(self.__weeklyTasksDF, uid, 'days', taskDict['days']):
							days = taskDict['days']
							if utils.checkIfToBeDoneToday(days) or utils.checkIfWasDueInPast(days):
								days = utils.updateDaysToToday(days)
							self.__weeklyTasksDF = utils.updateFieldWithUID(self.__weeklyTasksDF, uid, 'days', days)
							changeList = self.__updateChangeList(uid, 'weeklyTasks', 'daysUpdatedWeeklyTaskList', changeList)
							
					else:
						#Task added in weekly list, this should not happen
						print('Task added to weekly list, this should not happen')
						print(line)
						
					uidsInTextFile = uidsInTextFile.append(pd.DataFrame([{'uid':uid}]))
				else:
					currentCategory = line
		
		#Since text file is completely read, check what uid's need to be deleted
		if len(uidsInTextFile) > 0:
			uidsDeleted = utils.getDeletedCells(uidsInTextFile, self.__weeklyTasksDF['uid'].to_frame())
			if len(uidsDeleted) > 0:
				for index, row in uidsDeleted.iterrows():
					if utils.checkFieldWithUID(self.__weeklyTasksDF, row['uid'], 'weeklyStatus', 'Active'):
						self.__weeklyTasksDF = utils.updateFieldWithUID(self.__weeklyTasksDF, row['uid'], 'weeklyStatus', 'Deleted')
						changeList = self.__updateChangeList(row['uid'], 'weeklyTasks', 'taskDeletedFromWeeklyTasks', changeList)
		else:
			print('Weekly tasks text file is empty')		
		
		return changeList
	

	#Function: Create weekly task dictonary from line in WeeklyTasks.txt file
	#Input: Line having task, category
	#Output: weekly task dictonary 
	def __parseWeeklyTasks(self, currentCategory, line):
		#Init empty dict
		task = {}
		tagsParsed = 0
		
		#Parse contents in brackets as tags
		tags = utils.getTagsInBrackets(line)
		
		#Minimum tag count should be 4
		if len(tags) < 4:
			print(line)
			print('Invalid Task found, there should be at least 4 tags')
			return tasks
		
		#Update dictonary with tags
		task['category'] = currentCategory
		task['status'] = tags[0]						
		task['subCategory'] = tags[1]
		task['details'] = tags[2]
		tagsParsed = 3
		
		#If subCategory is Algo then there will be at least 2 more tags
		if task['subCategory'] == 'Algo':
			if len(tags) < 5:
				print(line)
				print('Invalid Task found, algo task should have at least 5 tags')
				return task
			task['customer'] = tags[3]
			tagsParsed = 4
			
		task['days'] = utils.checkForDays(tags[tagsParsed])		
				
		return task	
		
		
		
	#Function: Reads old data frame for daily tasks stored in pickle and daily tasks text file. 
	#	Updates old data frame and returns change list. Writes the new data frame
	#Input: <None>
	#Return: change list
	def loadDailyTasks(self):
		#Load old data frame from pickle
		self.__dailyTasksDF = utils.loadPickleDF(self.__pickleDBAdd + '/' + 'dailyTasksDF.p')
		
		#Update daily tasks data frame from text file
		changeList = self.__updateDailyTasksFromTextFile(self.__textListDBAdd + '/' + 'DailyTasks.txt')
		
		#Write update data frame to pickle
		utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'dailyTasksDF.p',self.__dailyTasksDF)
		print('Loaded daily tasks.')
		
		return changeList
		
	#Function: Reads daily tasks text file line by line and update daily tasks data frame
	#Input: daily tasks text file name
	#Return: change list
	def __updateDailyTasksFromTextFile(self, filename):	
		#Init new change list
		changeList = []
		
		#If daily task DF is empty, daily list data frame has to be created first before being read.
		if len(self.__dailyTasksDF) == 0:
			self.__dayChanged = True
			changeList = self.regenerateDailyTasks()
			self.__dayChanged = False
			
		#Read contents of file line by line and remove new lines, tabs
		content = utils.readFileStripped(filename)
		if len(content) == 0:
			return changeList
			
		#Start new data frame to track uids read in text file.
		uidsInTextFile = pd.DataFrame()
		
		#Loop over all lines
		for line in content:
			if len(line) > 0:
				#Check if it is a task
				if self.__checkIfCurrentLineIsTask(line):
					
					#parse line to get daily task dict
					taskDict = self.__parseDailyTasks(line)

					
					#Depending on contents of task, it checks if task already exists or not
					uid = self.__checkIfTaskExists(taskDict, 1)
					
					if uid != -1:
						#Task exists in all task list
						
						#Check if status is not active, if it is not, make status active
						if not utils.checkFieldWithUID(self.__dailyTasksDF, uid, 'dailyStatus', 'Active'):
							self.__dailyTasksDF = utils.updateFieldWithUID(self.__dailyTasksDF, uid, 'dailyStatus', 'Active')
							changeList = self.__updateChangeList(uid, 'dailyTasks', 'taskActivatedInDailyTasks', changeList)
						
						if not utils.checkFieldWithUID(self.__dailyTasksDF, uid, 'time', taskDict['time']):
							self.__dailyTasksDF = utils.updateFieldWithUID(self.__dailyTasksDF, uid, 'time', taskDict['time'])
							changeList = self.__updateChangeList(uid, 'dailyTasks', 'timeUpdatedDailyTaskList', changeList)
						
						followupRequested = False
						completed = False
						if not utils.checkFieldWithUID(self.__dailyTasksDF, uid, 'lastCompleted', taskDict['lastCompleted']):
							completed = True
							self.__dailyTasksDF = utils.updateFieldWithUID(self.__dailyTasksDF, uid, 'lastCompleted', taskDict['lastCompleted'])
							self.__dailyTasksDF = utils.updateFieldWithUID(self.__dailyTasksDF, uid, 'duration', taskDict['duration'])
							self.__dailyTasksDF = utils.updateFieldWithUID(self.__dailyTasksDF, uid, 'dailyStatus', 'Completed')
						
						if not utils.checkFieldWithUID(self.__dailyTasksDF, uid, 'followupDate', taskDict['followupDate']):
							followupRequested = True
							self.__dailyTasksDF = utils.updateFieldWithUID(self.__dailyTasksDF, uid, 'followupDate', taskDict['followupDate'])
						
						if followupRequested and completed:
							changeList = self.__updateChangeList(uid, 'dailyTasks', 'completedAndFollowupRequestedDailyTaskList', changeList)
						
						if followupRequested and not completed:
							changeList = self.__updateChangeList(uid, 'dailyTasks', 'followupRequestedDailyTaskList', changeList)
						
						if not followupRequested and completed:
							changeList = self.__updateChangeList(uid, 'dailyTasks', 'completionUpdatedDailyTaskList', changeList)
						
						if not utils.checkFieldWithUID(self.__dailyTasksDF, uid, 'completed', taskDict['completed']):
							self.__dailyTasksDF = utils.updateFieldWithUID(self.__dailyTasksDF, uid, 'completed', taskDict['completed'])
							changeList = self.__updateChangeList(uid, 'dailyTasks', 'completedDailyTaskList', changeList)
						
						
					else:
						#Task added in daily list, this should not happen
						print('Task added to daily list, this should not happen')
						print(line)
						
									
					uidsInTextFile = uidsInTextFile.append(pd.DataFrame([{'uid':uid}]))
				

		#Since text file is completely read, check what uid's need to be deleted
		if len(uidsInTextFile) > 0:
			uidsDeleted = utils.getDeletedCells(uidsInTextFile, self.__dailyTasksDF['uid'].to_frame())
			if len(uidsInTextFile)>0:
				if len(uidsDeleted) > 0:
					for index, row in uidsDeleted.iterrows():
						if utils.checkFieldWithUID(self.__dailyTasksDF, row['uid'], 'dailyStatus', 'Active'):
							self.__dailyTasksDF = utils.updateFieldWithUID(self.__dailyTasksDF, row['uid'], 'dailyStatus', 'Deleted')
							changeList = self.__updateChangeList(row['uid'], 'dailyTasks', 'taskDeletedFromDailyTasks', changeList)
		else:
			print('Weekly tasks text file is empty')				
		
		return changeList
		
	
	#Function: Create daily task dictonary from line in DailyTasks.txt file
	#Input: Line having task
	#Output: weekly task dictonary 
	def __parseDailyTasks(self, line):
		#Init empty dict
		task = {}
		tagsParsed = 0
		
		#Parse contents in brackets as tags
		tags = utils.getTagsInBrackets(line)
		
		#Minimum tag count should be 3
		if len(tags) < 3:
			print(line)
			print('Invalid Task found, there should be at least 3 tags')
			return tasks
		
		#Update dictonary with tags
		task['time'] = utils.getTime(tags[0])
		task['subCategory'] = tags[1]
		task['details'] = tags[2]
		tagsParsed = 3
		
		#If subCategory is Algo then there will be at least 2 more tags
		if task['subCategory'] == 'Algo':
			if len(tags) < 4:
				print(line)
				print('Invalid Task found, algo task should have at least 5 tags')
				return task
			task['customer'] = tags[3]
			tagsParsed = 4
		
		#There could be tags for completed, time completed, followup time 
		task['lastCompleted'] = -1
		task['duration'] = -1
		task['followupDate'] = 'None'
		task['completed'] = False
		for currentTagIndex in range(tagsParsed,len(tags)):
			if utils.checkForKeyWordWithSeparation(tags[currentTagIndex], 'Followup'):
				task['followupDate'] = (tags[currentTagIndex][tags[currentTagIndex].index('Followup') + len('Followup'):]).strip()
				continue
			if utils.checkForKeyWordWithSeparation(tags[currentTagIndex], 'Completed'):
				task['completed'] = True
				continue
			completetionDetails = utils.getDetailsOfCompletion(tags[currentTagIndex])
			task['lastCompleted'] = completetionDetails['lastCompleted']
			task['duration'] = completetionDetails['duration']
		
		return task	
	
	
	#Function: Propogates all changes to other tasks lists
	#Input: change list
	#Return: non
	def updateTasks(self, changeList):
		#Iterate over change list
		if len(changeList) > 0:
			
			for changes in changeList:
				#Possible actions
				deleteFromAllTasks = False
				updateLastCompleted = False
				updateProgress = False
				createFollowupRequest = False
				addToWeeklyTask = False
				deleteFromWeeklyTask = False
				updateWeeklyListToNextDay = False
				addToDailyTask = False
				deleteFromDailyTask = False
				
				#Init variables
				days = -1
				time = -1
				
				#Check if source is allTask
				if changes['source'] == 'allTasks':
					#If any new task is added or any existing task is updated
					if changes['change'] == 'taskAdded' or changes['change'] == 'freqUpdated' or changes['change'] == 'datesUpdated' or changes['change'] == 'occuranceUpdated' or changes['change'] == 'lastPerformedUpdated' or changes['change'] == 'followupDateUpdated' or changes['change'] == 'followupAdded': 
						#Get dict from all tasks
						allTaskDict = utils.getDictFromRowwithUID(self.__allTasksDF,changes['uid'])
						
						#if it is repeating task then check if it is to be done this week
						if allTaskDict['status'] == 'Repeating':
							repTaskDict = utils.getDictFromRowwithUID(self.__repeatingTaskFreqDF,changes['uid'])
							
							#Check if it has to be done this week, else delete the task from weekly and daily
							if self.__checkIfToBeDoneThisWeek(repTaskDict['freq'], repTaskDict['dates'], repTaskDict['occ'], repTaskDict['lastPerformed']):
								addToWeeklyTask = True
								days = self.__getDaysWhenDone(repTaskDict['freq'], repTaskDict['dates'], repTaskDict['occ'])
								
								#Check if it has to be done today, else delete the task from daily
								if utils.checkIfToBeDoneToday(days) or utils.checkIfWasDueInPast(days):
									addToDailyTask = True
									days = utils.updateDaysToToday(days)
									time = self.__getTimeWhenDone(days)
								else:
									deleteFromDailyTask = True
							else:
								deleteFromWeeklyTask = True
								deleteFromDailyTask = True
								
						if allTaskDict['status'] == 'Ongoing':
							#Check if followup exists, if not then add it to list
							if len(self.__followupTasksDF[self.__followupTasksDF['uid'] == changes['uid']]) == 1:
								#Check if followup is required this week.
								if self.__checkIfFollowupIsThisWeek(utils.getFieldValueWithUID(self.__followupTasksDF, changes['uid'],'followupDate')):
									addToWeeklyTask = True
									days = self.__getDaysWhenToDoFollowup(utils.getFieldValueWithUID(self.__followupTasksDF, changes['uid'],'followupDate'))
									#Check if it has to be done today, else delete the task from daily
									if utils.checkIfToBeDoneToday(days) or utils.checkIfWasDueInPast(days):
										addToDailyTask = True
										days = utils.updateDaysToToday(days)
										time = self.__getTimeWhenDone(days)
									else:
										deleteFromDailyTask = True
								else:
									deleteFromWeeklyTask = True
									deleteFromDailyTask = True
							else:
								days = utils.updateDaysToToday(1)
								time = self.__getTimeWhenDone(days)
								addToWeeklyTask = True
								addToDailyTask = True
								
					#If any task is deleted
					if changes['change'] == 'taskDeletedFromAllTasks':
						deleteFromAllTasks = True
						deleteFromWeeklyTask = True
						deleteFromDailyTask = True
				
				#Check if source is weeklyTasks
				if changes['source'] == 'weeklyTasks':
					#If task is activated 
					if changes['change'] == 'taskActivatedInWeeklyTasks': 
						#Check if it is done today, if yes then add to daily list otherwise delete
						if utils.checkIfToBeDoneToday(days):
							addToDailyTask = True
							time = self.__getTimeWhenDone(days)
						else:
							deleteFromDailyTask = True
							
					#If days are updated on weekly list
					if changes['change'] == 'daysUpdatedWeeklyTaskList':
						days = utils.getFieldValueWithUID(self.__weeklyTasksDF, changes['uid'], 'days')
						
						#Check if it is done today, if yes then add to daily list otherwise delete
						if utils.checkIfToBeDoneToday(days):
							addToDailyTask = True
							time = self.__getTimeWhenDone(days)
						else:
							deleteFromDailyTask = True
					
					#If task is deleted then remove from daily list
					if changes['change'] == 'taskDeletedFromWeeklyTasks':
						deleteFromDailyTask = True

				#Check if source is dailyTasks
				if changes['source'] == 'dailyTasks':
					if changes['change'] == 'taskActivatedInDailyTasks': 
						addToWeeklyTask = True
					
					#If task is completed in daily tasks, if it is repeating task then update last completed date, 
					#if it is non repeating, check for followup if no followp then delete the task.
					if changes['change'] == 'completionUpdatedDailyTaskList': 
						#Get dict from all tasks
						allTaskDict = utils.getDictFromRowwithUID(self.__allTasksDF,changes['uid'])
						
						#if it is repeating task then update last completed date
						if allTaskDict['status'] == 'Repeating':
							updateLastCompleted = True
						#if it is non repeating, check for progress if no progress is required then delete the task
						if allTaskDict['status'] == 'Ongoing':
							if allTaskDict['progressFlag']:
								updateProgress = True
							else:
								deleteFromAllTasks = True
								deleteFromWeeklyTask = True
						
							
					#if followup is requested add new followup date in table. If entry doesnt exist, create a new entry.
					if changes['change'] == 'followupRequestedDailyTaskList': 
						createFollowupRequest = True
					
					if changes['change'] == 'completedAndFollowupRequestedDailyTaskList': 	
						createFollowupRequest = True
								
					#If task is marked completed, then delete the task from list
					if changes['change'] == 'completedDailyTaskList': 
						deleteFromWeeklyTask = True
						deleteFromAllTasks = True
					
					#If task is deleted from daily tasks, put it for next day on weekly list
					if changes['change'] == 'taskDeletedFromDailyTasks': 
						updateWeeklyListToNextDay = True				
				
				
				
				if deleteFromAllTasks:
					#delete the task
					self.__allTasksDF = self.__allTasksDF[self.__allTasksDF['uid'] != changes['uid']]
					self.__repeatingTaskFreqDF = self.__repeatingTaskFreqDF[self.__repeatingTaskFreqDF['uid'] != changes['uid']]
					self.__algoCustomerNamesDF = self.__algoCustomerNamesDF[self.__algoCustomerNamesDF['uid'] != changes['uid']]
					self.__followupTasksDF = self.__followupTasksDF[self.__followupTasksDF['uid'] != changes['uid']]
					
				if updateLastCompleted:
					#update last completed in repeating task freq df
					if self.__dayChanged:
						lastPerformed = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
					else:
						lastPerformed = datetime.datetime.today().strftime('%Y-%m-%d')
					self.__repeatingTaskFreqDF = utils.updateFieldWithUID(self.__repeatingTaskFreqDF, changes['uid'], 'lastPerformed', lastPerformed)
					repTaskDict = utils.getDictFromRowwithUID(self.__repeatingTaskFreqDF, changes['uid'])
					if self.__checkIfToBeDoneThisWeek(repTaskDict['freq'], repTaskDict['dates'], repTaskDict['occ'], repTaskDict['lastPerformed']):
						days = self.__getDaysWhenDone(repTaskDict['freq'], repTaskDict['dates'], repTaskDict['occ'])
						addToWeeklyTask = True
					else:
						deleteFromWeeklyTask = True
					
						
				if updateProgress: 
					#update progress 
					if self.__dayChanged:
						days = utils.updateDaysToToday(utils.getFieldValueWithUID(self.__weeklyTasksDF, changes['uid'], 'days'))
					else:
						days = utils.updateDaysToTomorrow(utils.getFieldValueWithUID(self.__weeklyTasksDF, changes['uid'], 'days'))
					self.__weeklyTasksDF = utils.updateFieldWithUID(self.__weeklyTasksDF, changes['uid'], 'days', days)		
					self.__updateFileWithNewProgress(changes['uid'])
				
				if createFollowupRequest:
					followupDate = utils.getFieldValueWithUID(self.__dailyTasksDF,changes['uid'],'followupDate')
					#Check if task already exist in followup list, if yes then update follow up date, else create new task and then update follow up date.
					if len(self.__followupTasksDF[self.__followupTasksDF['uid'] == changes['uid']]) == 1:
						self.__followupTasksDF = utils.updateFieldWithUID(self.__followupTasksDF, changes['uid'], 'followupDate', followupDate)
					else:
						self.__followupTasksDF = utils.appendDictAndResetIndexinDF(self.__followupTasksDF,{'uid':changes['uid'], 'followupDate': followupDate})
					#Check if followup is required this week.
					if self.__checkIfFollowupIsThisWeek(utils.getFieldValueWithUID(self.__followupTasksDF, changes['uid'],'followupDate')):
						days = self.__getDaysWhenToDoFollowup(utils.getFieldValueWithUID(self.__followupTasksDF, changes['uid'],'followupDate'))
						addToWeeklyTask = True
					else:
						deleteFromWeeklyTask = True
							
				if addToWeeklyTask:
					#Check if task already exist in weekly list, if yes then make it activate and update days else, create new weekly task.
					if len(self.__weeklyTasksDF[self.__weeklyTasksDF['uid'] == changes['uid']]) == 1:
						self.__weeklyTasksDF = utils.updateFieldWithUID(self.__weeklyTasksDF, changes['uid'], 'weeklyStatus', 'Active')
						self.__weeklyTasksDF = utils.updateFieldWithUID(self.__weeklyTasksDF, changes['uid'], 'days', days)
					else:
						self.__weeklyTasksDF = utils.appendDictAndResetIndexinDF(self.__weeklyTasksDF,{'uid':changes['uid'], 'days': days, 'weeklyStatus': 'Active'})
				
				if deleteFromWeeklyTask:
					#Check if task already exist in weekly list, if yes then deactivate it
					if len(self.__weeklyTasksDF[self.__weeklyTasksDF['uid'] == changes['uid']]) == 1:
						self.__weeklyTasksDF = utils.updateFieldWithUID(self.__weeklyTasksDF, changes['uid'], 'weeklyStatus', 'Deleted')
					
				if updateWeeklyListToNextDay:
					if self.__dayChanged:
						days = utils.updateDaysToToday(utils.getFieldValueWithUID(self.__weeklyTasksDF, changes['uid'], 'days'))
					else:
						days = utils.updateDaysToTomorrow(utils.getFieldValueWithUID(self.__weeklyTasksDF, changes['uid'], 'days'))
					self.__weeklyTasksDF = utils.updateFieldWithUID(self.__weeklyTasksDF, changes['uid'], 'days', days)		
				
				if addToDailyTask:
					#Check if task already exist in daily list, if yes then make it active and update time else, create new daily task.
					if len(self.__dailyTasksDF[self.__dailyTasksDF['uid'] == changes['uid']]) == 1:
						self.__dailyTasksDF = utils.updateFieldWithUID(self.__dailyTasksDF, changes['uid'], 'dailyStatus', 'Active')
						self.__dailyTasksDF = utils.updateFieldWithUID(self.__dailyTasksDF, changes['uid'], 'time', time)
					else:
						self.__dailyTasksDF = utils.appendDictAndResetIndexinDF(self.__dailyTasksDF,{'uid':changes['uid'], 'time':time,'dailyStatus': 'Active','lastCompleted' :-1,'duration':-1, 'completed':False, 'followupDate':'None'})
				
				if deleteFromDailyTask:
					#Check if task already exist in weekly list, if yes then deactivate it
					if len(self.__dailyTasksDF[self.__dailyTasksDF['uid'] == changes['uid']]) == 1:
						self.__dailyTasksDF = utils.updateFieldWithUID(self.__dailyTasksDF, changes['uid'], 'dailyStatus', 'Deleted')
						
			#Write updated dfs to pickle
			utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'allTasksDF.p',self.__allTasksDF)
			utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'repeatingTaskFreqDF.p',self.__repeatingTaskFreqDF)
			utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'weeklyTasksDF.p',self.__weeklyTasksDF)
			utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'dailyTasksDF.p',self.__dailyTasksDF)
			utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'followupTasksDF.p',self.__followupTasksDF)
			
			print('Updated all tasks.')
		return []
			
	
	#Function: Regenerates weekly tasks using the all tasks data frame
	#Input: <none>
	#Return: change list
	def regenerateWeeklyTasks(self):
		#Init change list
		changeList = []
	
		#Check if week changed
		if self.__weekChanged == True:
			
			#Refresh weekly task df
			self.__weeklyTasksDF = pd.DataFrame()
			
			#Fetch all the ongoing tasks and append them and assign Monday for all of them
			ongoingTasks = self.__allTasksDF[self.__allTasksDF['status'] == 'Ongoing']
			for index, row in ongoingTasks.iterrows():
				#Check if followup is required for this task else simply add the task to list
				if len(self.__followupTasksDF[self.__followupTasksDF['uid'] == row['uid']]) == 1:
					
					#Check if followup is this week, if yes then add task to list
					if self.__checkIfFollowupIsThisWeek(utils.getFieldValueWithUID(self.__followupTasksDF,row['uid'],'followupDate')):
						days = self.__getDaysWhenToDoFollowup(utils.getFieldValueWithUID(self.__followupTasksDF,row['uid'],'followupDate'))
						self.__weeklyTasksDF = utils.appendDictAndResetIndexinDF(self.__weeklyTasksDF,{'uid' : row['uid'], 'days': days, 'weeklyStatus': 'Active'})
						changeList = self.__updateChangeList(row['uid'], 'WeeklyTasks', 'taskAddedWeeklyTaskList', changeList)
				
				else:
					self.__weeklyTasksDF = utils.appendDictAndResetIndexinDF(self.__weeklyTasksDF,{'uid':row['uid'], 'days': utils.checkForDays('Monday'), 'weeklyStatus': 'Active'})
					changeList = self.__updateChangeList(row['uid'], 'WeeklyTasks', 'taskAddedWeeklyTaskList', changeList)
				
			#Fetch all the repeating tasks and check if they need to be done this week, if yes, then add them 
			for index, row in self.__repeatingTaskFreqDF.iterrows():
				if self.__checkIfToBeDoneThisWeek(row['freq'], row['dates'], row['occ'], row['lastPerformed']):
					days = self.__getDaysWhenDone(row['freq'], row['dates'], row['occ'])
					self.__weeklyTasksDF = utils.appendDictAndResetIndexinDF(self.__weeklyTasksDF,{'uid':row['uid'], 'days': days, 'weeklyStatus': 'Active'})
					changeList = self.__updateChangeList(row['uid'], 'WeeklyTasks', 'taskAddedWeeklyTaskList', changeList)
			print('Regenerated weekly tasks')
		
		
		#Check if day changed
		if self.__dayChanged == True:
			#Depending on current day, if the task is active this implies it has not be completed yet. This could be because it is either 
			#due in future or today. In that case nothing has to be done. But if it was due in past then it has to be changed to today's date
			for index, row in self.__weeklyTasksDF.iterrows():
				if row['weeklyStatus'] == 'Active':
					if utils.checkIfWasDueInPast(row['days']):
						self.__weeklyTasksDF.set_value(index,'days',utils.updateDaysToToday(row['days']))
						
		#Write to pickle updated weekly dat frame
		utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'weeklyTasksDF.p',self.__weeklyTasksDF)
					
		return changeList
	
	#Function: Gives the days of week when task has to be done this week
	#Input: freq, dates, occ
	#Return: Boolean
	def __getDaysWhenDone(self, freq, dates, occ):
		if dates == 1111111:
			return dates
		if freq == 'Weekly':
			if dates == -1:
				return 1
			else:
				return dates
		if freq == 'Monthly':
			if dates == -1:
				return 1
			else:
				daysOfMonth = utils.getDaysOfMonth(dates)
				daysOfCurrentWeek = []
				today = datetime.date.today()
				startDateOfWeek = today - datetime.timedelta(days=today.weekday())
				for i in range(0,7):
					temp = startDateOfWeek + datetime.timedelta(days=i)
					daysOfCurrentWeek.append(temp.day)
				
				day_index = 0
				dates = 0
				for dayInWeek in daysOfCurrentWeek:
					for day in daysOfMonth:
						if dayInWeek == day:
							dates += 10**day_index
					day_index += 1
				return dates
				
	
	#Function: Checks if the task has to be done this week
	#Input: freq, dates, occ, lastPerformed
	#Return: Boolean
	def __checkIfToBeDoneThisWeek(self, freq, dates, occ, lastPerformed):
		#Get number of days between last performed and end of week
		today = datetime.date.today()
		lastPerformedDate = datetime.datetime.strptime(lastPerformed, '%Y-%m-%d')
		timeDifference = abs(lastPerformedDate - datetime.datetime.now())
		numberOfDays = timeDifference.days + 7 - today.weekday() #planning for this week
		
		#If freq is weekly
		if freq == 'Weekly':
			#if everyday return true
			if dates == 1111111:
				return True
			#If weekly return true
			if occ == 1:
				return True
			#If number of days have passed are more than 7, return true
			if numberOfDays >= 7*occ:
				return True
			else:
				return False
		
		#If freq is monthly
		if freq == 'Monthly':
			#if no specific dates assigned
			if dates == -1:
				#If number of days have passed are more than 30*Occ, return true
				if numberOfDays >= 30*occ:
					return True
				else:
					return False
			else:
				#Specific days are assigned
				checkForDays = False
				if occ == 1:
					#If occurs monthly check if days when done are during this week
					checkForDays = True
				else:
					#First check If number of days have passed are more than 30*(Occ-1),
					if numberOfDays >= 30*(occ-1):
						checkForDays = True
					else:
						return False
				if checkForDays:
					#Get days of the month when task has to be done
					daysOfMonth = utils.getDaysOfMonth(dates)
					daysOfCurrentWeek = []
					startDateOfWeek = today - datetime.timedelta(days=today.weekday())
					
					#Get dates for this week
					for i in range(0,7):
						temp = startDateOfWeek + datetime.timedelta(days=i)
						daysOfCurrentWeek.append(temp.day)
					
					#Check if any date matches then return true
					for dayInWeek in daysOfCurrentWeek:
						for day in daysOfMonth:
							if dayInWeek == day:
								return True
					return False	
				
	
	
	#Function: Gives the days of week when task has to be followed up
	#Input: dateString in format '%Y-%m-%d'
	#Return: dates
	def __getDaysWhenToDoFollowup(self, dateString):
		#Check if followup date was in past
		dayOfMonth = datetime.datetime.strptime(dateString, '%Y-%m-%d')
		if (datetime.datetime.now()-dayOfMonth).days > 0:
			return utils.updateDaysToToday(1)
			
		#Get days of the month when task has to be done
		return 10**dayOfMonth.weekday()
	
	
	#Function: Check if followup is this week
	#Input: dateString in format '%Y-%m-%d'
	#Return: Boolean
	def __checkIfFollowupIsThisWeek(self, dateString):
		#Get day of the month when task has to be done
		today = datetime.date.today()
		dayOfMonth = datetime.datetime.strptime(dateString, '%Y-%m-%d')
		
		#Check if followup date was in past
		if (datetime.datetime.now()-dayOfMonth).days > 0:
			return True
		
		daysOfCurrentWeek = []
		startDateOfWeek = today - datetime.timedelta(days=today.weekday())
		
		#Get dates for this week
		for i in range(0,7):
			temp = startDateOfWeek + datetime.timedelta(days=i)
			daysOfCurrentWeek.append(temp.day)
		
		#Check if any date matches then return true
		for dayInWeek in daysOfCurrentWeek:
			if dayInWeek == dayOfMonth.day:
				return True
		return False	
		
	#Function: Regenerates daily tasks using the weekly tasks data frame
	#Input: <none>
	#Return: change list
	def regenerateDailyTasks(self):
		#Init change list
		changeList = []
		
		#Check if day changed
		if self.__dayChanged == True:
			
			#Refresh daily task df
			self.__dailyTasksDF = pd.DataFrame()
			
			#Iterate over all weekly tasks
			for index, row in self.__weeklyTasksDF.iterrows():
				#Check if task is active
				if row['weeklyStatus'] == 'Active' :
					if utils.checkIfToBeDoneToday(row['days']):
						time = self.__getTimeWhenDone(row['days'])
						self.__dailyTasksDF = utils.appendDictAndResetIndexinDF(self.__dailyTasksDF,{'uid':row['uid'], 'time':time,'dailyStatus': 'Active','lastCompleted' :-1,'duration':-1, 'completed':False, 'followupDate':'None'})
						changeList = self.__updateChangeList(row['uid'], 'dailyTasks', 'taskAddedDailyTaskList', changeList)
			print('Regenerated daily tasks.')

		#Write to pickle daily tasks dat frame
		utils.writeToPickleDF(self.__pickleDBAdd + '/' + 'dailyTasksDF.p',self.__dailyTasksDF)
			
		return changeList
			
	#Function: Write alls tasks to a text file
	#Input: <None>
	#Return: <None>
	def writeToTextAllTasks(self):
		#Open text file
		f = open(self.__textListDBAdd + '/' + 'Tasks.txt','w') 
		
		#Identify unique categories and iterate over them
		uniqueCategories = self.__allTasksDF.category.unique()
		for categoryCal in uniqueCategories:
			
			#Write category and new lines
			f.write(categoryCal + '\n\n')
			
			#iterate in order of status
			statusList = ['Ongoing','Repeating','Hold']
			for statusToBeChecked in statusList:
				
				#Get all tasks from all tasks DF which are in current category and has status as required
				statusTasksList = self.__allTasksDF[(self.__allTasksDF['category']==categoryCal) & (self.__allTasksDF['status']==statusToBeChecked)]
				
				#Identify unique sub categories and iterate over them
				uniqueSubCategories = statusTasksList.subCategory.unique()
				for subCategoryCal in uniqueSubCategories:
					
					#Get all tasks in current sub cateogory and iterate over them
					tasksList = statusTasksList[statusTasksList['subCategory'] == subCategoryCal]
					for index, row in tasksList.iterrows():
						f.write('\t* [' + row['status'] + '] [' + row['subCategory'] + '] [' + row['details'] + ']')
						
						if row['subCategory'] == 'Algo':
							f.write(' [' + utils.getFieldValueWithUID(self.__algoCustomerNamesDF,row['uid'],'customer') + ']')
						
						if row['status'] == 'Repeating':
							repTaskDict = utils.getDictFromRowwithUID(self.__repeatingTaskFreqDF,row['uid'])
							freqString = utils.getStringForFreqDateOcc(repTaskDict['freq'],repTaskDict['dates'], repTaskDict['occ'])
							f.write(' [' + freqString + ']')
							f.write(' [' + repTaskDict['lastPerformed'] + ']')
						
						if row['progressFlag'] == True:
							f.write(' [Progress]')
						
						if row['notesFlag'] == True:
							f.write(' [Notes]')
						
						#Check if followup is present, if yes then write  followup date
						if len(self.__followupTasksDF[self.__followupTasksDF['uid'] == row['uid']]) == 1:
							f.write(' [Followup ' + utils.getFieldValueWithUID(self.__followupTasksDF,row['uid'],'followupDate') + ']')
							
						f.write('\n')
			f.write('\n\n')
		f.close()
		print('All tasks written.')
	
	#Function: Get time of day when task has to be done
	#Input: day
	#Return: time
	def __getTimeWhenDone(self, days):
		return 10*60
		
	#Function: Write weekly tasks to a text file
	#Input: <None>
	#Return: <None>
	def writeToTextWeeklyTasks(self):
		#Open text file
		f = open(self.__textListDBAdd + '/' + 'WeeklyTasks.txt','w') 
		
		#Identify unique categories and iterate over them
		uniqueCategories = self.__allTasksDF.category.unique()
		for categoryCal in uniqueCategories:
			#Get all tasks from all tasks DF which are in current category and are present in weeekly list
			categoryWeeklyTasks = self.__allTasksDF[(self.__allTasksDF['category'] == categoryCal) & (self.__allTasksDF['uid'].isin(self.__weeklyTasksDF['uid'].tolist()))]
			if len(categoryWeeklyTasks) == 0:
				continue
			
			#Get days for the tasks are in current category and are present in weeekly list and are active
			categoryWeeklyTasksDays = self.__weeklyTasksDF[(self.__weeklyTasksDF['weeklyStatus'] == 'Active') & (self.__weeklyTasksDF['uid'].isin(categoryWeeklyTasks['uid'].tolist()))]
			if len(categoryWeeklyTasksDays) == 0:
				continue
			
			#Write category and new lines
			f.write(categoryCal + '\n\n')
			
			#Get sorted UIDs depending on the day of week when the task has to be done
			sortedUidArray = self.__sortListForDays(categoryWeeklyTasksDays)
			
			#iterate over UIDs in sorted array
			for uid in sortedUidArray:
				#Write details about the task 
				taskDict = utils.getDictFromRowwithUID(self.__allTasksDF,uid)
				f.write('\t* [' + taskDict['status'] + '] [' + taskDict['subCategory'] + '] [' + taskDict['details'] + ']')
				
				#Write task has subcatogory as algo, write customer name
				if taskDict['subCategory'] == 'Algo':
					f.write(' [' + utils.getFieldValueWithUID(self.__algoCustomerNamesDF,uid,'customer') + ']')
					
				#Write days when teh task has to be done
				days = utils.getFieldValueWithUID(self.__weeklyTasksDF,uid,'days')
				if days == 1111111:
					f.write(' [Everyday]')
				else:
					days = utils.getDaysOfWeek(days)
					f.write(' [')
					temp_var = 0
					for day in days:
						f.write(day)
						temp_var += 1
						if temp_var < len(days):
							f.write(',')			
					f.write(']')		
				
				#Write a new line
				f.write('\n')
				
			#Write 2 new lines if cateogry is over	
			f.write('\n\n')
		
		#Close the file
		f.close()
		print('Weekly tasks written.')
	
	
	#Function: Sort uids depending on the day of week when task is to be done
	#Input: weeklyTasks data frame for the tasks to be sorted
	#Return: Sorted array of uids
	def __sortListForDays(self, weeklyTasks):
		priorityArray = np.zeros(len(weeklyTasks))
		uidArray = np.zeros(len(weeklyTasks))
		arrayIndex = 0
		for index, row in weeklyTasks.iterrows():
			priorityArray[arrayIndex] = utils.getDayPriority(row['days'])
			uidArray[arrayIndex] = (row['uid'])
			arrayIndex += 1
			#numpy arra of uid and priority and then sort and create new array
		sortedUidArray = uidArray[np.argsort(priorityArray)]
		return sortedUidArray
		
	
	#Function: Write daily tasks to a text file
	#Input: <None>
	#Return: <None>
	def writeToTextDailyTasks(self):
		#Open text file
		f = open(self.__textListDBAdd + '/' + 'DailyTasks.txt','w') 
		
		#Get all tasks from all tasks DF which are in current category and are present in daily list
		categoryDailyTasks = self.__allTasksDF[(self.__allTasksDF['uid'].isin(self.__dailyTasksDF['uid'].tolist()))]
		
		#Get time for the tasks are in current category and are present in daily list and are active
		categoryDailyTasksTime = self.__dailyTasksDF[(self.__dailyTasksDF['dailyStatus'] == 'Active') & (self.__dailyTasksDF['uid'].isin(categoryDailyTasks['uid'].tolist()))]
		
		#Get sorted UIDs depending on the time of day when the task has to be done
		sortedUidArray = self.__sortListForTime(categoryDailyTasksTime)
		
		#iterate over UIDs in sorted array
		for uid in sortedUidArray:
			#Get details about the task 
			taskDict = utils.getDictFromRowwithUID(self.__allTasksDF,uid)
			
			#Get time of day when task has to be done			
			time = utils.getFieldValueWithUID(self.__dailyTasksDF,uid,'time') 
			
			#Write task
			f.write('* [' + utils.getTimeString(time) + '] [' + taskDict['subCategory'] + '] [' + taskDict['details'] + ']')
			
			#Write task has subcatogory as algo, write customer name
			if taskDict['subCategory'] == 'Algo':
				f.write(' [' + utils.getFieldValueWithUID(self.__algoCustomerNamesDF,uid,'customer') + ']')
						
			#Write a new line
			f.write('\n')
		
		#Close the file
		f.close()
		print('Daily tasks written.')
		return []
		
	
	#Function: Sort uids depending on the time of day when task is to be done
	#Input: dailyTask data frame for the tasks to be sorted
	#Return: Sorted array of uids
	def __sortListForTime(self, dailyTasks):
		priorityArray = np.zeros(len(dailyTasks))
		uidArray = np.zeros(len(dailyTasks))
		arrayIndex = 0
		for index, row in dailyTasks.iterrows():
			priorityArray[arrayIndex] = row['time']
			uidArray[arrayIndex] = row['uid']
			arrayIndex += 1
			#numpy arra of uid and priority and then sort and create new array
		sortedUidArray = uidArray[np.argsort(priorityArray)]
		return sortedUidArray
		
	
	#Function: Check for current time and last updated time and decide if day has changed or week has changed
	#Input: <none>
	#Return: <none>
	def updateToCurrentTime(self):
		#Get current day and week of day
		currentDay = datetime.datetime.today()
		currentWeekDay = datetime.datetime.today().weekday()
		
		#Check if date file exist, else make both day and week day changed as true
		my_file = Path(self.__pickleDBAdd + '/' + 'date.p')
		if my_file.is_file():
			with open(self.__pickleDBAdd + '/' + 'date.p', 'rb') as handle:
				dateDict = pickle.load(handle)
			
			previousDay = dateDict['day']
			previousWeekDay = dateDict['weekDay']
			
			#If dates changed
			if currentDay.date() != previousDay.date():
				self.__dayChanged = True
			else:
				self.__dayChanged = False
				
			#if week changed
			if currentWeekDay < previousWeekDay or (currentDay - previousDay).days >= 7:
				self.__weekChanged = True
			else:
				self.__weekChanged = False
		else:
			dateDict = {}
			self.__dayChanged = True
			self.__weekChanged = True
			
		#Update date dict
		dateDict['weekDay'] = currentWeekDay
		dateDict['day'] = currentDay
		
		#Save date dict
		with open(self.__pickleDBAdd + '/' + 'date.p', 'wb') as handle:
			pickle.dump(dateDict, handle, protocol=pickle.HIGHEST_PROTOCOL)
		print('Current time updated.')
		
	
	#Function: Dumps all tables into html
	#Input: <none>
	#Return: <none>
	def printAllListsToHTML(self):
		print('Priting all data frames to html...')
		if len(self.__allTasksDF) > 0:
			self.__allTasksDF.to_html('AllTask.html')
		if len(self.__algoCustomerNamesDF) > 0:
			self.__algoCustomerNamesDF.to_html('CustomerNames.html')
		if len(self.__repeatingTaskFreqDF) > 0:
			self.__repeatingTaskFreqDF.to_html('RepeatingTasks.html')
		if len(self.__weeklyTasksDF) > 0:
			self.__weeklyTasksDF.to_html('WeeklyTasks.html')
		if len(self.__dailyTasksDF) > 0:
			self.__dailyTasksDF.to_html('DailyTasks.html')
		if len(self.__followupTasksDF) > 0:
			self.__followupTasksDF.to_html('FollowupTasksDF.html')
			
	
	#Function: Logs all updates
	#Input: Change list
	#Return: <none>
	def logAllUpdates(self, changeList):
		if len(changeList) > 0:
			#Open file to append it
			f = open(self.__pickleDBAdd + '/' + 'changeLog' ,"a+")
			
			#Write current date and time
			f.write('Time:'+ datetime.datetime.now().isoformat() + '\n')
			for changes in changeList:
				
				#Write changes
				stringToWrite = ", ".join(["=".join([key, str(val)]) for key, val in changes.items()])
				f.write('Changes:' + stringToWrite + '\n')
				
				#Write details of task
				matchedRowAllTasks = self.__allTasksDF[self.__allTasksDF['uid'] == changes['uid']]
				for index, row in matchedRowAllTasks.iterrows():
					stringToWrite = ", ".join(["=".join([key, str(val)]) for key, val in row.items()])
				f.write('AllTasks:'+ stringToWrite + '\n')
				
				#Write customer name if task is algo
				matchedRowAlgoCustomerName = self.__algoCustomerNamesDF[self.__algoCustomerNamesDF['uid'] == changes['uid']]
				if len(matchedRowAlgoCustomerName) > 0: 
					for index, row in matchedRowAlgoCustomerName.iterrows():
						stringToWrite = ", ".join(["=".join([key, str(val)]) for key, val in row.items()])
					f.write('AlgoCustomerNames:'+ stringToWrite + '\n')

				#Write repeating task freq if task is repeating
				matchedRowRepTaskFreq = self.__repeatingTaskFreqDF[self.__repeatingTaskFreqDF['uid'] == changes['uid']]
				if len(matchedRowRepTaskFreq) > 0: 
					for index, row in matchedRowRepTaskFreq.iterrows():
						stringToWrite = ", ".join(["=".join([key, str(val)]) for key, val in row.items()])
					f.write('RepTaskFreq:'+ stringToWrite + '\n')
				
				#Write followup details if task has followup
				matchedRowFollowupTasks = self.__followupTasksDF[self.__followupTasksDF['uid'] == changes['uid']]
				if len(matchedRowFollowupTasks) > 0: 
					for index, row in matchedRowFollowupTasks.iterrows():
						stringToWrite = ", ".join(["=".join([key, str(val)]) for key, val in row.items()])
					f.write('FollowupTask:'+ stringToWrite + '\n')	
				
				#Write details on weekly list 
				matchedRowWeeklyTasks = self.__weeklyTasksDF[self.__weeklyTasksDF['uid'] == changes['uid']]
				if len(matchedRowWeeklyTasks) > 0: 
					for index, row in matchedRowWeeklyTasks.iterrows():
						stringToWrite = ", ".join(["=".join([key, str(val)]) for key, val in row.items()])
					f.write('WeeklyTasks:'+ stringToWrite + '\n')
					
				#Write details on daily list 
				matchedRowDailyTasks = self.__dailyTasksDF[self.__dailyTasksDF['uid'] == changes['uid']]
				if len(matchedRowDailyTasks) > 0:
					for index, row in matchedRowDailyTasks.iterrows():
						stringToWrite = ", ".join(["=".join([key, str(val)]) for key, val in row.items()])
					f.write('DailyTasks:'+ stringToWrite + '\n')
			#Close the file		
			f.close()
			
	
	#Function: Creates infrastructure for tasks if task have notes or progress flags
	#Input: <none>
	#Return: <none>
	def createProgressAndNotesInfra(self):
		#Get all the tasks that have progress flag and are not on hold
		mergedDF = self.__allTasksDF[(self.__allTasksDF['progressFlag'] == True) & (self.__allTasksDF['status'] != 'Hold')]
		for index, rows in mergedDF.iterrows():
			filename = rows['subCategory'] + '_' + rows['details'] + ".txt"
			filename = filename.replace(" ", "_")
			filename = filename.replace("/", "_")
			filename = filename.replace(",", "")
			my_file = Path(self.__progressDBAdd + '/' + filename)
			if not my_file.is_file():
				f = open(self.__progressDBAdd + '/' + filename,"w+")
				f.write('Deadline\n--------\n\n\n')
				f.write('Current Tasks\n-------------\n\n\n')
				f.write('Current Issues\n--------------\n\n\n')
				f.write('Progress\n--------\n\n\n')
				f.close()
		
		#Get all the tasks that have notes flag and are not on hold
		mergedDF = self.__allTasksDF[(self.__allTasksDF['notesFlag'] == True) & (self.__allTasksDF['status'] != 'Hold')]
		for index, rows in mergedDF.iterrows():
			filename = rows['subCategory'] + '_' + rows['details']
			filename = filename.replace(" ", "_")
			filename = filename.replace("/", "_")
			filename = filename.replace(",", "")
			filename = self.__notesDBAdd + '/' + filename
			if not os.path.exists(filename):
				os.makedirs(filename)
				
			
	#Function: Updates progress page if there is any progress on task
	#Input: uid of task that has progress
	#Return: <none>
	def __updateFileWithNewProgress(self, uid):
		#Get file name for progress page
		taskDict = utils.getDictFromRowwithUID(self.__allTasksDF, uid)
		filename = taskDict['subCategory'] + '_' + taskDict['details'] + ".txt"
		filename = filename.replace(" ", "_")
		filename = filename.replace("/", "_")
		filename = filename.replace(",", "")
		
		#Get contents of the file
		f = open(self.__progressDBAdd + '/' + filename, "r")
		contents = f.readlines()
		f.close()
		
		#Get date for which progress has to be updated
		if self.__dayChanged:
			date = (datetime.datetime.today() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
		else:
			date = datetime.datetime.today().strftime('%Y-%m-%d')
			
		#Check if page already have progress for date
		pageHasDatesProgress = False
		for line in contents:
			if utils.checkForKeyWord(line, date):
				pageHasDatesProgress = True
				break
			
		#If page doesnt have progress then add progress
		if not pageHasDatesProgress:
			f = open(self.__progressDBAdd + '/' + filename, "w")
			progressLocationFound = False
			for line in contents:
				f.write(line)
				if progressLocationFound == True:
					f.write('[' + date + ']\n-\n-\n\n')
					progressLocationFound = False
				if utils.checkForKeyWord(line, 'Progress'):
					progressLocationFound = True	
			f.close()